import unittest
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'Models')
if MODELS_DIR not in sys.path:
    sys.path.insert(0, MODELS_DIR)

from Business.historic import Historic
from Models.event import Event


class TestHistoric(unittest.TestCase):
    """Unit tests for the Historic event archive and deletion storage."""

    def setUp(self):
        """Create sample events and a fresh Historic manager."""
        self.historic = Historic()
        dt = datetime(2026, 1, 1, 10, 0)
        self.event1 = Event(id=1, priority=2, magnitude=5.0, depth=10.0, epicenter=(0.0, 0.0), date_time=dt, review=0)
        self.event2 = Event(id=2, priority=3, magnitude=6.5, depth=15.0, epicenter=(1.0, 1.0), date_time=dt, review=1)

    def test_initial_state(self):
        """Historic should start with empty archived and deleted registries."""
        self.assertEqual(self.historic.archived, {})
        self.assertEqual(self.historic.deleted, {})

    def test_archive_event(self):
        """Archiving an event should mark its status as Archived and store it."""
        self.historic.archive_event(self.event1)
        self.assertEqual(self.event1.status, "Archived")
        self.assertIn(1, self.historic.archived)
        self.assertEqual(self.historic.archived[1].id, 1)

    def test_archive_invalid_type_raises_type_error(self):
        """Archiving an object that is not an Event must raise TypeError."""
        with self.assertRaises(TypeError):
            self.historic.archive_event("not_an_event")

    def test_delete_event(self):
        """Deleting an event should mark its status as Deleted and store it."""
        self.historic.delete_event(self.event2)
        self.assertEqual(self.event2.status, "Deleted")
        self.assertIn(2, self.historic.deleted)
        self.assertEqual(self.historic.deleted[2].id, 2)

    def test_delete_invalid_type_raises_type_error(self):
        """Deleting an object that is not an Event must raise TypeError."""
        with self.assertRaises(TypeError):
            self.historic.delete_event(12345)

    def test_unarchive_event(self):
        """Unarchiving an existing event should reactivate and remove it from archived."""
        self.historic.archive_event(self.event1)
        restored = self.historic.unarchive_event(1)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.status, "Active")
        self.assertNotIn(1, self.historic.archived)

        # Unarchiving a non-existent ID should return None
        self.assertIsNone(self.historic.unarchive_event(999))

    def test_undelete_event(self):
        """Undeleting an existing event should reactivate and remove it from deleted."""
        self.historic.delete_event(self.event2)
        restored = self.historic.undelete_event(2)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.status, "Active")
        self.assertNotIn(2, self.historic.deleted)

        # Undeleting a non-existent ID should return None
        self.assertIsNone(self.historic.undelete_event(999))

    def test_archived_and_deleted_setters(self):
        """Property setters should validate that values are dictionaries."""
        self.historic.archived = {1: self.event1}
        self.assertEqual(len(self.historic.archived), 1)

        with self.assertRaises(TypeError):
            self.historic.archived = ["not", "a", "dict"]

        with self.assertRaises(TypeError):
            self.historic.deleted = "not_a_dict"


if __name__ == '__main__':
    unittest.main()
