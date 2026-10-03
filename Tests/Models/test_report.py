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

from Models.report import Report
from Models.station import Station


class TestReport(unittest.TestCase):
    """Unit tests for the Report domain model."""

    def setUp(self):
        """Create sample Report and Station objects."""
        self.station1 = Station(id=201, name="Station Beta", coords=(-73.0, 5.0))
        self.station2 = Station(id=202, name="Station Gamma", coords=(-73.5, 5.2))
        self.report = Report(
            id=1,
            magnitude=5.5,
            depth=15.0,
            epicenter=(-73.0, 5.0),
            date_time=datetime(2026, 2, 1, 8, 30),
            review=0
        )

    def test_init_and_properties(self):
        """Report should initialize all fields properly."""
        self.assertEqual(self.report.id, 1)
        self.assertEqual(self.report.magnitude, 5.5)
        self.assertEqual(self.report.depth, 15.0)
        self.assertEqual(self.report.epicenter, (-73.0, 5.0))
        self.assertEqual(self.report.review, 0)
        self.assertEqual(self.report.origin_station, [])

    def test_add_origin_station_and_prevent_duplicates(self):
        """Adding origin station should append to list and avoid duplicates."""
        self.report.add_origin_station(self.station1)
        self.assertEqual(len(self.report.origin_station), 1)

        # Duplicate addition should be ignored
        self.report.add_origin_station(self.station1)
        self.assertEqual(len(self.report.origin_station), 1)

        # Distinct station should be added
        self.report.add_origin_station(self.station2)
        self.assertEqual(len(self.report.origin_station), 2)

    def test_add_origin_station_invalid_type_raises_type_error(self):
        """Adding a non-Station instance must raise TypeError."""
        with self.assertRaises(TypeError):
            self.report.add_origin_station("invalid_station")

    def test_validation_errors_on_init(self):
        """Report attributes must reject invalid types."""
        with self.assertRaises(TypeError):
            Report(id="abc", magnitude=5.0, depth=10.0, epicenter=(0.0, 0.0), date_time=datetime.now(), review=0)
        with self.assertRaises(TypeError):
            Report(id=1, magnitude="high", depth=10.0, epicenter=(0.0, 0.0), date_time=datetime.now(), review=0)
        with self.assertRaises(TypeError):
            Report(id=1, magnitude=5.0, depth=10.0, epicenter=(0.0, 0.0), date_time="2026-01-01", review=0)
        with self.assertRaises(ValueError):
            Report(id=1, magnitude=5.0, depth=10.0, epicenter=(0.0,), date_time=datetime.now(), review=0)


if __name__ == '__main__':
    unittest.main()
