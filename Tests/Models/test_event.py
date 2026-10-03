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
from Models.station import Station


class TestEvent(unittest.TestCase):
    """Unit tests for the Event domain model."""

    def setUp(self):
        """Create sample event for testing."""
        self.dt = datetime(2026, 3, 1, 14, 0)
        self.event = Event(
            id=10,
            priority=2,
            magnitude=6.2,
            depth=25.0,
            epicenter=(-72.5, 6.1),
            date_time=self.dt,
            review=1,
            attention_state="Pending",
            status="Active"
        )

    def test_init_and_properties(self):
        """Event attributes should match initialization arguments."""
        self.assertEqual(self.event.id, 10)
        self.assertEqual(self.event.priority, 2)
        self.assertEqual(self.event.magnitude, 6.2)
        self.assertEqual(self.event.depth, 25.0)
        self.assertEqual(self.event.epicenter, (-72.5, 6.1))
        self.assertEqual(self.event.date_time, self.dt)
        self.assertEqual(self.event.review, 1)
        self.assertEqual(self.event.attention_state, "Pending")
        self.assertEqual(self.event.status, "Active")

    def test_get_key(self):
        """Event key K must equal (priority, magnitude, id) as specified in Section 8."""
        key = self.event.get_key()
        self.assertEqual(key, (2, 6.2, 10))

    def test_add_origin_station(self):
        """Adding origin station should register in origin_stations and avoid duplicates."""
        station = Station(id=301, name="Station Gamma", coords=(-72.5, 6.1))
        self.event.add_origin_station(station)
        self.assertEqual(len(self.event.origin_stations), 1)

        # Duplicate addition should be ignored
        self.event.add_origin_station(station)
        self.assertEqual(len(self.event.origin_stations), 1)

    def test_origin_stations_setter_validation(self):
        """origin_stations setter must enforce list type."""
        self.event.origin_stations = []
        self.assertEqual(self.event.origin_stations, [])

        with self.assertRaises(TypeError):
            self.event.origin_stations = "not_a_list"


if __name__ == '__main__':
    unittest.main()
