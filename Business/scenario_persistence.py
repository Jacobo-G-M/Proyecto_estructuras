from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Any

from Models.event import Event
from Models.node import Node
from Models.report import Report
from Models.station import Station
from Models.zone import Zone
from Business.historic import Historic
from Business.geographical_map import Geographical_map
from Business.Structures.avl import AVL
from Business.Structures.bst import BST
from Business.Structures.report_queue import Report_Queue
from Business.Rules.asociation import Association
from Business.Rules.metrics import Metrics


class ScenarioPersistence:
    """
    1. Structural JSON export (export_to_dict, export_to_json).
    2. Atomic topology load with deep validation (load_by_topology, validate_topology_data).
    3. Sequential insertion comparison between balanced AVL and regular BST (load_by_insertions).
    """

    # -------------------------------------------------------------------------
    # 1. STRUCTURAL EXPORT
    # -------------------------------------------------------------------------

    @staticmethod
    def export_to_dict(observatory) -> dict[str, Any]:
        """
        Serializes the complete operational state of the Observatory into a structured dict.
        Captures tree topology, events, historic catalogs, queue, stations, associations,
        simulation clock, geographical zones, parameters, and accumulated metrics.
        """
        # Serialize active tree topology and nodes
        tree_data = ScenarioPersistence._serialize_tree(observatory.tree)

        # Serialize zones
        zones_data = []
        if observatory.geographical_map is not None:
            for zone in observatory.geographical_map.zones:
                zones_data.append({
                    "id": zone.id,
                    "name": zone.name,
                    "is_populated": zone.is_populated,
                    "ubication_x": list(zone.ubication_x),
                    "ubication_y": list(zone.ubication_y),
                })

        # Serialize stations
        stations_data = []
        for station in observatory.stations:
            stations_data.append({
                "id": station.id,
                "name": station.name,
                "coords": list(station.coords),
            })

        # Serialize historic catalogs (archived and deleted)
        historic_data = {"archived": [], "deleted": []}
        if observatory.historic is not None:
            for ev in observatory.historic.archived.values():
                historic_data["archived"].append(ScenarioPersistence._serialize_event(ev))
            for ev in observatory.historic.deleted.values():
                historic_data["deleted"].append(ScenarioPersistence._serialize_event(ev))

        # Serialize report queue in original FIFO order
        queue_data = []
        if observatory.report_queue is not None:
            for report in observatory.report_queue.view_all():
                station_ids = [
                    s.id for s in report.origin_station if hasattr(s, "id")
                ]
                queue_data.append({
                    "id": report.id,
                    "magnitude": report.magnitude,
                    "depth": report.depth,
                    "epicenter": list(report.epicenter),
                    "date_time": report.date_time.isoformat(),
                    "review": report.review,
                    "origin_stations": station_ids,
                })

        # Serialize associations
        associations_data = []
        for assoc in observatory.associations:
            ref_id = assoc.chosen_reference.id if assoc.chosen_reference is not None else None
            child_ids = [
                child.id for child in assoc.referenced_by if child is not None
            ]
            associations_data.append({
                "id": assoc.id,
                "chosen_reference_id": ref_id,
                "referenced_by_ids": child_ids,
            })

        # Serialize metrics
        metrics_data = {}
        if observatory.metrics is not None:
            metrics_data = {
                "corrections_accepted": observatory.metrics.corrections_accepted,
                "discarded_reports": observatory.metrics.discarded_reports,
                "conflicts": observatory.metrics.conflicts,
                "active_events": observatory.metrics.active_events,
                "removed_events": observatory.metrics.removed_events,
                "archived_events": observatory.metrics.archived_events,
                "cases": observatory.metrics.cases,
                "turns": observatory.metrics.turns,
            }

        return {
            "version": "1.0",
            "simulation_clock": observatory.clock_simulation.isoformat(),
            "stress_mode": bool(observatory.stress_mode),
            "parameters": {
                "limit_L": observatory.limit,
                "max_time_W": observatory.max_time,
                "distance_epicenter_R": observatory.distance_epicenter,
                "max_tree_age_T": observatory.max_tree_age,
            },
            "zones": zones_data,
            "stations": stations_data,
            "tree": tree_data,
            "historic": historic_data,
            "report_queue": queue_data,
            "associations": associations_data,
            "metrics": metrics_data,
        }

    @staticmethod
    def export_to_json(observatory, filepath: str, indent: int = 2) -> None:
        """
        Exports the current operational scenario to a JSON file at filepath.
        """
        data = ScenarioPersistence.export_to_dict(observatory)
        dirname = os.path.dirname(filepath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    # -------------------------------------------------------------------------
    # 2. TOPOLOGY VALIDATION & LOAD
    # -------------------------------------------------------------------------

    @staticmethod
    def validate_topology_data(
        data: dict[str, Any],
        geographical_map: Geographical_map | None = None,
        stress_mode_override: bool | None = None,
    ) -> list[str]:
        """
        Validates the JSON scenario data according to all criteria:
        1. Required fields and data formatting.
        2. ID uniqueness (active, archived, and deleted events must be disjoint).
        3. Pointer integrity and cycle detection (valid tree graph with single parent per child).
        4. Global BST ordering: K(left) < K(node) < K(right).
        5. Stored vs calculated heights and balance factors.
        6. Stored vs calculated event priorities.
        7. Stress mode constraints: unbalanced trees (|BF| > 1) require stress_mode.

        Returns a list of human-readable error descriptions. Empty list means data is 100% valid.
        """
        errors: list[str] = []

        if not isinstance(data, dict):
            return ["Invalid scenario format: Root must be a JSON object."]

        # 1. Parse zones for priority evaluation
        map_to_use = geographical_map
        if "zones" in data and isinstance(data["zones"], list):
            try:
                parsed_zones = []
                for z in data["zones"]:
                    parsed_zones.append(Zone(
                        id=z["id"],
                        name=z.get("name", ""),
                        is_populated=bool(z.get("is_populated", False)),
                        ubication_x=tuple(z["ubication_x"]),
                        ubication_y=tuple(z["ubication_y"]),
                    ))
                map_to_use = Geographical_map(zones=parsed_zones)
            except Exception as e:
                errors.append(f"Failed to parse zones for priority evaluation: {e}")

        # 2. Verify tree section presence
        tree_section = data.get("tree")
        if not isinstance(tree_section, dict):
            errors.append("Missing or invalid 'tree' object in scenario.")
            return errors

        root_id = tree_section.get("root_id")
        nodes_list = tree_section.get("nodes", [])
        if not isinstance(nodes_list, list):
            errors.append("'nodes' in tree section must be a list.")
            return errors

        # 3. ID Uniqueness across catalogs
        active_ids = set()
        for nd in nodes_list:
            nid = nd.get("id")
            if nid in active_ids:
                errors.append(f"Duplicate active node ID {nid} found in tree nodes.")
            active_ids.add(nid)

        archived_ids = set()
        historic_section = data.get("historic", {})
        if isinstance(historic_section, dict):
            for ev in historic_section.get("archived", []):
                eid = ev.get("id")
                if eid in archived_ids:
                    errors.append(f"Duplicate archived event ID {eid} found in historic.")
                archived_ids.add(eid)

        deleted_ids = set()
        if isinstance(historic_section, dict):
            for ev in historic_section.get("deleted", []):
                eid = ev.get("id")
                if eid in deleted_ids:
                    errors.append(f"Duplicate deleted event ID {eid} found in historic.")
                deleted_ids.add(eid)

        # Check disjointness among active, archived, and deleted
        active_archived_overlap = active_ids & archived_ids
        if active_archived_overlap:
            errors.append(f"ID overlap between active and archived catalogs: {sorted(active_archived_overlap)}.")

        active_deleted_overlap = active_ids & deleted_ids
        if active_deleted_overlap:
            errors.append(f"ID overlap between active and deleted catalogs: {sorted(active_deleted_overlap)}.")

        archived_deleted_overlap = archived_ids & deleted_ids
        if archived_deleted_overlap:
            errors.append(f"ID overlap between archived and deleted catalogs: {sorted(archived_deleted_overlap)}.")

        # 4. Topology and Graph Integrity
        nodes_dict = {nd["id"]: nd for nd in nodes_list if "id" in nd}

        if root_id is None:
            if len(nodes_list) > 0:
                errors.append("Tree root_id is null but nodes list is not empty.")
            return errors

        if root_id not in nodes_dict:
            errors.append(f"Tree root_id {root_id} does not exist in nodes list.")
            return errors

        # Verify child pointers and parent counts (in-degree)
        in_degrees: dict[int, int] = {nid: 0 for nid in nodes_dict}
        for nid, nd in nodes_dict.items():
            left_id = nd.get("left_id")
            right_id = nd.get("right_id")

            if left_id is not None:
                if left_id not in nodes_dict:
                    errors.append(f"Node {nid} has invalid left_id reference {left_id}.")
                elif left_id == nid:
                    errors.append(f"Node {nid} has a self-referencing left child loop.")
                else:
                    in_degrees[left_id] += 1

            if right_id is not None:
                if right_id not in nodes_dict:
                    errors.append(f"Node {nid} has invalid right_id reference {right_id}.")
                elif right_id == nid:
                    errors.append(f"Node {nid} has a self-referencing right child loop.")
                else:
                    in_degrees[right_id] += 1

            if left_id is not None and right_id is not None and left_id == right_id:
                errors.append(f"Node {nid} points to the same node {left_id} for both left and right children.")

        # Root must have in-degree 0; all other reachable nodes must have in-degree 1
        if in_degrees.get(root_id, 0) != 0:
            errors.append(f"Root node {root_id} cannot have a parent (in-degree is {in_degrees[root_id]}).")

        for nid, deg in in_degrees.items():
            if nid != root_id and deg != 1:
                errors.append(f"Node {nid} must have exactly one parent, but has {deg}.")

        # Cycle detection and reachability from root
        visited: set[int] = set()
        has_cycle = False

        def _traverse(cur_id: int):
            nonlocal has_cycle
            if cur_id in visited:
                has_cycle = True
                return
            visited.add(cur_id)
            cur_nd = nodes_dict[cur_id]
            l_id = cur_nd.get("left_id")
            r_id = cur_nd.get("right_id")
            if l_id is not None and l_id in nodes_dict:
                _traverse(l_id)
            if r_id is not None and r_id in nodes_dict:
                _traverse(r_id)

        _traverse(root_id)

        if has_cycle:
            errors.append("Cycle detected in tree nodes graph.")

        if len(visited) != len(nodes_dict):
            unreachable = set(nodes_dict.keys()) - visited
            errors.append(f"Unreachable nodes disconnected from root: {sorted(unreachable)}.")

        # 5. Global BST Order Verification
        # In-order traversal must produce strictly ascending keys K = (P, M, I)
        inorder_keys: list[tuple[tuple[int, float, int], int]] = []

        def _inorder(cur_id: int):
            cur_nd = nodes_dict[cur_id]
            l_id = cur_nd.get("left_id")
            r_id = cur_nd.get("right_id")
            if l_id is not None and l_id in nodes_dict:
                _inorder(l_id)
            ev = cur_nd.get("event", {})
            k = (ev.get("priority", 0), float(ev.get("magnitude", 0.0)), int(ev.get("id", 0)))
            inorder_keys.append((k, cur_id))
            if r_id is not None and r_id in nodes_dict:
                _inorder(r_id)

        if not has_cycle and len(visited) == len(nodes_dict):
            _inorder(root_id)
            for i in range(len(inorder_keys) - 1):
                k1, id1 = inorder_keys[i]
                k2, id2 = inorder_keys[i + 1]
                if k1 >= k2:
                    errors.append(
                        f"Global BST order violation: Node {id1} key {k1} >= Node {id2} key {k2} in in-order sequence."
                    )

        # 6. Verify Heights, Balance Factors, and Event Priorities
        max_abs_bf = 0

        def _verify_metrics(cur_id: int) -> int:
            nonlocal max_abs_bf
            cur_nd = nodes_dict[cur_id]
            l_id = cur_nd.get("left_id")
            r_id = cur_nd.get("right_id")

            left_h = _verify_metrics(l_id) if (l_id is not None and l_id in nodes_dict) else -1
            right_h = _verify_metrics(r_id) if (r_id is not None and r_id in nodes_dict) else -1

            calc_h = max(left_h, right_h) + 1
            calc_bf = left_h - right_h
            if abs(calc_bf) > max_abs_bf:
                max_abs_bf = abs(calc_bf)

            stored_h = cur_nd.get("height")
            if stored_h is not None and stored_h != calc_h:
                errors.append(f"Node {cur_id}: stored height {stored_h} does not match calculated height {calc_h}.")

            stored_bf = cur_nd.get("balance_factor")
            if stored_bf is not None and stored_bf != calc_bf:
                errors.append(f"Node {cur_id}: stored balance factor {stored_bf} does not match calculated {calc_bf}.")

            # Verify priority calculation
            ev_data = cur_nd.get("event", {})
            mag = float(ev_data.get("magnitude", 0.0))
            depth = float(ev_data.get("depth", 0.0))
            epicenter = tuple(ev_data.get("epicenter", (0.0, 0.0)))
            stored_p = ev_data.get("priority")

            calc_p = ScenarioPersistence._compute_priority(mag, depth, epicenter, map_to_use)
            if stored_p is not None and stored_p != calc_p:
                errors.append(
                    f"Event {cur_id}: stored priority {stored_p} does not match calculated priority {calc_p}."
                )

            return calc_h

        if not has_cycle and len(visited) == len(nodes_dict):
            _verify_metrics(root_id)

        # 7. Stress Mode rule
        # An unbalanced tree (|BF| > 1) can ONLY be loaded with stress_mode = True
        file_stress = bool(data.get("stress_mode", False))
        effective_stress = file_stress if stress_mode_override is None else stress_mode_override
        if max_abs_bf > 1 and not effective_stress:
            errors.append(
                f"Unbalanced topology (maximum |balance factor| is {max_abs_bf} > 1). "
                "Can only be loaded when stress_mode is enabled."
            )

        return errors

    @staticmethod
    def load_by_topology(
        observatory,
        filepath: str,
        stress_mode_override: bool | None = None
    ) -> tuple[bool, list[str]]:
        """
        Loads and reconstructs an operational scenario from a JSON file using direct topology reconstruction.
        Validates all invariants atomically:
        - If any error is detected, the current scenario remains 100% UNCHANGED, and (False, errors) is returned.
        - If valid, updates the entire observatory state atomically and returns (True, []).
        """
        if not os.path.exists(filepath):
            return False, [f"File not found: {filepath}"]

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return False, [f"Failed to parse JSON file: {e}"]

        errors = ScenarioPersistence.validate_topology_data(
            data,
            geographical_map=observatory.geographical_map,
            stress_mode_override=stress_mode_override,
        )

        if errors:
            return False, errors

        # ---------------------------------------------------------------------
        # ATOMIC RECONSTRUCTION: Apply state to observatory
        # ---------------------------------------------------------------------
        # Parameters and execution flags
        params = data.get("parameters", {})
        if "limit_L" in params:
            observatory.limit = int(params["limit_L"])
        if "max_time_W" in params:
            observatory.max_time = float(params["max_time_W"])
        if "distance_epicenter_R" in params:
            observatory.distance_epicenter = float(params["distance_epicenter_R"])
        if "max_tree_age_T" in params:
            observatory.max_tree_age = int(params["max_tree_age_T"])

        file_stress = bool(data.get("stress_mode", False))
        observatory.stress_mode = file_stress if stress_mode_override is None else stress_mode_override

        if "simulation_clock" in data:
            observatory.clock_simulation = datetime.fromisoformat(data["simulation_clock"])

        # Reconstruct Zones
        if "zones" in data and isinstance(data["zones"], list):
            reconstructed_zones = []
            for z in data["zones"]:
                reconstructed_zones.append(Zone(
                    id=z["id"],
                    name=z.get("name", ""),
                    is_populated=bool(z.get("is_populated", False)),
                    ubication_x=tuple(z["ubication_x"]),
                    ubication_y=tuple(z["ubication_y"]),
                ))
            observatory.geographical_map = Geographical_map(zones=reconstructed_zones)

        # Reconstruct Stations
        stations_dict: dict[int, Station] = {}
        if "stations" in data and isinstance(data["stations"], list):
            for s in data["stations"]:
                st = Station(id=s["id"], name=s["name"], coords=tuple(s["coords"]))
                stations_dict[s["id"]] = st
            observatory.stations = list(stations_dict.values())

        # Reconstruct Tree Topology without reinsertion
        tree_section = data.get("tree", {})
        nodes_list = tree_section.get("nodes", [])
        root_id = tree_section.get("root_id")

        new_tree = AVL(
            id=1,
            stress_mode=observatory.stress_mode,
            on_rotation=observatory._handle_tree_rotation,
        )

        nodes_map: dict[int, Node] = {}
        events_dict: dict[int, Event] = {}

        for nd in nodes_list:
            ev_data = nd["event"]
            ev = Event(
                id=ev_data["id"],
                priority=int(ev_data["priority"]),
                magnitude=float(ev_data["magnitude"]),
                depth=float(ev_data["depth"]),
                epicenter=tuple(ev_data["epicenter"]),
                date_time=datetime.fromisoformat(ev_data["date_time"]),
                review=int(ev_data.get("review", 1)),
                attention_state=ev_data.get("attention_state", "Pending"),
                status=ev_data.get("status", "Active"),
            )
            # Link stations
            for sid in ev_data.get("origin_stations", []):
                if sid in stations_dict:
                    ev.add_origin_station(stations_dict[sid])

            node = Node(id=nd["id"], event=ev)
            nodes_map[nd["id"]] = node
            events_dict[ev.id] = ev

        # Connect explicit left/right and father pointers
        for nd in nodes_list:
            cur_node = nodes_map[nd["id"]]
            left_id = nd.get("left_id")
            right_id = nd.get("right_id")

            if left_id is not None and left_id in nodes_map:
                left_node = nodes_map[left_id]
                cur_node.left_son = left_node
                left_node.father = cur_node

            if right_id is not None and right_id in nodes_map:
                right_node = nodes_map[right_id]
                cur_node.right_son = right_node
                right_node.father = cur_node

        if root_id is not None and root_id in nodes_map:
            new_tree.root = nodes_map[root_id]
            new_tree.root.father = None
        else:
            new_tree.root = None

        # Update node heights bottom-up (post-order) so parents compute accurate heights
        def _post_order_heights(node: Node | None) -> None:
            if node is None:
                return
            _post_order_heights(node.left_son)
            _post_order_heights(node.right_son)
            node.update_height()

        if new_tree.root is not None:
            _post_order_heights(new_tree.root)

        observatory.tree = new_tree
        observatory.events_dict = events_dict

        # Reconstruct Historic Catalogs
        new_historic = Historic()
        historic_section = data.get("historic", {})
        if isinstance(historic_section, dict):
            for ev_data in historic_section.get("archived", []):
                ev = Event(
                    id=ev_data["id"],
                    priority=int(ev_data["priority"]),
                    magnitude=float(ev_data["magnitude"]),
                    depth=float(ev_data["depth"]),
                    epicenter=tuple(ev_data["epicenter"]),
                    date_time=datetime.fromisoformat(ev_data["date_time"]),
                    review=int(ev_data.get("review", 1)),
                    attention_state=ev_data.get("attention_state", "Pending"),
                    status="Archived",
                )
                new_historic.archive_event(ev)

            for ev_data in historic_section.get("deleted", []):
                ev = Event(
                    id=ev_data["id"],
                    priority=int(ev_data["priority"]),
                    magnitude=float(ev_data["magnitude"]),
                    depth=float(ev_data["depth"]),
                    epicenter=tuple(ev_data["epicenter"]),
                    date_time=datetime.fromisoformat(ev_data["date_time"]),
                    review=int(ev_data.get("review", 1)),
                    attention_state=ev_data.get("attention_state", "Pending"),
                    status="Deleted",
                )
                new_historic.delete_event(ev)

        observatory.historic = new_historic

        # Reconstruct Report Queue
        new_queue = Report_Queue()
        for r_data in data.get("report_queue", []):
            st_list = [
                stations_dict[sid]
                for sid in r_data.get("origin_stations", [])
                if sid in stations_dict
            ]
            report = Report(
                id=r_data["id"],
                magnitude=float(r_data["magnitude"]),
                depth=float(r_data["depth"]),
                epicenter=tuple(r_data["epicenter"]),
                date_time=datetime.fromisoformat(r_data["date_time"]),
                review=int(r_data.get("review", 1)),
                origin_station=st_list,
            )
            new_queue.enqueue(report)

        observatory.report_queue = new_queue

        # Reconstruct Associations
        all_catalog = dict(events_dict)
        all_catalog.update(new_historic.archived)
        all_catalog.update(new_historic.deleted)

        new_associations = []
        for assoc_data in data.get("associations", []):
            ref_id = assoc_data.get("chosen_reference_id")
            if ref_id in all_catalog:
                assoc = Association(
                    assoc_id=assoc_data["id"],
                    chosen_reference=all_catalog[ref_id],
                )
                for child_id in assoc_data.get("referenced_by_ids", []):
                    if child_id in all_catalog:
                        assoc.add_replica(all_catalog[child_id])
                new_associations.append(assoc)

        observatory.associations = new_associations

        # Reconstruct Metrics
        new_metrics = Metrics()
        metrics_data = data.get("metrics", {})
        if metrics_data:
            new_metrics.corrections_accepted = metrics_data.get("corrections_accepted", 0)
            new_metrics.discarded_reports = metrics_data.get("discarded_reports", 0)
            new_metrics.conflicts = metrics_data.get("conflicts", 0)
            new_metrics.active_events = metrics_data.get("active_events", len(events_dict))
            new_metrics.removed_events = metrics_data.get("removed_events", len(new_historic.deleted))
            new_metrics.archived_events = metrics_data.get("archived_events", len(new_historic.archived))
            for k, v in metrics_data.get("cases", {}).items():
                new_metrics._cases[k] = v
            for k, v in metrics_data.get("turns", {}).items():
                new_metrics._turns[k] = v

        observatory.metrics = new_metrics

        return True, []

    # -------------------------------------------------------------------------
    # 3. SEQUENTIAL INSERTION LOAD
    # -------------------------------------------------------------------------

    @staticmethod
    def load_by_insertions(
        filepath: str,
        geographical_map: Geographical_map | None = None
    ) -> dict[str, Any]:
        """
        Loads a sequence of events from a JSON file and applies the exact same comparator
        and insertion order to both an AVL (with active balancing) and a regular BST (without balancing).

        Validates that no duplicate event ID exists in the insertion sequence;
        any duplicate ID immediately invalidates the file (raises ValueError).

        Returns a dictionary containing:
        - 'avl': The constructed AVL tree.
        - 'bst': The constructed BST tree.
        - 'events': The list of Event instances in order of insertion.
        - 'metrics': Comparison metrics (root, height, max_depth, leaves count).
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            events_data = data
        elif isinstance(data, dict) and "events" in data:
            events_data = data["events"]
        else:
            raise ValueError("Invalid format for insertions: Expected a JSON array of events or an object with 'events'.")

        seen_ids: set[int] = set()
        events_list: list[Event] = []

        avl = AVL(id=1, stress_mode=False)
        bst = BST(id=2)

        for item in events_data:
            eid = int(item["id"])
            if eid in seen_ids:
                raise ValueError(f"Duplicate event ID {eid} found in insertion sequence; invalid file.")
            seen_ids.add(eid)

            mag = float(item["magnitude"])
            depth = float(item["depth"])
            epicenter = tuple(item["epicenter"])
            dt = datetime.fromisoformat(item["date_time"])
            review = int(item.get("review", 1))
            attention = item.get("attention_state", "Pending")
            status = item.get("status", "Active")

            # Determine priority: if stored, use it; otherwise compute it
            if "priority" in item:
                priority = int(item["priority"])
            else:
                priority = ScenarioPersistence._compute_priority(mag, depth, epicenter, geographical_map)

            ev = Event(
                id=eid,
                priority=priority,
                magnitude=mag,
                depth=depth,
                epicenter=epicenter,
                date_time=dt,
                review=review,
                attention_state=attention,
                status=status,
            )
            events_list.append(ev)

            # Insert into both trees with identical key K = (P, M, I)
            avl.insert(Node(id=eid, event=ev))
            bst.insert(Node(id=eid, event=ev))

        # Compute comparative structural metrics
        avl_depths = avl.get_all_nodes_with_depth()
        bst_depths = bst.get_all_nodes_with_depth()

        avl_max_depth = max((d for _, d in avl_depths), default=-1)
        bst_max_depth = max((d for _, d in bst_depths), default=-1)

        avl_leaves = sum(1 for n, _ in avl_depths if n.is_leaf())
        bst_leaves = sum(1 for n, _ in bst_depths if n.is_leaf())

        metrics = {
            "avl_root_id": avl.root.id if avl.root else None,
            "bst_root_id": bst.root.id if bst.root else None,
            "avl_height": avl.height(),
            "bst_height": bst.height(),
            "avl_max_depth": avl_max_depth,
            "bst_max_depth": bst_max_depth,
            "avl_leaves": avl_leaves,
            "bst_leaves": bst_leaves,
            "total_events": len(events_list),
        }

        return {
            "avl": avl,
            "bst": bst,
            "events": events_list,
            "metrics": metrics,
        }

    # -------------------------------------------------------------------------
    # Auxiliary Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _compute_priority(
        magnitude: float,
        depth: float,
        epicenter: tuple[float, float],
        geographical_map: Geographical_map | None = None
    ) -> int:
        """
        Priority calculation rule according to Section 4:
        - 3 (High): M >= 6.0 or (M >= 4.5 and depth <= 30.0 km in a populated area).
        - 2 (Medium): M >= 4.5.
        - 1 (Low): All other events.
        """
        is_populated = False
        if geographical_map is not None:
            is_populated = geographical_map.is_in_populated_zone(epicenter[0], epicenter[1])

        if magnitude >= 6.0 or (magnitude >= 4.5 and depth <= 30.0 and is_populated):
            return 3
        elif magnitude >= 4.5:
            return 2
        else:
            return 1

    @staticmethod
    def _serialize_tree(tree: AVL | None) -> dict[str, Any]:
        if tree is None or tree.root is None:
            return {"root_id": None, "nodes": []}

        nodes_data: list[dict[str, Any]] = []
        all_nodes = tree.preorder()

        for nd in all_nodes:
            nodes_data.append({
                "id": nd.id,
                "left_id": nd.left_son.id if nd.left_son is not None else None,
                "right_id": nd.right_son.id if nd.right_son is not None else None,
                "height": nd.height,
                "balance_factor": nd.balance_factor(),
                "event": ScenarioPersistence._serialize_event(nd.event),
            })

        return {
            "root_id": tree.root.id,
            "nodes": nodes_data,
        }

    @staticmethod
    def _serialize_event(event: Event | None) -> dict[str, Any]:
        if event is None:
            return {}

        station_ids = [
            s.id for s in event.origin_stations if hasattr(s, "id")
        ]
        return {
            "id": event.id,
            "priority": event.priority,
            "magnitude": event.magnitude,
            "depth": event.depth,
            "epicenter": list(event.epicenter),
            "date_time": event.date_time.isoformat(),
            "review": event.review,
            "attention_state": event.attention_state,
            "status": event.status,
            "origin_stations": station_ids,
        }