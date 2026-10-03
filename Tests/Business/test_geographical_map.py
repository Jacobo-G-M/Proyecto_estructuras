import unittest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'Models')
if MODELS_DIR not in sys.path:
    sys.path.insert(0, MODELS_DIR)

from Business.geographical_map import Geographical_map
from Models.zone import Zone


class TestGeographicalMap(unittest.TestCase):
    """Unit tests for the Geographical_map container and spatial query logic."""

    def setUp(self):
        """Create sample zones and an empty Geographical_map."""
        self.geo_map = Geographical_map()
        self.zone_pop = Zone(
            id=1, name="Metropolitan", is_populated=True,
            ubication_x=(-75.0, -70.0), ubication_y=(4.0, 8.0)
        )
        self.zone_rural = Zone(
            id=2, name="Rural Desert", is_populated=False,
            ubication_x=(-69.0, -65.0), ubication_y=(1.0, 3.0)
        )

    def test_initial_state(self):
        """A new map should have an empty list of zones."""
        self.assertEqual(self.geo_map.zones, [])

    def test_add_zone_success(self):
        """Adding zones should append them to the internal list."""
        self.geo_map.add_zone(self.zone_pop)
        self.assertEqual(len(self.geo_map.zones), 1)
        self.assertEqual(self.geo_map.zones[0].id, 1)

    def test_add_zone_duplicate_id_raises_value_error(self):
        """Adding two zones with the same id must raise ValueError."""
        self.geo_map.add_zone(self.zone_pop)
        duplicate_zone = Zone(
            id=1, name="Clone", is_populated=False,
            ubication_x=(0.0, 1.0), ubication_y=(0.0, 1.0)
        )
        with self.assertRaises(ValueError):
            self.geo_map.add_zone(duplicate_zone)

    def test_add_zone_invalid_type_raises_type_error(self):
        """Adding a non-Zone object must raise TypeError."""
        with self.assertRaises(TypeError):
            self.geo_map.add_zone("not_a_zone")

    def test_remove_zone(self):
        """remove_zone should remove the zone if present."""
        self.geo_map.add_zone(self.zone_pop)
        self.geo_map.add_zone(self.zone_rural)
        self.assertEqual(len(self.geo_map.zones), 2)

        self.geo_map.remove_zone(self.zone_pop)
        self.assertEqual(len(self.geo_map.zones), 1)
        self.assertEqual(self.geo_map.zones[0].id, 2)

    def test_remove_zone_invalid_type_raises_type_error(self):
        """Calling remove_zone with a non-Zone object must raise TypeError."""
        with self.assertRaises(TypeError):
            self.geo_map.remove_zone("invalid")

    def test_get_zone_by_id(self):
        """get_zone_by_id should return the zone if found, or None otherwise."""
        self.geo_map.add_zone(self.zone_pop)
        self.geo_map.add_zone(self.zone_rural)

        found = self.geo_map.get_zone_by_id(1)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Metropolitan")

        not_found = self.geo_map.get_zone_by_id(999)
        self.assertIsNone(not_found)

    def test_get_zone_by_id_invalid_type_raises_type_error(self):
        """Querying with a non-integer or boolean ID must raise TypeError."""
        with self.assertRaises(TypeError):
            self.geo_map.get_zone_by_id("1")
        with self.assertRaises(TypeError):
            self.geo_map.get_zone_by_id(True)

    def test_is_in_populated_zone(self):
        """is_in_populated_zone should only return True if the point is inside a populated zone."""
        self.geo_map.add_zone(self.zone_pop)
        self.geo_map.add_zone(self.zone_rural)

        # Inside populated zone (-75 to -70, 4 to 8)
        self.assertTrue(self.geo_map.is_in_populated_zone(-72.0, 5.0))

        # Inside rural unpopulated zone (-69 to -65, 1 to 3)
        self.assertFalse(self.geo_map.is_in_populated_zone(-67.0, 2.0))

        # Outside all zones
        self.assertFalse(self.geo_map.is_in_populated_zone(0.0, 0.0))

    def test_is_in_populated_zone_invalid_types_raise_type_error(self):
        """Coordinates must be numbers."""
        with self.assertRaises(TypeError):
            self.geo_map.is_in_populated_zone("0", 0)
        with self.assertRaises(TypeError):
            self.geo_map.is_in_populated_zone(0, None)


if __name__ == '__main__':
    unittest.main()
