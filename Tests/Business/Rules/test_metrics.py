import unittest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'Models')
if MODELS_DIR not in sys.path:
    sys.path.insert(0, MODELS_DIR)

from Business.Rules.metrics import Metrics
from Models.event import Event
from Models.node import Node


class TestMetrics(unittest.TestCase):
    """Unit tests for the Metrics business logic and rotation counters."""

    def setUp(self):
        """Initialize fresh Metrics instance and sample nodes."""
        self.metrics = Metrics()
        self.dt = datetime(2026, 1, 1, 12, 0, 0)

        # Helper to create a node with specific event attributes
        self.event_p1_pending = Event(
            id=1, priority=1, magnitude=4.0, depth=10.0,
            epicenter=(0.0, 0.0), date_time=self.dt, review=0,
            attention_state="Pending"
        )
        self.event_p2_reviewed = Event(
            id=2, priority=2, magnitude=5.5, depth=20.0,
            epicenter=(1.0, 1.0), date_time=self.dt, review=1,
            attention_state="Reviewed"
        )
        self.event_p3_pendiente = Event(
            id=3, priority=3, magnitude=7.2, depth=30.0,
            epicenter=(2.0, 2.0), date_time=self.dt, review=0,
            attention_state="pendiente"
        )
        self.event_p3_revisado = Event(
            id=4, priority=3, magnitude=6.0, depth=15.0,
            epicenter=(3.0, 3.0), date_time=self.dt, review=1,
            attention_state="revisado"
        )

        self.node1 = Node(id=1, event=self.event_p1_pending)
        self.node2 = Node(id=2, event=self.event_p2_reviewed)
        self.node3 = Node(id=3, event=self.event_p3_pendiente)
        self.node4 = Node(id=4, event=self.event_p3_revisado)

    def test_initial_values(self):
        """All initial metrics counters should default to zero."""
        self.assertEqual(self.metrics.corrections_accepted, 0)
        self.assertEqual(self.metrics.discarded_reports, 0)
        self.assertEqual(self.metrics.conflicts, 0)
        self.assertEqual(self.metrics.active_events, 0)
        self.assertEqual(self.metrics.removed_events, 0)
        self.assertEqual(self.metrics.archived_events, 0)
        self.assertEqual(self.metrics.cases, {"LL": 0, "RR": 0, "LR": 0, "RL": 0})
        self.assertEqual(self.metrics.turns, {"left": 0, "right": 0})

    def test_counter_getters_and_setters(self):
        """Counters should update when set with valid non-negative integers."""
        self.metrics.corrections_accepted = 5
        self.assertEqual(self.metrics.corrections_accepted, 5)

        self.metrics.discarded_reports = 3
        self.assertEqual(self.metrics.discarded_reports, 3)

        self.metrics.conflicts = 2
        self.assertEqual(self.metrics.conflicts, 2)

        self.metrics.active_events = 10
        self.assertEqual(self.metrics.active_events, 10)

        self.metrics.removed_events = 4
        self.assertEqual(self.metrics.removed_events, 4)

        self.metrics.archived_events = 7
        self.assertEqual(self.metrics.archived_events, 7)

    def test_counter_setter_invalid_values_raise_value_error(self):
        """Negative values or non-integers should raise ValueError."""
        with self.assertRaises(ValueError):
            self.metrics.corrections_accepted = -1
        with self.assertRaises(ValueError):
            self.metrics.discarded_reports = "ten"
        with self.assertRaises(ValueError):
            self.metrics.conflicts = -5
        with self.assertRaises(ValueError):
            self.metrics.active_events = -1
        with self.assertRaises(ValueError):
            self.metrics.removed_events = None
        with self.assertRaises(ValueError):
            self.metrics.archived_events = -2

    def test_register_case(self):
        """Registering rotation cases should increment the corresponding counter."""
        self.metrics.register_case("LL")
        self.metrics.register_case("LL")
        self.metrics.register_case("LR")
        self.metrics.register_case("UNKNOWN")  # Should be safely ignored

        expected_cases = {"LL": 2, "RR": 0, "LR": 1, "RL": 0}
        self.assertEqual(self.metrics.cases, expected_cases)

    def test_register_turn(self):
        """Registering elementary turns should increment the corresponding counter."""
        self.metrics.register_turn("left")
        self.metrics.register_turn("left")
        self.metrics.register_turn("right")
        self.metrics.register_turn("up")  # Should be safely ignored

        expected_turns = {"left": 2, "right": 1}
        self.assertEqual(self.metrics.turns, expected_turns)

    def test_cases_and_turns_return_copies(self):
        """Modifying the dictionary returned by cases or turns should not mutate internal state."""
        cases_copy = self.metrics.cases
        cases_copy["LL"] = 999
        self.assertEqual(self.metrics.cases["LL"], 0)

        turns_copy = self.metrics.turns
        turns_copy["left"] = 999
        self.assertEqual(self.metrics.turns["left"], 0)

    def test_pending_events_calculation(self):
        """pending_events should count nodes with pending/pendiente attention state."""
        nodes = [self.node1, self.node2, self.node3, self.node4]
        # node1 is "Pending", node3 is "pending" -> 2
        self.assertEqual(self.metrics.pending_events(nodes), 2)
        self.assertEqual(self.metrics.pending_events([]), 0)

    def test_reviewed_events_calculation(self):
        """reviewed_events should count nodes with reviewed/revisado attention state."""
        nodes = [self.node1, self.node2, self.node3, self.node4]
        # node2 is "Reviewed", node4 is "reviewed" -> 2
        self.assertEqual(self.metrics.reviewed_events(nodes), 2)
        self.assertEqual(self.metrics.reviewed_events([]), 0)

    def test_events_by_priority(self):
        """events_by_priority should return correct counts grouped by priority."""
        nodes = [self.node1, self.node2, self.node3, self.node4]
        # node1: p1, node2: p2, node3: p3, node4: p3
        expected = {1: 1, 2: 1, 3: 2}
        self.assertEqual(self.metrics.events_by_priority(nodes), expected)
        self.assertEqual(self.metrics.events_by_priority([]), {1: 0, 2: 0, 3: 0})

    def test_cant_leaves(self):
        """cant_leaves should count only nodes that are leaves (no children)."""
        # node1 and node2 have no children -> leaves
        # make node3 parent of node4
        self.node3.left_son = self.node4
        self.node4.father = self.node3

        nodes = [self.node1, self.node2, self.node3, self.node4]
        # node1 is leaf, node2 is leaf, node3 has left child (not leaf), node4 is leaf -> 3 leaves
        self.assertEqual(self.metrics.cant_leaves(nodes), 3)
        self.assertEqual(self.metrics.cant_leaves([]), 0)


if __name__ == '__main__':
    unittest.main()
