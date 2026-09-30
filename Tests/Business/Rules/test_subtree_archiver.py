import unittest
import sys
import os
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'Models')
if MODELS_DIR not in sys.path:
    sys.path.insert(0, MODELS_DIR)

from Business.Rules.sub_tree_archiver import SubtreeArchiver
from Business.Structures.avl import AVL
from Models.event import Event
from Models.node import Node


class TestSubtreeArchiver(unittest.TestCase):

    def setUp(self):
        self.clock = datetime(2026, 3, 15, 12, 0, 0)
        self.old_time = self.clock - timedelta(hours=10)   # 10 hours old
        self.recent_time = self.clock - timedelta(hours=2) # 2 hours old

    def test_is_eligible_branch_all_low_priority_and_old_enough(self):
        """Branch is eligible when all nodes have priority 1 and age > max_age_hours."""
        e1 = Event(id=1, priority=1, magnitude=3.0, depth=10.0, epicenter=(0.0, 0.0), date_time=self.old_time, review=0)
        e2 = Event(id=2, priority=1, magnitude=3.5, depth=10.0, epicenter=(0.0, 0.0), date_time=self.old_time, review=0)
        nodes = [Node(id=1, event=e1), Node(id=2, event=e2)]

        # max_age_hours = 5, both are 10 hours old -> True
        self.assertTrue(SubtreeArchiver.is_eligible_branch(nodes, max_age_hours=5.0, simulation_clock=self.clock))

    def test_is_eligible_branch_rejects_high_priority_events(self):
        """Branch is ineligible if even one node has priority > 1."""
        e1 = Event(id=1, priority=1, magnitude=3.0, depth=10.0, epicenter=(0.0, 0.0), date_time=self.old_time, review=0)
        e2 = Event(id=2, priority=2, magnitude=5.0, depth=10.0, epicenter=(0.0, 0.0), date_time=self.old_time, review=0)
        nodes = [Node(id=1, event=e1), Node(id=2, event=e2)]

        self.assertFalse(SubtreeArchiver.is_eligible_branch(nodes, max_age_hours=5.0, simulation_clock=self.clock))

    def test_is_eligible_branch_rejects_recent_events(self):
        """Branch is ineligible if any event is younger than or equal to max_age_hours."""
        e1 = Event(id=1, priority=1, magnitude=3.0, depth=10.0, epicenter=(0.0, 0.0), date_time=self.old_time, review=0)
        e2 = Event(id=2, priority=1, magnitude=3.2, depth=10.0, epicenter=(0.0, 0.0), date_time=self.recent_time, review=0)
        nodes = [Node(id=1, event=e1), Node(id=2, event=e2)]

        # max_age_hours = 5, e2 is only 2 hours old -> False
        self.assertFalse(SubtreeArchiver.is_eligible_branch(nodes, max_age_hours=5.0, simulation_clock=self.clock))

    def test_is_eligible_branch_empty_list_returns_false(self):
        """An empty list of nodes cannot form an eligible branch."""
        self.assertFalse(SubtreeArchiver.is_eligible_branch([], max_age_hours=5.0, simulation_clock=self.clock))

    def test_find_best_branch_on_empty_tree(self):
        """Querying an empty tree should return (None, [])."""
        tree = AVL(id=1)
        root, nodes = SubtreeArchiver.find_best_branch(tree, max_age_hours=5.0, simulation_clock=self.clock)
        self.assertIsNone(root)
        self.assertEqual(nodes, [])

    def test_find_best_branch_selects_highest_score(self):
        """Branch selection prioritizes node count, then depth, then root ID."""
        tree = AVL(id=1)

        # Create two priority 1 old events
        e1 = Event(id=10, priority=1, magnitude=2.0, depth=10.0, epicenter=(0.0, 0.0), date_time=self.old_time, review=0)
        e2 = Event(id=20, priority=1, magnitude=3.0, depth=10.0, epicenter=(0.0, 0.0), date_time=self.old_time, review=0)

        tree.insert(Node(id=10, event=e1))
        tree.insert(Node(id=20, event=e2))

        best_root, best_nodes = SubtreeArchiver.find_best_branch(tree, max_age_hours=5.0, simulation_clock=self.clock)
        self.assertIsNotNone(best_root)
        # Root of the tree contains both nodes (size 2), making it the highest scoring eligible branch
        self.assertEqual(len(best_nodes), 2)


if __name__ == '__main__':
    unittest.main()
