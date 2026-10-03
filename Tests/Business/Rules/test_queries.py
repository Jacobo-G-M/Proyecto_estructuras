import unittest
import sys
import os
from datetime import datetime, timedelta

# Ensure project root and Models are in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'Models')
if MODELS_DIR not in sys.path:
    sys.path.insert(0, MODELS_DIR)

from Business.Rules.queries import Queries
from Business.Rules.asociation import Association
from Business.historic import Historic
from Business.Structures.avl import AVL
from Models.event import Event
from Models.node import Node


class TestQueries(unittest.TestCase):
    """Unit tests for the Section 11 query algorithms in Queries class."""

    def setUp(self):
        """Create sample events and an AVL tree for query testing."""
        self.tree = AVL(id=1)
        self.base_time = datetime(2026, 3, 10, 12, 0, 0)

        # Create events with distinct keys K = (P, M, I)
        # Priority 1 events
        self.ev1 = Event(
            id=1, priority=1, magnitude=3.0, depth=10.0,
            epicenter=(0.0, 0.0), date_time=self.base_time, review=0,
            attention_state="Pending"
        )
        self.ev2 = Event(
            id=2, priority=1, magnitude=4.0, depth=12.0,
            epicenter=(0.1, 0.1), date_time=self.base_time + timedelta(hours=1), review=0,
            attention_state="Reviewed"
        )

        # Priority 2 events
        self.ev3 = Event(
            id=3, priority=2, magnitude=5.0, depth=15.0,
            epicenter=(0.2, 0.2), date_time=self.base_time + timedelta(hours=2), review=0,
            attention_state="Pending"
        )
        self.ev4 = Event(
            id=4, priority=2, magnitude=5.8, depth=20.0,
            epicenter=(0.3, 0.3), date_time=self.base_time + timedelta(hours=3), review=0,
            attention_state="Pending"
        )

        # Priority 3 events (highest priority)
        self.ev5 = Event(
            id=5, priority=3, magnitude=6.5, depth=25.0,
            epicenter=(0.4, 0.4), date_time=self.base_time + timedelta(hours=4), review=0,
            attention_state="Pending"
        )
        self.ev6 = Event(
            id=6, priority=3, magnitude=7.2, depth=30.0,
            epicenter=(0.5, 0.5), date_time=self.base_time + timedelta(hours=5), review=0,
            attention_state="Pending"
        )

        for ev in [self.ev1, self.ev2, self.ev3, self.ev4, self.ev5, self.ev6]:
            self.tree.insert(Node(id=ev.id, event=ev))

    # =========================================================================
    # TESTS PARA CONSULTA 1: Top k pendientes en orden descendente de K
    # =========================================================================

    def test_top_k_pending_descending_order(self):
        """Top k pending must return events in descending order of key K."""
        # Pending events in descending order of K: ev6 (3, 7.2), ev5 (3, 6.5), ev4 (2, 5.8), ev3 (2, 5.0), ev1 (1, 3.0)
        # Note: ev2 is 'Reviewed', so it must be omitted
        results, examined = Queries.top_k_pending(self.tree, k=3)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].id, self.ev6.id)
        self.assertEqual(results[1].id, self.ev5.id)
        self.assertEqual(results[2].id, self.ev4.id)
        self.assertGreater(examined, 0)
        # Pruning check: it should not have examined all nodes in the tree
        self.assertLess(examined, 6)

    def test_top_k_pending_k_larger_than_available(self):
        """When k exceeds the number of pending events, return all available."""
        results, examined = Queries.top_k_pending(self.tree, k=100)
        # Total pending events = 5 (ev1, ev3, ev4, ev5, ev6)
        self.assertEqual(len(results), 5)
        self.assertEqual(examined, 6)

    def test_top_k_pending_empty_tree_or_invalid_k(self):
        """Empty tree or non-positive k should return an empty list and 0 examined."""
        empty_tree = AVL(id=99)
        results, examined = Queries.top_k_pending(empty_tree, k=5)
        self.assertEqual(results, [])
        self.assertEqual(examined, 0)

        results_zero_k, examined_zero = Queries.top_k_pending(self.tree, k=0)
        self.assertEqual(results_zero_k, [])
        self.assertEqual(examined_zero, 0)

    # =========================================================================
    # TESTS PARA CONSULTA 2: Filtro por magnitud, profundidad y fechas
    # =========================================================================

    def test_events_by_filters_matching(self):
        """Finds events matching magnitude in [5.0, 7.0], depth <= 25.0, within date range."""
        results, examined = Queries.events_by_filters(
            tree=self.tree,
            min_magnitude=5.0,
            max_magnitude=7.0,
            max_depth=25.0,
            start_date=self.base_time,
            end_date=self.base_time + timedelta(hours=10)
        )

        # Expected matches: ev3 (mag 5.0, depth 15), ev4 (mag 5.8, depth 20), ev5 (mag 6.5, depth 25)
        # ev6 has mag 7.2 (exceeds max 7.0) and depth 30 (exceeds max 25)
        matching_ids = {ev.id for ev in results}
        self.assertEqual(matching_ids, {3, 4, 5})
        self.assertGreater(examined, 0)

    def test_events_by_filters_empty_tree(self):
        """Querying an empty tree should return empty results and 0 examined."""
        empty_tree = AVL(id=99)
        results, examined = Queries.events_by_filters(
            empty_tree, 4.0, 8.0, 50.0, self.base_time, self.base_time + timedelta(days=1)
        )
        self.assertEqual(results, [])
        self.assertEqual(examined, 0)

    # =========================================================================
    # TESTS PARA CONSULTA 3: Candidatos y referencia elegida
    # =========================================================================

    def test_event_associations_active_and_archived(self):
        """Query 3 resolves chosen reference, candidates, and replicas across active and historic."""
        historic = Historic()
        # Create an earlier, larger event archived in historic
        archived_ref = Event(
            id=100, priority=3, magnitude=8.0, depth=15.0,
            epicenter=(0.0, 0.0), date_time=self.base_time - timedelta(hours=5), review=1
        )
        historic.archive_event(archived_ref)

        # Create an association where archived_ref is chosen reference of ev1, and ev1 has ev2 as replica
        assoc = Association(assoc_id=self.ev1.id, chosen_reference=archived_ref)
        assoc.add_replica(self.ev2)

        report, examined = Queries.event_associations(
            tree=self.tree,
            historic=historic,
            associations=[assoc],
            event_id=self.ev1.id,
            max_time_hours=48.0,
            max_distance_km=100.0
        )

        self.assertIsNotNone(report)
        self.assertEqual(report["event"].id, self.ev1.id)
        self.assertEqual(report["status"], "Activo")
        self.assertIsNotNone(report["chosen_reference"])
        self.assertEqual(report["chosen_reference"]["event"].id, 100)
        self.assertEqual(report["chosen_reference"]["status"], "Archivado")
        self.assertEqual(len(report["referenced_by"]), 1)
        self.assertEqual(report["referenced_by"][0]["event"].id, self.ev2.id)
        self.assertGreater(examined, 0)

    def test_event_associations_non_existent_event(self):
        """Query 3 for a non-existent event ID returns an empty dict."""
        historic = Historic()
        report, examined = Queries.event_associations(
            tree=self.tree,
            historic=historic,
            associations=[],
            event_id=9999
        )
        self.assertEqual(report, {})

    # =========================================================================
    # TESTS PARA CONSULTA 4: Eventos de prioridad alta con acceso costoso
    # =========================================================================

    def test_costly_high_priority_events_identification(self):
        """Identifies priority 3 events whose tree depth strictly exceeds limit L."""
        # In our tree: ev5 and ev6 have priority 3.
        # Set limit L = 0 so that any priority 3 node with depth > 0 is flagged as costly
        results, examined = Queries.costly_high_priority_events(self.tree, limit=0)

        self.assertGreater(len(results), 0)
        for item in results:
            self.assertEqual(item["event"].priority, 3)
            self.assertGreater(item["depth"], item["limit"])
            self.assertEqual(item["visited_nodes"], item["depth"] + 1)
        self.assertGreater(examined, 0)

    def test_costly_high_priority_events_empty_tree(self):
        """Empty tree returns empty results and 0 examined."""
        empty_tree = AVL(id=99)
        results, examined = Queries.costly_high_priority_events(empty_tree, limit=1)
        self.assertEqual(results, [])
        self.assertEqual(examined, 0)

    def test_top_k_pending_none_or_negative_k(self):
        """None or negative k returns empty list safely without TypeError."""
        res_none, ex_none = Queries.top_k_pending(self.tree, k=None)
        self.assertEqual(res_none, [])
        self.assertEqual(ex_none, 0)

        res_neg, ex_neg = Queries.top_k_pending(self.tree, k=-3)
        self.assertEqual(res_neg, [])
        self.assertEqual(ex_neg, 0)

    def test_events_by_filters_omitted_or_none_arguments(self):
        """Default or None filter arguments return valid matches without TypeError."""
        results_min, _ = Queries.events_by_filters(self.tree, min_magnitude=6.0)
        self.assertEqual({ev.id for ev in results_min}, {5, 6})

        results_all, _ = Queries.events_by_filters(self.tree)
        self.assertEqual(len(results_all), 6)

        results_inv, ex_inv = Queries.events_by_filters(self.tree, min_magnitude=7.0, max_magnitude=3.0)
        self.assertEqual(results_inv, [])
        self.assertEqual(ex_inv, 0)

    def test_event_associations_replica_lookup(self):
        """Querying an event registered as replica inside referenced_by resolves its chosen reference."""
        assoc = Association(assoc_id=10, chosen_reference=self.ev6)
        assoc.add_replica(self.ev1)

        report, examined = Queries.event_associations(
            tree=self.tree,
            historic=None,
            associations=[assoc],
            event_id=self.ev1.id,
            max_time_hours=48.0,
            max_distance_km=50.0
        )
        self.assertIsNotNone(report.get("chosen_reference"))
        self.assertEqual(report["chosen_reference"]["event"].id, self.ev6.id)
        self.assertEqual(report["chosen_reference"]["status"], "Activo")

    def test_event_associations_none_thresholds(self):
        """Passing None for max_time_hours and max_distance_km uses safe defaults."""
        report, _ = Queries.event_associations(
            tree=self.tree,
            historic=None,
            associations=[],
            event_id=self.ev1.id,
            max_time_hours=None,
            max_distance_km=None
        )
        self.assertEqual(report["event"].id, self.ev1.id)

    def test_costly_high_priority_events_limit_none(self):
        """Passing limit=None defaults safely to limit 3 without crashing."""
        results, examined = Queries.costly_high_priority_events(self.tree, limit=None)
        self.assertIsInstance(results, list)
        self.assertGreater(examined, 0)


if __name__ == '__main__':
    unittest.main()

