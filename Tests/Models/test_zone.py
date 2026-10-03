import unittest
import sys
import os

# Ensure project root and Models are in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'Models')
if MODELS_DIR not in sys.path:
    sys.path.insert(0, MODELS_DIR)

from Models.zone import Zone


class TestZone(unittest.TestCase):
    """Unit tests for the Zone domain model and spatial containment."""

    def setUp(self):
        """Create sample Zone for testing."""
        self.zone = Zone(
            id=1,
            name="Central Metropolitan",
            is_populated=True,
            ubication_x=(-75.5, -70.0),
            ubication_y=(4.0, 8.5)
        )

    def test_init_and_properties(self):
        """Zone initializes with correct attributes and supports getters/setters."""
        self.assertEqual(self.zone.id, 1)
        self.assertEqual(self.zone.name, "Central Metropolitan")
        self.assertTrue(self.zone.is_populated)
        self.assertEqual(self.zone.ubication_x, (-75.5, -70.0))
        self.assertEqual(self.zone.ubication_y, (4.0, 8.5))

        self.zone.name = "Northern Sector"
        self.assertEqual(self.zone.name, "Northern Sector")

    def test_contains_inside_points(self):
        """contains should return True for points strictly inside the bounding box."""
        self.assertTrue(self.zone.contains(-73.0, 6.0))
        self.assertTrue(self.zone.contains(-71.0, 5.0))

    def test_contains_boundary_points(self):
        """contains should return True for points on the exact borders."""
        self.assertTrue(self.zone.contains(-75.5, 4.0))  # Bottom-left corner
        self.assertTrue(self.zone.contains(-70.0, 8.5))  # Top-right corner
        self.assertTrue(self.zone.contains(-75.5, 6.0))  # Left edge
        self.assertTrue(self.zone.contains(-70.0, 6.0))  # Right edge

    def test_contains_outside_points(self):
        """contains should return False for points outside the bounding box."""
        self.assertFalse(self.zone.contains(-76.0, 6.0))  # Left of X
        self.assertFalse(self.zone.contains(-69.0, 6.0))  # Right of X
        self.assertFalse(self.zone.contains(-72.0, 3.5))  # Below Y
        self.assertFalse(self.zone.contains(-72.0, 9.0))  # Above Y

    def test_type_and_value_validations(self):
        """Zone should reject invalid types or invalid coordinate tuples."""
        with self.assertRaises(TypeError):
            Zone(id="1", name="Z", is_populated=True, ubication_x=(0.0, 1.0), ubication_y=(0.0, 1.0))
        with self.assertRaises(TypeError):
            Zone(id=1, name=123, is_populated=True, ubication_x=(0.0, 1.0), ubication_y=(0.0, 1.0))
        with self.assertRaises(TypeError):
            Zone(id=1, name="Z", is_populated="yes", ubication_x=(0.0, 1.0), ubication_y=(0.0, 1.0))
        with self.assertRaises(ValueError):
            Zone(id=1, name="Z", is_populated=True, ubication_x=(0.0,), ubication_y=(0.0, 1.0))


if __name__ == '__main__':
    unittest.main()
