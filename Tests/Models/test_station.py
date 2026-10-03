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

from Models.station import Station
from Models.report import Report


class TestStation(unittest.TestCase):
    """Unit tests for the Station domain model."""

    def setUp(self):
        """Create sample station and reports for testing."""
        self.station = Station(id=101, name="Station Alpha", coords=(-74.1, 4.6))
        self.report1 = Report(
            id=1, magnitude=4.5, depth=10.0,
            epicenter=(-74.1, 4.6), date_time=datetime(2026, 1, 1),
            review=0
        )
        self.report2 = Report(
            id=2, magnitude=5.2, depth=15.0,
            epicenter=(-74.1, 4.6), date_time=datetime(2026, 1, 2),
            review=1
        )

    def test_init_and_properties(self):
        """Station should initialize and store attributes properly."""
        self.assertEqual(self.station.id, 101)
        self.assertEqual(self.station.name, "Station Alpha")
        self.assertEqual(self.station.coords, (-74.1, 4.6))
        self.assertEqual(self.station.my_reports, [])

    def test_add_report_and_prevent_duplicates(self):
        """Adding reports should update the list and avoid duplicates."""
        self.station.add_report(self.report1)
        self.assertEqual(len(self.station.my_reports), 1)

        # Duplicate addition should be ignored
        self.station.add_report(self.report1)
        self.assertEqual(len(self.station.my_reports), 1)

        # Different report should be added
        self.station.add_report(self.report2)
        self.assertEqual(len(self.station.my_reports), 2)

    def test_add_report_invalid_type_raises_type_error(self):
        """Adding a non-Report instance must raise TypeError."""
        with self.assertRaises(TypeError):
            self.station.add_report("not_a_report")
        with self.assertRaises(TypeError):
            self.station.add_report(None)

    def test_type_validations_on_properties(self):
        """Properties should reject invalid types."""
        with self.assertRaises(TypeError):
            self.station.id = "invalid"
        with self.assertRaises(TypeError):
            self.station.name = 123
        with self.assertRaises(TypeError):
            self.station.my_reports = "not_a_list"


if __name__ == '__main__':
    unittest.main()
