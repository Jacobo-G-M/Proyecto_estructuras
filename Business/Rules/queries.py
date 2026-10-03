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
        Query 1: Retrieves the top k pending events in descending order of key K = (P, M, I).
        
        Algorithm:
        - Traverses the AVL tree using reverse in-order traversal (Right -> Root -> Left).
        - Since BST ordering satisfies K(left) < K(root) < K(right), exploring the right
          subtree first guarantees strictly descending key order.
        - Applies early termination pruning: once k matching pending events are collected,
          all remaining traversal branches are immediately aborted.
        
        Returns:
            A tuple of (matching_events_list, examined_nodes_count).
        """
        # Counter to track how many nodes were physically visited during traversal
        examined_nodes = 0
        # Output list holding the matching pending events in descending order
        results: list[Event] = []

        # Defensive guard: return empty result if the tree is empty or k is non-positive / invalid.
        # Notice: in Python, bool subclasses int (isinstance(True, int) is True),
        # so we explicitly verify that k is an integer and not a boolean.
        if tree is None or tree.root is None or k is None or not isinstance(k, int) or isinstance(k, bool) or k <= 0:
            return results, examined_nodes

        def _reverse_inorder(current: Node | None) -> None:
            nonlocal examined_nodes
            # Base case: empty subtree or quota k has already been reached
            if current is None or len(results) >= k:
                return

            # Step 1: Traverse right subtree first (contains strictly greater K keys)
            _reverse_inorder(current.right_son)

            # Early pruning check: avoid inspecting current node if quota was satisfied in right branch
            if len(results) >= k:
                return

            # Step 2: Inspect current node
            examined_nodes += 1
            if current.event is not None:
                # Normalize state string to handle case sensitivity and localization
                attention = str(current.event.attention_state).strip().lower()
                if attention in ("pending", "pendiente"):
                    results.append(current.event)

            # Early pruning check: avoid traversing left subtree if quota is now met
            if len(results) >= k:
                return

            # Step 3: Traverse left subtree (contains strictly smaller K keys)
            _reverse_inorder(current.left_son)

        # Initiate traversal from root
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
        Query 2: Multi-criteria filtering by magnitude range, maximum depth, and date range.
        
        Algorithm:
        - Recursively visits tree nodes while testing all criteria against the event.
        - Applies mathematical branch pruning based on the composite key K = (Priority, Magnitude, ID):
          * When current node has priority 3 (maximum possible priority in system) and its
            magnitude exceeds max_magnitude: any node in its right subtree must have priority 3
            and magnitude >= current.magnitude > max_magnitude. Thus, the entire right branch
            cannot contain any matching event and is safely pruned.
          * When current node has priority 1 (minimum possible priority in system) and its
            magnitude is below min_magnitude: any node in its left subtree must have priority 1
            and magnitude <= current.magnitude < min_magnitude. Thus, the entire left branch
            cannot contain any matching event and is safely pruned.
        
        Returns:
            A tuple of (matching_events_list, examined_nodes_count).
        """
        # Counter for total tree nodes evaluated
        examined_nodes = 0
        # Collector for events satisfying all active criteria
        results: list[Event] = []

        # Return immediately if tree has no root
        if tree is None or tree.root is None:
            return results, examined_nodes

        # Fallback to safe infinite/extreme bounds when parameters are omitted (None)
        # This prevents TypeError comparisons while preserving unconstrained filtering
        min_mag = float(min_magnitude) if min_magnitude is not None else -float('inf')
        max_mag = float(max_magnitude) if max_magnitude is not None else float('inf')
        max_d = float(max_depth) if max_depth is not None else float('inf')
        start_dt = start_date if start_date is not None else datetime.min
        end_dt = end_date if end_date is not None else datetime.max

        # Contradictory range pruning: if min > max, no event can possibly match
        if min_mag > max_mag or start_dt > end_dt:
            return results, examined_nodes

        def _filter_helper(current: Node | None) -> None:
            nonlocal examined_nodes
            # Base case: reached empty leaf slot
            if current is None:
                return

            # Count current node visit
            examined_nodes += 1
            ev = current.event

            if ev is not None:
                # Evaluate whether the current event satisfies all 3 filter dimensions
                mag_ok = min_mag <= ev.magnitude <= max_mag
                depth_ok = ev.depth <= max_d
                date_ok = start_dt <= ev.date_time <= end_dt

                # Collect if all criteria are satisfied
                if mag_ok and depth_ok and date_ok:
                    results.append(ev)

                # Pruning Rule 1 (Right Subtree):
                # If priority is 3 and magnitude exceeds max_mag, right subtree has keys > K(current),
                # so all right descendants have priority 3 and magnitude >= ev.magnitude > max_mag.
                prune_right = (ev.priority == 3 and max_magnitude is not None and ev.magnitude > max_mag)

                # Pruning Rule 2 (Left Subtree):
                # If priority is 1 and magnitude is below min_mag, left subtree has keys < K(current),
                # so all left descendants have priority 1 and magnitude <= ev.magnitude < min_mag.
                prune_left = (ev.priority == 1 and min_magnitude is not None and ev.magnitude < min_mag)

                # Recursively explore left child if not pruned
                if not prune_left:
                    _filter_helper(current.left_son)

                # Recursively explore right child if not pruned
                if not prune_right:
                    _filter_helper(current.right_son)
            else:
                # If node has no event payload, safely traverse both child branches
                _filter_helper(current.left_son)
                _filter_helper(current.right_son)

        # Start traversal from root
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
        Query 3: Resolves candidate references, chosen reference, and replicas for an event.
        
        Algorithm:
        1. Searches for target event in active AVL tree (recording examined nodes).
           If not found, searches in historic archived catalog.
        2. Resolves association relationships:
           - If target is a replica inside an association (in referenced_by), identifies its chosen reference.
           - If target is the chosen reference (parent) of an association, identifies all replicas using it.
        3. Scans for candidate reference events in both active tree and archived catalog:
           - Candidates must have strictly higher magnitude than target.
           - Candidates must have strictly earlier timestamp than target.
           - Time elapsed between candidate and target must be <= max_time_hours.
           - Spatial Euclidean distance between epicenters must be <= max_distance_km.
        
        Returns:
            A tuple of (report_dictionary, examined_nodes_count).
        """
        examined_nodes = 0
        target_event: Event | None = None
        target_is_active = False

        # Apply safe operational defaults if parameters are omitted
        max_t = float(max_time_hours) if max_time_hours is not None else 48.0
        max_d = float(max_distance_km) if max_distance_km is not None else 40.0

        # Helper: computes 2D Euclidean distance between coordinates (x, y)
        def _calc_dist(p1: tuple[float, float], p2: tuple[float, float]) -> float:
            return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

        # Step 1A: Search for target event in the active tree
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

                # Explore left and then right subtrees
                _find_target(current.left_son)
                if target_event is None:
                    _find_target(current.right_son)

            _find_target(tree.root)

        # Step 1B: If not found in active tree, search in historic archived catalog
        if target_event is None and historic is not None and hasattr(historic, "archived"):
            if event_id in historic.archived:
                target_event = historic.archived[event_id]
                target_is_active = False

        # If target event does not exist in any catalog, return an empty dictionary
        if target_event is None:
            return {}, examined_nodes

        # Step 2: Resolve chosen reference and replica associations
        chosen_ref_event: Event | None = None
        replicas: list[Event] = []

        if associations:
            for assoc in associations:
                # Case 2A: Target is the chosen reference (parent) of this association cluster
                if assoc.chosen_reference is not None and getattr(assoc.chosen_reference, "id", None) == event_id:
                    # Collect all replica events attached to this reference event
                    for rep in assoc.referenced_by:
                        if rep is not None and rep not in replicas and getattr(rep, "id", None) != event_id:
                            replicas.append(rep)

                # Case 2B: Target is a child replica registered in referenced_by
                is_replica = any(
                    getattr(rep, "id", None) == event_id
                    for rep in assoc.referenced_by
                    if rep is not None
                )
                if is_replica:
                    # Its chosen parent reference is the association's chosen_reference
                    if chosen_ref_event is None and assoc.chosen_reference is not None:
                        chosen_ref_event = assoc.chosen_reference

        # Step 3: Discover candidate reference events meeting spatiotemporal constraints
        candidates_raw: list[tuple[Event, str]] = []

        # Step 3A: Search candidates within the active tree
        if tree is not None and tree.root is not None:
            def _search_candidates(current: Node | None) -> None:
                nonlocal examined_nodes
                if current is None:
                    return

                examined_nodes += 1
                cand = current.event
                if cand is not None and cand.id != event_id:
                    # Must have strictly greater magnitude and occur strictly earlier
                    if cand.magnitude > target_event.magnitude and cand.date_time < target_event.date_time:
                        time_hours = (target_event.date_time - cand.date_time).total_seconds() / 3600.0
                        dist = _calc_dist(cand.epicenter, target_event.epicenter)
                        # Verify temporal window W and spatial radius R
                        if time_hours <= max_t and dist <= max_d:
                            candidates_raw.append((cand, "Activo"))

                _search_candidates(current.left_son)
                _search_candidates(current.right_son)

            _search_candidates(tree.root)

        # Step 3B: Search candidates within historic archived events
        if historic is not None and hasattr(historic, "archived"):
            for cand_id, cand in historic.archived.items():
                if cand.id != event_id:
                    if cand.magnitude > target_event.magnitude and cand.date_time < target_event.date_time:
                        time_hours = (target_event.date_time - cand.date_time).total_seconds() / 3600.0
                        dist = _calc_dist(cand.epicenter, target_event.epicenter)
                        if time_hours <= max_t and dist <= max_d:
                            candidates_raw.append((cand, "Archivado"))

        # Helper: determines whether an event is in the archived catalog or active
        def _get_status(ev: Event | None) -> str:
            if ev is None:
                return "Desconocido"
            if historic is not None and hasattr(historic, "archived") and ev.id in historic.archived:
                return "Archivado"
            return "Activo"

        # Build final report payload
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
        AVL tree strictly exceeds limit L.
        
        Algorithm:
        - Traverses the tree calculating the depth of each node (root = 0).
        - Applies branch pruning based on key ordering K = (P, M, I):
          * If a node has priority < 3, all nodes in its left subtree have keys strictly
            smaller than current_key, so their priorities are <= current.priority < 3.
            Therefore, no priority 3 node can exist in the left branch, and it is safely pruned!
        - For every node where priority == 3 and depth > limit, records:
          * The event instance.
          * The node's actual tree depth.
          * The operational limit L.
          * The simulated visited nodes count (depth + 1).
        
        Returns:
            A tuple of (costly_events_info_list, examined_nodes_count).
        """
        examined_nodes = 0
        results: list[dict[str, Any]] = []

        # Return immediately on empty tree
        if tree is None or tree.root is None:
            return results, examined_nodes

        # Fallback to default limit L = 3 if omitted, invalid, or negative
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
            # Therefore, we safely discard the left branch and only explore the right branch!
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

            # Explore both left and right subtrees within priority 3 range
            _traverse_high_priority(current.left_son, depth + 1)
            _traverse_high_priority(current.right_son, depth + 1)

        # Initiate traversal starting at root (depth 0)
        _traverse_high_priority(tree.root, 0)
        return results, examined_nodes