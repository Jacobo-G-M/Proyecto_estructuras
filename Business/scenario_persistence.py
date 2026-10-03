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
        # Serialize the active AVL tree topology, preserving parent-child pointers and node heights
        tree_data = ScenarioPersistence._serialize_tree(observatory.tree)

        # Serialize geographical zones for spatial classification (e.g., populated areas)
        zones_data = []
        if observatory.geographical_map is not None:
            for zone in observatory.geographical_map.zones:
                # Convert polygon boundary coordinate tuples to JSON-serializable lists
                zones_data.append({
                    "id": zone.id,
                    "name": zone.name,
                    "is_populated": zone.is_populated,
                    "ubication_x": list(zone.ubication_x),
                    "ubication_y": list(zone.ubication_y),
                })

        # Serialize seismic monitoring stations
        stations_data = []
        for station in observatory.stations:
            # Map station coordinate tuple (x, y) to a serializable list
            stations_data.append({
                "id": station.id,
                "name": station.name,
                "coords": list(station.coords),
            })

        # Serialize historical catalogs, separating archived events from soft-deleted events
        historic_data = {"archived": [], "deleted": []}
        if observatory.historic is not None:
            # Extract and serialize all archived event instances
            for ev in observatory.historic.archived.values():
                historic_data["archived"].append(ScenarioPersistence._serialize_event(ev))
            # Extract and serialize all soft-deleted event instances
            for ev in observatory.historic.deleted.values():
                historic_data["deleted"].append(ScenarioPersistence._serialize_event(ev))

        # Serialize pending report queue while strictly preserving original FIFO queue order
        queue_data = []
        if observatory.report_queue is not None:
            for report in observatory.report_queue.view_all():
                # Extract integer IDs of originating monitoring stations
                station_ids = [
                    s.id for s in report.origin_station if hasattr(s, "id")
                ]
                # Format report payload with ISO-8601 timestamp and coordinates list
                queue_data.append({
                    "id": report.id,
                    "magnitude": report.magnitude,
                    "depth": report.depth,
                    "epicenter": list(report.epicenter),
                    "date_time": report.date_time.isoformat(),
                    "review": report.review,
                    "origin_stations": station_ids,
                })

        # Serialize event replica associations (graph clusters of related seismic events)
        associations_data = []
        for assoc in observatory.associations:
            # Capture reference event ID (the primary seismic event in the cluster)
            ref_id = assoc.chosen_reference.id if assoc.chosen_reference is not None else None
            # Collect IDs of all linked replica events referencing this cluster
            child_ids = [
                child.id for child in assoc.referenced_by if child is not None
            ]
            associations_data.append({
                "id": assoc.id,
                "chosen_reference_id": ref_id,
                "referenced_by_ids": child_ids,
            })

        # Serialize observatory operational metrics and statistical performance counters
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

        # Package complete scenario snapshot matching specification schema version 1.0
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
        Ensures destination directories exist and encodes with UTF-8 indentation.
        """
        # Generate the structured scenario dictionary
        data = ScenarioPersistence.export_to_dict(observatory)
        # Ensure that any parent directory path exists prior to file writing
        dirname = os.path.dirname(filepath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        # Write formatted JSON data with UTF-8 encoding
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

        # Verify that root scenario structure is a valid JSON dictionary
        if not isinstance(data, dict):
            return ["Invalid scenario format: Root must be a JSON object."]

        # ---------------------------------------------------------------------
        # Step 0: Validate simulation_clock format if present
        # ---------------------------------------------------------------------
        # The simulation clock coordinates temporal windows across the observatory.
        # It must conform strictly to the ISO-8601 standard (e.g., '2026-03-31T14:30:00').
        if "simulation_clock" in data:
            clock_str = data["simulation_clock"]
            try:
                datetime.fromisoformat(clock_str)
            except Exception:
                errors.append(f"Invalid ISO-8601 simulation_clock format: '{clock_str}'.")

        # ---------------------------------------------------------------------
        # Step 1: Parse and instantiate geographical zones for priority evaluation
        # ---------------------------------------------------------------------
        # Priority rules require knowing whether an epicenter lies inside
        # a populated geographical zone. If zones are defined in the JSON payload, we
        # instantiate a temporary Geographical_map using polygon bounding vertices
        # (ubication_x, ubication_y) to allow spatial Point-in-Polygon queries in Step 6.
        # ---------------------------------------------------------------------
        # Step 1: Parse and instantiate geographical zones for priority evaluation
        # ---------------------------------------------------------------------
        # Priority rules require knowing whether an epicenter lies inside
        # a populated geographical zone. If zones are defined in the JSON payload, we
        # instantiate a temporary Geographical_map using polygon bounding vertices
        # (ubication_x, ubication_y) to allow spatial Point-in-Polygon queries in Step 6.
        map_to_use = geographical_map
        # Conditional Check: Check if custom geographical zones are provided in scenario data
        if "zones" in data:
            # Conditional Check: Ensure 'zones' is a valid list of zone objects
            if not isinstance(data["zones"], list):
                errors.append("'zones' must be a list of zone objects.")
            else:
                try:
                    parsed_zones = []
                    # Loop: Iterate through each zone descriptor with its list index
                    for idx, z in enumerate(data["zones"]):
                        # Conditional Check: Guard against non-dict elements inside the 'zones' array
                        if not isinstance(z, dict):
                            errors.append(f"Zone at index {idx} is not a valid JSON object.")
                            continue
                        # Bounding coordinate lists are converted into immutable tuples
                        # to represent the 2D polygon boundaries of the geographical zone.
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

        # ---------------------------------------------------------------------
        # Step 2: Verify presence and type of the tree structure section
        # ---------------------------------------------------------------------
        # The 'tree' section is mandatory; it contains the root node ID and the flat
        # list of serialized node descriptors representing the active AVL tree.
        tree_section = data.get("tree")
        if not isinstance(tree_section, dict):
            errors.append("Missing or invalid 'tree' object in scenario.")
            return errors

        root_id = tree_section.get("root_id")
        nodes_list = tree_section.get("nodes", [])
        if not isinstance(nodes_list, list):
            errors.append("'nodes' in tree section must be a list.")
            return errors

        # ---------------------------------------------------------------------
        # Step 3: Node Integrity and ID Uniqueness across Catalogs
        # ---------------------------------------------------------------------
        # Invariant: Each seismic event must possess a unique integer identifier.
        # Furthermore, the system partitions events into three mutually exclusive lifecycle catalogs:
        # 1. Active: Currently stored as a Node inside the operational AVL tree.
        # 2. Archived: Past events preserved in Historic.archived.
        # 3. Deleted: Soft-deleted events preserved in Historic.deleted.
        # No event ID may appear in more than one catalog simultaneously.
        active_ids = set()
        # Loop: Iterate through each node descriptor in the active tree's 'nodes' list.
        # `enumerate` provides both the zero-based index `idx` (for diagnostic messages) and the item `nd`.
        for idx, nd in enumerate(nodes_list):
            # Conditional Check 1 (Node Object Type):
            # Guard against malformed entries (e.g. primitive values or nulls) inside the nodes list.
            # If invalid, record error and skip to the next element with `continue`.
            if not isinstance(nd, dict):
                errors.append(f"Node at index {idx} is not a valid JSON object.")
                continue

            nid = nd.get("id")
            # Conditional Check 2 (Node ID Validation & Python Boolean Guard):
            # In Python, `bool` subclasses `int` (`issubclass(bool, int) == True`).
            # Therefore, `isinstance(True, int)` evaluates to True. We must explicitly test:
            # - `nid is None`: rejects omitted or null IDs.
            # - `not isinstance(nid, int)`: rejects non-numeric types (strings, floats, dicts).
            # - `isinstance(nid, bool)`: strictly rejects JSON booleans (`true`/`false`).
            # If invalid, record error and `continue` to the next node.
            if nid is None or not isinstance(nid, int) or isinstance(nid, bool):
                errors.append(f"Node at index {idx} is missing a valid integer 'id'.")
                continue

            # Conditional Check 3 (Active Tree ID Uniqueness):
            # Check if this node ID was already registered in `active_ids`.
            # If present, record a duplicate ID violation.
            if nid in active_ids:
                errors.append(f"Duplicate active node ID {nid} found in tree nodes.")
            # Register the valid integer ID in the active set
            active_ids.add(nid)

            # Conditional Check 4 (Embedded Event Payload Object):
            # Each node must embed a valid dictionary representing the underlying Event domain model.
            ev = nd.get("event")
            if not isinstance(ev, dict):
                errors.append(f"Node {nid} is missing a valid 'event' dictionary object.")
                continue

            # Conditional Check 5 (Node-to-Event ID Matching Invariant):
            # A tree Node and its contained Event represent the same logical entity;
            # their identifiers must match identically (Node.id == Event.id).
            if ev.get("id") != nid:
                errors.append(f"Node {nid} id mismatch with internal event id {ev.get('id')}.")

            # Conditional Check 6 (Temporal Format Validation):
            # Check whether 'date_time' is present and conforms to ISO-8601.
            dt_str = ev.get("date_time")
            if dt_str:
                try:
                    datetime.fromisoformat(dt_str)
                except Exception:
                    # Captures invalid dates (e.g., '2026-02-31' or non-ISO formatting)
                    errors.append(f"Event {nid} has invalid ISO-8601 date_time format '{dt_str}'.")
            else:
                errors.append(f"Event {nid} is missing required 'date_time'.")

            # Conditional Check 7 (Epicenter Coordinates Validation):
            # Epicenter must be a sequence of at least two numeric coordinates (x, y / longitude, latitude).
            # 1. `not isinstance(epi, (list, tuple))`: verifies it is an iterable list or tuple.
            # 2. `len(epi) < 2`: ensures at least two coordinate dimensions exist.
            # 3. `not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in epi[:2])`:
            #    ensures both x and y are numbers and rejects boolean literals.
            epi = ev.get("epicenter")
            if not isinstance(epi, (list, tuple)) or len(epi) < 2 or not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in epi[:2]):
                errors.append(f"Event {nid} has invalid epicenter coordinates.")

        # Validate archived historic events catalog
        # We track archived event IDs to ensure internal catalog uniqueness and cross-catalog disjointness.
        archived_ids = set()
        historic_section = data.get("historic", {})
        # Conditional Check: Ensure the "historic" container is a valid dictionary.
        # This prevents crashes if "historic" is passed as a primitive, list, or null.
        if isinstance(historic_section, dict):
            # Loop: Iterate over each event in the "archived" list.
            # `historic_section.get("archived", [])` safely returns an empty list if the key is missing.
            for idx, ev in enumerate(historic_section.get("archived", [])):
                # Conditional Check 1 (Payload Type):
                # Ensure the archived event item is a dictionary object.
                # If a primitive (string, number, null) is found, record error and `continue`.
                if not isinstance(ev, dict):
                    errors.append(f"Archived event at index {idx} is not a valid JSON object.")
                    continue

                eid = ev.get("id")
                # Conditional Check 2 (ID Validation & Python Boolean Guard):
                # Enforce that ID exists, is an integer, and is NOT a boolean literal.
                if eid is None or not isinstance(eid, int) or isinstance(eid, bool):
                    errors.append(f"Archived event at index {idx} is missing a valid integer 'id'.")
                    continue

                # Conditional Check 3 (Catalog Uniqueness):
                # Detect duplicate IDs within the archived events list.
                if eid in archived_ids:
                    errors.append(f"Duplicate archived event ID {eid} found in historic.")
                # Register valid integer ID into archived_ids set
                archived_ids.add(eid)

                # Conditional Check 4 (Date Validation):
                # If 'date_time' is specified, verify it conforms to ISO-8601 formatting.
                dt_str = ev.get("date_time")
                if dt_str:
                    try:
                        datetime.fromisoformat(dt_str)
                    except Exception:
                        errors.append(f"Archived event {eid} has invalid date_time format '{dt_str}'.")

            # Validate soft-deleted historic events catalog
            # Soft-deleted events are retained in Historic.deleted for auditing and recovery.
            deleted_ids = set()
            # Loop: Iterate over each event in the "deleted" list.
            for idx, ev in enumerate(historic_section.get("deleted", [])):
                # Conditional Check 1 (Payload Type):
                # Ensure the deleted event item is a dictionary object.
                if not isinstance(ev, dict):
                    errors.append(f"Deleted event at index {idx} is not a valid JSON object.")
                    continue

                eid = ev.get("id")
                # Conditional Check 2 (ID Validation & Python Boolean Guard):
                # Enforce integer ID type and reject booleans.
                if eid is None or not isinstance(eid, int) or isinstance(eid, bool):
                    errors.append(f"Deleted event at index {idx} is missing a valid integer 'id'.")
                    continue

                # Conditional Check 3 (Catalog Uniqueness):
                # Detect duplicate IDs within the deleted events list.
                if eid in deleted_ids:
                    errors.append(f"Duplicate deleted event ID {eid} found in historic.")
                # Register valid integer ID into deleted_ids set
                deleted_ids.add(eid)

                # Conditional Check 4 (Date Validation):
                # Verify ISO-8601 date_time format if present.
                dt_str = ev.get("date_time")
                if dt_str:
                    try:
                        datetime.fromisoformat(dt_str)
                    except Exception:
                        errors.append(f"Deleted event {eid} has invalid date_time format '{dt_str}'.")

        # Global Lifecycle Invariant: Mutually Disjoint Catalogs
        # An event cannot simultaneously be Active and Archived, Active and Deleted,
        # or Archived and Deleted. Set intersection (&) detects any cross-catalog collisions.
        # Condition 1: Check active vs archived collisions
        active_archived_overlap = active_ids & archived_ids
        if active_archived_overlap:
            errors.append(f"ID overlap between active and archived catalogs: {sorted(active_archived_overlap)}.")

        # Condition 2: Check active vs deleted collisions
        active_deleted_overlap = active_ids & deleted_ids
        if active_deleted_overlap:
            errors.append(f"ID overlap between active and deleted catalogs: {sorted(active_deleted_overlap)}.")

        # Condition 3: Check archived vs deleted collisions
        archived_deleted_overlap = archived_ids & deleted_ids
        if archived_deleted_overlap:
            errors.append(f"ID overlap between archived and deleted catalogs: {sorted(archived_deleted_overlap)}.")

        # ---------------------------------------------------------------------
        # Step 4: Topology and Graph Integrity
        # ---------------------------------------------------------------------
        # Build an O(1) fast lookup table of all valid active nodes indexed by integer ID
        nodes_dict = {
            nd["id"]: nd for nd in nodes_list
            if isinstance(nd, dict) and isinstance(nd.get("id"), int) and not isinstance(nd.get("id"), bool)
        }

        # Case 4A: Empty tree scenario (root_id is null)
        # If root_id is None, the tree must contain zero nodes; otherwise it is inconsistent.
        if root_id is None:
            if len(nodes_list) > 0:
                errors.append("Tree root_id is null but nodes list is not empty.")
            return errors

        # Case 4B: Root node existence
        # The specified root_id must resolve to an actual entry in the nodes list.
        if root_id not in nodes_dict:
            errors.append(f"Tree root_id {root_id} does not exist in nodes list.")
            return errors

        # Initialize in-degree (parent count) for every active node to 0
        in_degrees: dict[int, int] = {nid: 0 for nid in nodes_dict}
        # Loop: Iterate through each active node and inspect its declared child pointers
        for nid, nd in nodes_dict.items():
            left_id = nd.get("left_id")
            right_id = nd.get("right_id")

            # Conditional Branch 1: Validate left child pointer integrity if defined
            if left_id is not None:
                # Conditional 1A: Check if the referenced left child exists in active nodes
                if left_id not in nodes_dict:
                    # Dangling pointer: refers to a node ID that does not exist in the active catalog
                    errors.append(f"Node {nid} has invalid left_id reference {left_id}.")
                # Conditional 1B: Disallow self-referencing loops (node pointing to itself)
                elif left_id == nid:
                    # Self-loop: causes infinite recursive traversals
                    errors.append(f"Node {nid} has a self-referencing left child loop.")
                else:
                    # Valid child edge: increment in-degree (parent count) of the left child
                    in_degrees[left_id] += 1

            # Conditional Branch 2: Validate right child pointer integrity if defined
            if right_id is not None:
                # Conditional 2A: Check if the referenced right child exists in active nodes
                if right_id not in nodes_dict:
                    # Dangling pointer: refers to a node ID that does not exist in the active catalog
                    errors.append(f"Node {nid} has invalid right_id reference {right_id}.")
                # Conditional 2B: Disallow self-referencing loops (node pointing to itself)
                elif right_id == nid:
                    # Self-loop: causes infinite recursive traversals
                    errors.append(f"Node {nid} has a self-referencing right child loop.")
                else:
                    # Valid child edge: increment in-degree (parent count) of the right child
                    in_degrees[right_id] += 1

            # Conditional Branch 3: Disallow twin-child collision
            # A binary tree node cannot point to the exact same child on both left and right branches
            if left_id is not None and right_id is not None and left_id == right_id:
                errors.append(f"Node {nid} points to the same node {left_id} for both left and right children.")

        # Root In-Degree Invariant:
        # In a directed tree graph, the root node is the global source and must have in-degree 0.
        # If in_degrees[root_id] != 0, another node is erroneously pointing to root as its child.
        if in_degrees.get(root_id, 0) != 0:
            errors.append(f"Root node {root_id} cannot have a parent (in-degree is {in_degrees[root_id]}).")

        # Non-Root Vertex Invariant:
        # Every node in a binary tree other than the root must have exactly one parent (in-degree == 1).
        # Loop: Check parent count for every node in the tree
        for nid, deg in in_degrees.items():
            # Conditional: Flag any non-root node whose parent count is not exactly 1
            # - If deg == 0: node is an unattached orphan with no parent.
            # - If deg > 1: multiple parents point to this child (forming a DAG or cycle).
            if nid != root_id and deg != 1:
                errors.append(f"Node {nid} must have exactly one parent, but has {deg}.")

        # Cycle Detection and Reachability using Depth-First Search (DFS)
        # Starting at root_id, we traverse all reachable vertices downward.
        # If any node is encountered more than once during traversal, a cycle exists.
        visited: set[int] = set()
        has_cycle = False

        def _traverse(cur_id: int):
            nonlocal has_cycle
            # Cycle Check: If cur_id is already in visited, a back-edge or cross-edge was traversed
            if cur_id in visited:
                has_cycle = True
                return
            # Mark current node as visited
            visited.add(cur_id)
            cur_nd = nodes_dict[cur_id]
            l_id = cur_nd.get("left_id")
            r_id = cur_nd.get("right_id")
            # Recursive Step: Traverse left child if pointer is valid
            if l_id is not None and l_id in nodes_dict:
                _traverse(l_id)
            # Recursive Step: Traverse right child if pointer is valid
            if r_id is not None and r_id in nodes_dict:
                _traverse(r_id)

        # Initiate downward DFS traversal starting from tree root
        _traverse(root_id)

        # Conditional Check: Record error if a cyclic graph structure was detected
        if has_cycle:
            errors.append("Cycle detected in tree nodes graph.")

        # Disconnected Components Check (Reachability Invariant):
        # In a valid rooted tree, every single node in the nodes list must be reachable from root_id.
        # If len(visited) != len(nodes_dict), there exist floating islands or orphan subtrees.
        if len(visited) != len(nodes_dict):
            # Compute set difference to identify the exact unreachable node IDs
            unreachable = set(nodes_dict.keys()) - visited
            errors.append(f"Unreachable nodes disconnected from root: {sorted(unreachable)}.")

        # ---------------------------------------------------------------------
        # Step 5: Global BST Order Verification
        # ---------------------------------------------------------------------
        # Fundamental BST Invariant:
        # In any valid Binary Search Tree, an in-order traversal (Left -> Node -> Right)
        # flattens the 2D tree hierarchy into a 1D sequence of search keys that MUST be
        # strictly monotonically increasing.
        #
        # In this system, the search key is a 3-element composite tuple K = (P, M, I):
        # - P: Priority in {1, 2, 3} (primary dimension).
        # - M: Magnitude as a float (secondary dimension).
        # - I: Event ID as an integer (tertiary tiebreaker guaranteeing strict uniqueness).
        #
        # Python evaluates tuple comparison lexicographically:
        # (P1, M1, I1) < (P2, M2, I2) checks P1 < P2; if equal, M1 < M2; if equal, I1 < I2.
        # Because all active event IDs are strictly unique, no two nodes can have identical keys.
        inorder_keys: list[tuple[tuple[int, float, int], int]] = []

        def _inorder(cur_id: int):
            cur_nd = nodes_dict[cur_id]
            l_id = cur_nd.get("left_id")
            r_id = cur_nd.get("right_id")
            # In-order: Step 1 - Explore Left subtree
            if l_id is not None and l_id in nodes_dict:
                _inorder(l_id)
            # In-order: Step 2 - Visit current node and extract its composite key K = (P, M, I)
            ev = cur_nd.get("event")
            if isinstance(ev, dict):
                k = (ev.get("priority", 0), float(ev.get("magnitude", 0.0)), int(ev.get("id", 0)))
                inorder_keys.append((k, cur_id))
            # In-order: Step 3 - Explore Right subtree
            if r_id is not None and r_id in nodes_dict:
                _inorder(r_id)

        # Only verify ordering if the tree is acyclic and fully connected
        if not has_cycle and len(visited) == len(nodes_dict):
            _inorder(root_id)
            # Compare each adjacent pair in the in-order traversal sequence
            for i in range(len(inorder_keys) - 1):
                k1, id1 = inorder_keys[i]
                k2, id2 = inorder_keys[i + 1]
                # If key1 >= key2, the strict monotonic ascending BST property is violated
                if k1 >= k2:
                    errors.append(
                        f"Global BST order violation: Node {id1} key {k1} >= Node {id2} key {k2} in in-order sequence."
                    )

        # ---------------------------------------------------------------------
        # Step 6: Verify Heights, Balance Factors, and Event Priorities
        # ---------------------------------------------------------------------
        # Structural Invariant: Post-Order Height and Balance Factor Recalculation
        # Why Post-Order (Left -> Right -> Root)?
        # The height H(N) and balance factor BF(N) of any node N are inductive properties:
        #   H(N) = max(H(left_child), H(right_child)) + 1
        #   BF(N) = H(left_child) - H(right_child)
        # Neither H(N) nor BF(N) can be computed until both the left and right subtrees have
        # completed their evaluations and reported their exact heights.
        #
        # Sentinel Base Case:
        # An empty subtree slot (represented by None) has a defined height of -1.
        # Consequently, a leaf node with two None children calculates:
        #   H(leaf) = max(-1, -1) + 1 = 0
        #   BF(leaf) = -1 - (-1) = 0
        max_abs_bf = 0

        def _verify_metrics(cur_id: int) -> int:
            nonlocal max_abs_bf
            cur_nd = nodes_dict[cur_id]
            l_id = cur_nd.get("left_id")
            r_id = cur_nd.get("right_id")

            # Recursive post-order traversal: compute heights of subtrees (-1 for absent child)
            left_h = _verify_metrics(l_id) if (l_id is not None and l_id in nodes_dict) else -1
            right_h = _verify_metrics(r_id) if (r_id is not None and r_id in nodes_dict) else -1

            # Recalculate true height and balance factor from children
            calc_h = max(left_h, right_h) + 1
            calc_bf = left_h - right_h
            if abs(calc_bf) > max_abs_bf:
                max_abs_bf = abs(calc_bf)

            # Compare stored height against the recalculated height
            stored_h = cur_nd.get("height")
            if stored_h is not None and stored_h != calc_h:
                errors.append(f"Node {cur_id}: stored height {stored_h} does not match calculated height {calc_h}.")

            # Compare stored balance factor against the recalculated balance factor
            stored_bf = cur_nd.get("balance_factor")
            if stored_bf is not None and stored_bf != calc_bf:
                errors.append(f"Node {cur_id}: stored balance factor {stored_bf} does not match calculated {calc_bf}.")

            # Verify business priority calculation according to Section 4 rules:
            # - Priority 3 (High): M >= 6.0 OR (M >= 4.5 and depth <= 30.0 in a populated area).
            # - Priority 2 (Medium): M >= 4.5.
            # - Priority 1 (Low): All other seismic events.
            ev_data = cur_nd.get("event")
            if isinstance(ev_data, dict):
                try:
                    mag = float(ev_data.get("magnitude", 0.0))
                    depth = float(ev_data.get("depth", 0.0))
                    epicenter = tuple(ev_data.get("epicenter", (0.0, 0.0)))
                    stored_p = ev_data.get("priority")

                    calc_p = ScenarioPersistence._compute_priority(mag, depth, epicenter, map_to_use)
                    if stored_p is not None and stored_p != calc_p:
                        errors.append(
                            f"Event {cur_id}: stored priority {stored_p} does not match calculated priority {calc_p}."
                        )
                except Exception as e:
                    errors.append(f"Failed to verify priority for Node {cur_id}: {e}")

            return calc_h

        # Execute metric verification if the tree structure is intact
        if not has_cycle and len(visited) == len(nodes_dict):
            _verify_metrics(root_id)

        # ---------------------------------------------------------------------
        # Step 7: Stress Mode Enforcement
        # ---------------------------------------------------------------------
        # AVL Tree Invariant:
        # A tree is an AVL tree if and only if for every node u, |BF(u)| <= 1.
        # If any node has |BF| > 1, the topology is structurally unbalanced.
        # In standard operational mode, loading an unbalanced tree is strictly forbidden.
        # It may only be loaded when stress_mode is active (either enabled in the file
        # or explicitly overridden via stress_mode_override=True).
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
        # TRANSACTIONAL RECONSTRUCTION: Assemble state locally before applying
        # ---------------------------------------------------------------------
        try:
            # Safely extract threshold parameters dictionary from the parsed JSON payload
            params = data.get("parameters", {})
            # Parse maximum capacity limit L; fallback to existing observatory setting if omitted
            new_limit = int(params["limit_L"]) if "limit_L" in params else observatory.limit
            # Parse maximum time delta window W (in minutes) for replica associations
            new_max_time = float(params["max_time_W"]) if "max_time_W" in params else observatory.max_time
            # Parse maximum epicenter distance threshold R (in kilometers) for replica associations
            new_distance_epicenter = float(params["distance_epicenter_R"]) if "distance_epicenter_R" in params else observatory.distance_epicenter
            # Parse maximum active tree age threshold T (in turns) before automatic archival
            new_max_tree_age = int(params["max_tree_age_T"]) if "max_tree_age_T" in params else observatory.max_tree_age

            # Resolve stress mode: explicit method argument takes precedence over file-level flag
            file_stress = bool(data.get("stress_mode", False))
            new_stress_mode = file_stress if stress_mode_override is None else stress_mode_override

            # Parse simulation clock timestamp from ISO-8601 string, or retain current clock
            new_clock = datetime.fromisoformat(data["simulation_clock"]) if "simulation_clock" in data else observatory.clock_simulation

            # Reconstruct geographical zones for populated area detection
            new_geographical_map = observatory.geographical_map
            if "zones" in data and isinstance(data["zones"], list):
                reconstructed_zones = []
                for z in data["zones"]:
                    # Create Zone model instances with boundary coordinate tuples
                    reconstructed_zones.append(Zone(
                        id=z["id"],
                        name=z.get("name", ""),
                        is_populated=bool(z.get("is_populated", False)),
                        ubication_x=tuple(z["ubication_x"]),
                        ubication_y=tuple(z["ubication_y"]),
                    ))
                new_geographical_map = Geographical_map(zones=reconstructed_zones)

            # Reconstruct seismic sensor stations dictionary for fast O(1) ID lookups
            stations_dict: dict[int, Station] = {}
            if "stations" in data and isinstance(data["stations"], list):
                for s in data["stations"]:
                    st = Station(id=s["id"], name=s["name"], coords=tuple(s["coords"]))
                    stations_dict[s["id"]] = st
            # Update stations list or preserve existing observatory stations
            new_stations = list(stations_dict.values()) if stations_dict else observatory.stations

            # Reconstruct tree topology directly without triggering balancing rotations
            tree_section = data.get("tree", {})
            nodes_list = tree_section.get("nodes", [])
            root_id = tree_section.get("root_id")

            # Initialize a fresh AVL container instance wired to the observatory rotation callback
            new_tree = AVL(
                id=1,
                stress_mode=new_stress_mode,
                on_rotation=observatory._handle_tree_rotation,
            )

            # In-memory lookup dictionaries for O(1) pointer wiring and catalog caching
            nodes_map: dict[int, Node] = {}
            events_dict: dict[int, Event] = {}

            # Pass 1: Allocate Event domain models and Node wrappers without connecting child pointers
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
                # Link originating monitoring stations using the station lookup dictionary
                for sid in ev_data.get("origin_stations", []):
                    if sid in stations_dict:
                        ev.add_origin_station(stations_dict[sid])

                # Wrap the event in a tree Node and index by its integer ID
                node = Node(id=nd["id"], event=ev)
                nodes_map[nd["id"]] = node
                events_dict[ev.id] = ev

            # Pass 2: Wire explicit child pointers and bidirectional father references
            for nd in nodes_list:
                cur_node = nodes_map[nd["id"]]
                left_id = nd.get("left_id")
                right_id = nd.get("right_id")

                # Connect left child and establish bidirectional child -> father pointer
                if left_id is not None and left_id in nodes_map:
                    left_node = nodes_map[left_id]
                    cur_node.left_son = left_node
                    left_node.father = cur_node

                # Connect right child and establish bidirectional child -> father pointer
                if right_id is not None and right_id in nodes_map:
                    right_node = nodes_map[right_id]
                    cur_node.right_son = right_node
                    right_node.father = cur_node

            # Designate the root node and enforce that the root's father pointer is strictly None
            if root_id is not None and root_id in nodes_map:
                new_tree.root = nodes_map[root_id]
                new_tree.root.father = None
            else:
                new_tree.root = None

            # Bottom-Up Post-Order Height Propagation:
            # When raw node pointers (left_son, right_son) are assigned directly,
            # internal `.height` properties remain uninitialized (defaulting to 0).
            # A post-order traversal (Left -> Right -> Root) is mathematically required
            # so that children compute their true heights BEFORE parent heights are calculated.
            def _post_order_heights(node: Node | None) -> None:
                if node is None:
                    return
                # Step 1: Recurse left subtree
                _post_order_heights(node.left_son)
                # Step 2: Recurse right subtree
                _post_order_heights(node.right_son)
                # Step 3: Compute current node's height based on freshly evaluated children:
                # node.height = 1 + max(h_left, h_right)
                node.update_height()

            # Execute bottom-up height propagation starting from the reconstructed root
            if new_tree.root is not None:
                _post_order_heights(new_tree.root)

            # Reconstruct Historical Catalogs (archived and soft-deleted events)
            new_historic = Historic()
            historic_section = data.get("historic", {})
            # Conditional Check: Verify that the "historic" section is a valid dictionary
            if isinstance(historic_section, dict):
                # Loop: Iterate over archived event dictionaries in the "archived" list
                for ev_data in historic_section.get("archived", []):
                    # Construct Event domain model with status forced to "Archived"
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
                    # Register into historic.archived catalog map
                    new_historic.archive_event(ev)

                # Loop: Iterate over deleted event dictionaries in the "deleted" list
                for ev_data in historic_section.get("deleted", []):
                    # Construct Event domain model with status forced to "Deleted"
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
                    # Register into historic.deleted catalog map
                    new_historic.delete_event(ev)

            # -----------------------------------------------------------------
            # Reconstruct Report Queue in exact FIFO order
            # -----------------------------------------------------------------
            new_queue = Report_Queue()
            # Loop: Iterate over pending report descriptors in arrival order
            for r_data in data.get("report_queue", []):
                # List Comprehension with Conditional: Resolve station foreign key IDs
                # Filters and retrieves Station instances present in stations_dict
                st_list = [
                    stations_dict[sid]
                    for sid in r_data.get("origin_stations", [])
                    if sid in stations_dict
                ]
                # Construct Report domain model with linked origin stations
                report = Report(
                    id=r_data["id"],
                    magnitude=float(r_data["magnitude"]),
                    depth=float(r_data["depth"]),
                    epicenter=tuple(r_data["epicenter"]),
                    date_time=datetime.fromisoformat(r_data["date_time"]),
                    review=int(r_data.get("review", 1)),
                    origin_station=st_list,
                )
                # Enqueue report to preserve original FIFO scheduling queue
                new_queue.enqueue(report)

            # -----------------------------------------------------------------
            # Reconstruct Replica Association Clusters (Cross-Catalog Resolution)
            # -----------------------------------------------------------------
            # An association cluster groups related seismic events (a primary chosen reference
            # and its subsequent replica earthquakes). Over the lifetime of an observatory,
            # some events may remain in the active AVL tree while their replicas have aged into
            # the historic archive, or vice-versa.
            # To resolve foreign key references accurately without data loss, we synthesize
            # a unified catalog dictionary (`all_catalog`) spanning all three lifecycle tiers:
            # 1. `events_dict`: Active events currently in the tree.
            # 2. `new_historic.archived`: Events archived due to time aging or tree capacity.
            # 3. `new_historic.deleted`: Soft-deleted invalid or duplicate events.
            all_catalog = dict(events_dict)
            all_catalog.update(new_historic.archived)
            all_catalog.update(new_historic.deleted)

            new_associations = []
            # Loop: Iterate through each association cluster definition
            for assoc_data in data.get("associations", []):
                ref_id = assoc_data.get("chosen_reference_id")
                # Conditional Check 1: Ensure the chosen reference event exists in unified catalog
                if ref_id in all_catalog:
                    assoc = Association(
                        assoc_id=assoc_data["id"],
                        chosen_reference=all_catalog[ref_id],
                    )
                    # Loop: Iterate through all replica child IDs linked to this association
                    for child_id in assoc_data.get("referenced_by_ids", []):
                        # Conditional Check 2: Only attach replicas that exist in the unified catalog
                        if child_id in all_catalog:
                            assoc.add_replica(all_catalog[child_id])
                    # Register completed cluster in the reconstructed associations list
                    new_associations.append(assoc)

            # Reconstruct Metrics and operational counters
            new_metrics = Metrics()
            metrics_data = data.get("metrics", {})
            if metrics_data:
                new_metrics.corrections_accepted = metrics_data.get("corrections_accepted", 0)
                new_metrics.discarded_reports = metrics_data.get("discarded_reports", 0)
                new_metrics.conflicts = metrics_data.get("conflicts", 0)
                new_metrics.active_events = metrics_data.get("active_events", len(events_dict))
                new_metrics.removed_events = metrics_data.get("removed_events", len(new_historic.deleted))
                new_metrics.archived_events = metrics_data.get("archived_events", len(new_historic.archived))
                # Restore case frequency dictionary
                for k, v in metrics_data.get("cases", {}).items():
                    new_metrics._cases[k] = v
                # Restore turn frequency dictionary
                for k, v in metrics_data.get("turns", {}).items():
                    new_metrics._turns[k] = v
            else:
                # Fallback: compute active, removed, and archived counts from reconstructed collections
                new_metrics.active_events = len(events_dict)
                new_metrics.removed_events = len(new_historic.deleted)
                new_metrics.archived_events = len(new_historic.archived)

            # Reaching this point guarantees 100% success. We now atomically bind all local
            # objects into the observatory in a single contiguous sequence of attribute updates.
            observatory.limit = new_limit
            observatory.max_time = new_max_time
            observatory.distance_epicenter = new_distance_epicenter
            observatory.max_tree_age = new_max_tree_age
            observatory.stress_mode = new_stress_mode
            observatory.clock_simulation = new_clock
            observatory.geographical_map = new_geographical_map
            observatory.stations = new_stations
            observatory.tree = new_tree
            observatory.events_dict = events_dict
            observatory.historic = new_historic
            observatory.report_queue = new_queue
            observatory.associations = new_associations
            observatory.metrics = new_metrics

            return True, []

        except Exception as e:
            # Transaction Rollback:
            # Because all modifications were isolated to local variables, the observatory's
            # state remains 100% unaltered. We return the diagnostic error message.
            return False, [f"Atomic reconstruction error: {e}"]

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
        # Ensure the specified file exists on the filesystem
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Parse JSON content with UTF-8 encoding
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalize data format: accept either a raw list of events or an object with an 'events' list
        # Conditional Branch: Format Normalization
        # Case A: Top-level JSON is a flat array of events `[{...}, {...}]`
        if isinstance(data, list):
            events_data = data
        # Case B: Top-level JSON is an object containing an 'events' array `{"events": [{...}, {...}]}`
        elif isinstance(data, dict) and "events" in data and isinstance(data["events"], list):
            events_data = data["events"]
        # Case C: Unrecognized format (e.g. primitive, string, or missing 'events' key)
        else:
            raise ValueError("Invalid format for insertions: Expected a JSON array of events or an object with 'events'.")

        # Track seen IDs for strict O(1) duplicate detection across the insertion sequence
        seen_ids: set[int] = set()
        # Maintain ordered list of reconstructed Event instances
        events_list: list[Event] = []

        # Instantiate balanced AVL tree (with rotations enabled) and unbalanced baseline BST
        avl = AVL(id=1, stress_mode=False)
        bst = BST(id=2)

        # Loop: Process each event record in the exact sequence specified by the JSON file
        for idx, item in enumerate(events_data):
            # Conditional Check 1: Ensure each array element is a valid JSON dictionary object
            if not isinstance(item, dict):
                raise ValueError(f"Event item at index {idx} is not a valid JSON object.")
            # Conditional Check 2: Verify presence of the mandatory 'id' property
            if "id" not in item:
                raise ValueError(f"Event item at index {idx} is missing required 'id'.")

            # Conditional Check 3: Strict Duplicate ID Detection
            # A duplicate event ID in the insertion sequence violates domain uniqueness and invalidates the file
            eid = int(item["id"])
            if eid in seen_ids:
                raise ValueError(f"Duplicate event ID {eid} found in insertion sequence; invalid file.")
            # Register event ID in seen set
            seen_ids.add(eid)

            # Extract physical event parameters
            mag = float(item["magnitude"])
            depth = float(item["depth"])
            epicenter = tuple(item["epicenter"])
            dt = datetime.fromisoformat(item["date_time"])
            review = int(item.get("review", 1))
            attention = item.get("attention_state", "Pending")
            status = item.get("status", "Active")

            # Conditional Branch: Determine Event Priority
            # If the priority is explicitly stated in the JSON, honor the stored value;
            # otherwise, dynamically compute it based on magnitude, depth, and populated zone status.
            if "priority" in item:
                priority = int(item["priority"])
            else:
                priority = ScenarioPersistence._compute_priority(mag, depth, epicenter, geographical_map)

            # Instantiate Event domain model
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

            # Insert into both trees using the identical composite key K = (Priority, Magnitude, ID)
            # AVL will perform automatic rebalancing rotations; BST will retain unbalanced topology
            avl.insert(Node(id=eid, event=ev))
            bst.insert(Node(id=eid, event=ev))

        # ---------------------------------------------------------------------
        # Comparative Structural Metric Evaluation
        # ---------------------------------------------------------------------
        # Retrieve all (node, depth) pairs from both trees via level-by-level traversal,
        # where root is defined at depth 0.
        avl_depths = avl.get_all_nodes_with_depth()
        bst_depths = bst.get_all_nodes_with_depth()

        # Compute maximum path length from root to any descendant node.
        # In balanced AVL: max_depth ~ 1.44 * log2(N).
        # In unbalanced BST: max_depth can approach N in sorted or clustered sequences.
        avl_max_depth = max((d for _, d in avl_depths), default=-1)
        bst_max_depth = max((d for _, d in bst_depths), default=-1)

        # Count leaf nodes (nodes with neither left nor right children).
        # A well-balanced tree typically distributes nodes symmetrically across the lowest levels,
        # resulting in a higher leaf count than a degenerate single-branch BST.
        avl_leaves = sum(1 for n, _ in avl_depths if n.is_leaf())
        bst_leaves = sum(1 for n, _ in bst_depths if n.is_leaf())

        # Compile comparison metrics between self-balancing AVL and standard BST
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

        # Return both trees alongside the ordered event list and comparative analysis
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
        # Determine whether the seismic epicenter falls within a populated geographical zone
        is_populated = False
        if geographical_map is not None and isinstance(epicenter, (tuple, list)) and len(epicenter) >= 2:
            try:
                is_populated = geographical_map.is_in_populated_zone(epicenter[0], epicenter[1])
            except Exception:
                is_populated = False

        # Apply multi-tiered business logic criteria
        if magnitude >= 6.0 or (magnitude >= 4.5 and depth <= 30.0 and is_populated):
            return 3
        elif magnitude >= 4.5:
            return 2
        else:
            return 1

    @staticmethod
    def _serialize_tree(tree: AVL | None) -> dict[str, Any]:
        """
        Serializes an AVL tree topology into a flat list of node descriptors,
        capturing node IDs, left/right child IDs, heights, balance factors, and event payloads.
        """
        # Return empty structure if tree is uninitialized or has no root
        if tree is None or tree.root is None:
            return {"root_id": None, "nodes": []}

        nodes_data: list[dict[str, Any]] = []
        # Pre-order traversal guarantees parent nodes are listed before their children
        all_nodes = tree.preorder()

        for nd in all_nodes:
            # Map child references to their integer IDs, or None for empty child slots
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
        """
        Serializes a single Event domain model into a JSON-compliant dictionary,
        converting timestamps to ISO-8601 strings and coordinates to lists.
        """
        if event is None:
            return {}

        # Extract integer station IDs from originating monitoring stations
        station_ids = [
            s.id for s in event.origin_stations if hasattr(s, "id")
        ]
        # Return serializable dictionary representation of the event
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