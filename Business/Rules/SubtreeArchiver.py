from __future__ import annotations
from datetime import datetime
try:
    from Business.Structures.tree import Tree
    from Models.node import Node
except ImportError:
    try:
        from Structures.tree import Tree
        from ...Models.node import Node
    except ImportError:
        from tree import Tree
        from node import Node

class SubtreeArchiver:
    """
    Domain rule and service class responsible for evaluating, selecting,
    and retrieving eligible subtrees for mass archiving according to Section 10.
    """

    @staticmethod
    def is_eligible_branch(subtree_nodes: list[Node], max_age_hours: float, simulation_clock: datetime) -> bool:
        """
        A branch is eligible if and only if ALL of its events have priority 1 (low)
        and an age strictly greater than max_age_hours (T).
        """
        if not subtree_nodes:
            return False

        for node in subtree_nodes:
            event = getattr(node, 'event', None)
            if event is None:
                return False

            # All events must have priority 1 (low)
            if event.priority != 1:
                return False

            # Age is measured between simulation clock and occurrence time
            age_timedelta = simulation_clock - event.date_time
            age_in_hours = age_timedelta.total_seconds() / 3600.0

            if age_in_hours <= max_age_hours:
                return False

        return True

    @classmethod
    def find_best_branch(
        cls,
        tree: Tree,
        max_age_hours: float,
        simulation_clock: datetime
    ) -> tuple[Node | None, list[Node]]:
        """
        Traverses the tree to find the eligible branch with the highest score.
        Tie-breaking rules according to Section 10:
        1. Greatest node count.
        2. Greatest root depth in the tree.
        3. Highest numeric ID of its root node.
        """
        if tree is None or tree.root is None:
            return None, []

        all_nodes_with_depth = tree.get_all_nodes_with_depth()

        best_root: Node | None = None
        best_nodes_list: list[Node] = []
        best_score = (0, -1, -1)  # (node_count, root_depth, root_id)

        for current_node, depth in all_nodes_with_depth:
            subtree_nodes = tree.preorder(current_node)

            if cls.is_eligible_branch(subtree_nodes, max_age_hours, simulation_clock):
                current_score = (len(subtree_nodes), depth, current_node.id)

                if current_score > best_score:
                    best_score = current_score
                    best_root = current_node
                    best_nodes_list = subtree_nodes

        return best_root, best_nodes_list
