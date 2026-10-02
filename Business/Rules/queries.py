from __future__ import annotations
from datetime import datetime, timedelta
import math
from typing import Any

from Business.Structures.tree import Tree
from Business.Rules.asociation import Association
from Business.historic import Historic
from Models.event import Event
from Models.node import Node


class Queries:
    @staticmethod
    def top_k_pending(tree: Tree, k: int) -> tuple[list[Event], int]:
        """
        Query 1: Retrieves the top k pending events in descending order of K.
        Uses reverse in-order traversal (right -> root -> left) with early termination.
        Returns a tuple of (matching_events, examined_nodes_count).
        """
        examined_nodes = 0
        results: list[Event] = []

        if tree is None or tree.root is None or k is None or not isinstance(k, int) or isinstance(k, bool) or k <= 0:
            return results, examined_nodes

        def _reverse_inorder(current: Node | None) -> None:
            nonlocal examined_nodes
            if current is None or len(results) >= k:
                return

            # 1. Explore right subtree (greater K keys)
            _reverse_inorder(current.right_son)

            # Early pruning check after right branch
            if len(results) >= k:
                return

            # 2. Process current node
            examined_nodes += 1
            if current.event is not None:
                attention = str(current.event.attention_state).strip().lower()
                if attention in ("pending", "pendiente"):
                    results.append(current.event)

            # Early pruning check before entering left branch
            if len(results) >= k:
                return

            # 3. Explore left subtree (smaller K keys)
            _reverse_inorder(current.left_son)

        _reverse_inorder(tree.root)
        return results, examined_nodes

    @staticmethod
    def events_by_filters(
        tree: Tree,
        min_magnitude: float | None = None,
        max_magnitude: float | None = None,
        max_depth: float | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> tuple[list[Event], int]:
        """
        Query 2: Finds events with magnitude in [min_magnitude, max_magnitude],
        depth <= max_depth, and occurrence date in [start_date, end_date].
        Applies branch pruning based on priority and magnitude bounds.
        Returns a tuple of (matching_events, examined_nodes_count).
        """
        examined_nodes = 0
        results: list[Event] = []

        if tree is None or tree.root is None:
            return results, examined_nodes

        min_mag = float(min_magnitude) if min_magnitude is not None else -float('inf')
        max_mag = float(max_magnitude) if max_magnitude is not None else float('inf')
        max_d = float(max_depth) if max_depth is not None else float('inf')
        start_dt = start_date if start_date is not None else datetime.min
        end_dt = end_date if end_date is not None else datetime.max

        if min_mag > max_mag or start_dt > end_dt:
            return results, examined_nodes

        def _filter_helper(current: Node | None) -> None:
            nonlocal examined_nodes
            if current is None:
                return

            examined_nodes += 1
            ev = current.event

            if ev is not None:
                mag_ok = min_mag <= ev.magnitude <= max_mag
                depth_ok = ev.depth <= max_d
                date_ok = start_dt <= ev.date_time <= end_dt

                if mag_ok and depth_ok and date_ok:
                    results.append(ev)

                # Pruning based on key K = (P, M, I):
                # When priority is 3 (max priority) and magnitude exceeds max_magnitude,
                # all nodes in right subtree have priority 3 and magnitude >= ev.magnitude > max_magnitude.
                prune_right = (ev.priority == 3 and max_magnitude is not None and ev.magnitude > max_mag)

                # When priority is 1 (min priority) and magnitude is below min_magnitude,
                # all nodes in left subtree have priority 1 and magnitude <= ev.magnitude < min_magnitude.
                prune_left = (ev.priority == 1 and min_magnitude is not None and ev.magnitude < min_mag)

                if not prune_left:
                    _filter_helper(current.left_son)

                if not prune_right:
                    _filter_helper(current.right_son)
            else:
                _filter_helper(current.left_son)
                _filter_helper(current.right_son)

        _filter_helper(tree.root)
        return results, examined_nodes

    @staticmethod
    def event_associations(
        tree: Tree,
        historic: Historic | None,
        associations: list[Association],
        event_id: int,
        max_time_hours: float | None = None,
        max_distance_km: float | None = None
    ) -> tuple[dict[str, Any], int]:
        """
        Query 3: Locates candidates and chosen reference for an event, as well as
        events using it as reference, indicating whether each result is active or archived.
        Returns a tuple of (report_dict, examined_nodes_count).
        """
        examined_nodes = 0
        target_event: Event | None = None
        target_is_active = False

        max_t = float(max_time_hours) if max_time_hours is not None else 48.0
        max_d = float(max_distance_km) if max_distance_km is not None else 40.0

        # Helper to compute Euclidean distance
        def _calc_dist(p1: tuple[float, float], p2: tuple[float, float]) -> float:
            return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

        # 1. Locate the target event across active tree (recording examined nodes)
        if tree is not None and tree.root is not None:
            def _find_target(current: Node | None) -> None:
                nonlocal examined_nodes, target_event, target_is_active
                if current is None or target_event is not None:
                    return

                examined_nodes += 1
                if current.event is not None and current.event.id == event_id:
                    target_event = current.event
                    target_is_active = True
                    return

                _find_target(current.left_son)
                if target_event is None:
                    _find_target(current.right_son)

            _find_target(tree.root)

        # If not active, check historic archived catalog
        if target_event is None and historic is not None and hasattr(historic, "archived"):
            if event_id in historic.archived:
                target_event = historic.archived[event_id]
                target_is_active = False

        if target_event is None:
            return {}, examined_nodes

        # 2. Check chosen reference and replicas in associations
        chosen_ref_event: Event | None = None
        replicas: list[Event] = []

        if associations:
            for assoc in associations:
                # If target is the subject or reference of this association, collect its replicas
                is_subject_or_ref = (
                    getattr(assoc, "id", None) == event_id or
                    getattr(assoc, "_id", None) == event_id or
                    (assoc.chosen_reference is not None and getattr(assoc.chosen_reference, "id", None) == event_id)
                )
                if is_subject_or_ref:
                    # If target is subject (has chosen_reference distinct from target), resolve its reference
                    if assoc.chosen_reference is not None and getattr(assoc.chosen_reference, "id", None) != event_id:
                        if chosen_ref_event is None:
                            chosen_ref_event = assoc.chosen_reference
                    for rep in assoc.referenced_by:
                        if rep is not None and rep not in replicas and getattr(rep, "id", None) != event_id:
                            replicas.append(rep)

                # If target is a replica inside this association, its chosen reference is the association's reference
                is_replica = any(
                    getattr(rep, "id", None) == event_id
                    for rep in assoc.referenced_by
                    if rep is not None
                )
                if is_replica:
                    if chosen_ref_event is None:
                        chosen_ref_event = assoc.chosen_reference

        # 3. Discover candidate references (higher magnitude, strictly earlier, time <= W, dist <= R)
        candidates_raw: list[tuple[Event, str]] = []

        # Check in active tree
        if tree is not None and tree.root is not None:
            def _search_candidates(current: Node | None) -> None:
                nonlocal examined_nodes
                if current is None:
                    return

                examined_nodes += 1
                cand = current.event
                if cand is not None and cand.id != event_id:
                    if cand.magnitude > target_event.magnitude and cand.date_time < target_event.date_time:
                        time_hours = (target_event.date_time - cand.date_time).total_seconds() / 3600.0
                        dist = _calc_dist(cand.epicenter, target_event.epicenter)
                        if time_hours <= max_t and dist <= max_d:
                            candidates_raw.append((cand, "Activo"))

                _search_candidates(current.left_son)
                _search_candidates(current.right_son)

            _search_candidates(tree.root)

        # Check in historic archived events
        if historic is not None and hasattr(historic, "archived"):
            for cand_id, cand in historic.archived.items():
                if cand.id != event_id:
                    if cand.magnitude > target_event.magnitude and cand.date_time < target_event.date_time:
                        time_hours = (target_event.date_time - cand.date_time).total_seconds() / 3600.0
                        dist = _calc_dist(cand.epicenter, target_event.epicenter)
                        if time_hours <= max_t and dist <= max_d:
                            candidates_raw.append((cand, "Archivado"))

        # Determine status of chosen reference and replicas
        def _get_status(ev: Event | None) -> str:
            if ev is None:
                return "Desconocido"
            if historic is not None and hasattr(historic, "archived") and ev.id in historic.archived:
                return "Archivado"
            return "Activo"

        report = {
            "event": target_event,
            "status": "Activo" if target_is_active else "Archivado",
            "chosen_reference": (
                {"event": chosen_ref_event, "status": _get_status(chosen_ref_event)}
                if chosen_ref_event is not None else None
            ),
            "candidates": [{"event": c, "status": st} for c, st in candidates_raw],
            "referenced_by": [{"event": r, "status": _get_status(r)} for r in replicas]
        }

        return report, examined_nodes

    @staticmethod
    def costly_high_priority_events(tree: Tree, limit: int | None = None) -> tuple[list[dict[str, Any]], int]:
        """
        Query 4: Identifies high-priority events (priority = 3) whose depth in the active
        AVL tree strictly exceeds limit L. Reports node depth, limit L, and simulated
        visited nodes (depth + 1). Applies pruning by discarding left branches of nodes
        with priority < 3.
        Returns a tuple of (costly_events_info, examined_nodes_count).
        """
        examined_nodes = 0
        results: list[dict[str, Any]] = []

        if tree is None or tree.root is None:
            return results, examined_nodes

        safe_limit = limit if (limit is not None and isinstance(limit, int) and not isinstance(limit, bool) and limit >= 0) else 3

        def _traverse_high_priority(current: Node | None, depth: int) -> None:
            nonlocal examined_nodes
            if current is None:
                return

            examined_nodes += 1
            ev = current.event

            # Pruning rule according to key K = (P, M, I):
            # If current node has priority < 3, all nodes in its left subtree
            # have key < current_key, so their priority is strictly <= current.priority < 3.
            # Therefore, we safely discard the left branch!
            if ev is not None and ev.priority < 3:
                _traverse_high_priority(current.right_son, depth + 1)
                return

            # When priority == 3, evaluate current node for costly access
            if ev is not None and ev.priority == 3 and depth > safe_limit:
                results.append({
                    "event": ev,
                    "depth": depth,
                    "limit": safe_limit,
                    "visited_nodes": depth + 1
                })

            # Explore both left and right subtrees within priority 3
            _traverse_high_priority(current.left_son, depth + 1)
            _traverse_high_priority(current.right_son, depth + 1)

        _traverse_high_priority(tree.root, 0)
        return results, examined_nodes