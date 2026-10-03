import unittest
import sys
import os
from datetime import datetime

# Ensure project root and Models are in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'Models')
if MODELS_DIR not in sys.path:
    sys.path.insert(0, MODELS_DIR)

from Models.event import Event
from Models.node import Node


class TestNode(unittest.TestCase):
    """Unit tests for the Node AVL tree wrapper model."""

    def setUp(self):
        """Create sample events and nodes."""
        dt = datetime(2026, 1, 1)
        self.event_low = Event(id=1, priority=1, magnitude=4.0, depth=10.0, epicenter=(0.0, 0.0), date_time=dt, review=0)
        self.event_mid = Event(id=2, priority=2, magnitude=5.0, depth=10.0, epicenter=(0.0, 0.0), date_time=dt, review=0)
        self.event_high = Event(id=3, priority=3, magnitude=7.0, depth=10.0, epicenter=(0.0, 0.0), date_time=dt, review=0)

        self.node_low = Node(id=1, event=self.event_low)
        self.node_mid = Node(id=2, event=self.event_mid)
        self.node_high = Node(id=3, event=self.event_high)

    def test_init_and_leaf_state(self):
        """Node initializes as a leaf with height 0 and no children."""
        self.assertEqual(self.node_low.id, 1)
        self.assertTrue(self.node_low.is_leaf())
        self.assertEqual(self.node_low.height, 0)
        self.assertIsNone(self.node_low.left_son)
        self.assertIsNone(self.node_low.right_son)
        self.assertIsNone(self.node_low.father)

    def test_height_update_and_balance_factor(self):
        """update_height and balance_factor calculate correctly according to AVL specs."""
        # Initial leaf: height 0, balance factor 0 ((-1) - (-1))
        self.assertEqual(self.node_mid.balance_factor(), 0)

        # Attach left child
        self.node_mid.left_son = self.node_low
        self.node_low.father = self.node_mid
        self.node_mid.update_height()

        self.assertFalse(self.node_mid.is_leaf())
        self.assertEqual(self.node_mid.height, 1)
        # Left child height is 0, right child is None (-1) -> BF = 0 - (-1) = 1
        self.assertEqual(self.node_mid.balance_factor(), 1)

        # Attach right child
        self.node_mid.right_son = self.node_high
        self.node_high.father = self.node_mid
        self.node_mid.update_height()

        # Both children height 0 -> BF = 0 - 0 = 0
        self.assertEqual(self.node_mid.height, 1)
        self.assertEqual(self.node_mid.balance_factor(), 0)

    def test_node_comparisons_by_key(self):
        """Nodes must compare strictly by their key tuple (priority, magnitude, id)."""
        self.assertTrue(self.node_low < self.node_mid)
        self.assertTrue(self.node_mid < self.node_high)
        self.assertTrue(self.node_high > self.node_low)
        self.assertFalse(self.node_low == self.node_high)

        # Equal key nodes
        another_low = Node(id=1, event=self.event_low)
        self.assertTrue(self.node_low == another_low)
        self.assertFalse(self.node_low == "not_a_node")


if __name__ == '__main__':
    unittest.main()
