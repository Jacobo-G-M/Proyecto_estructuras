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

from Models.action import Action


class TestAction(unittest.TestCase):
    """Unit tests for the Action domain model."""

    def test_init_and_id_property(self):
        """Action should initialize with an integer id and allow updates."""
        action = Action(id=10)
        self.assertEqual(action.id, 10)
        self.assertEqual(repr(action), "Action(id=10)")

        action.id = 25
        self.assertEqual(action.id, 25)

    def test_id_type_validation_raises_type_error(self):
        """Action id must be an int; strings, floats, booleans, and None must raise TypeError."""
        with self.assertRaises(TypeError):
            Action(id="1")
        with self.assertRaises(TypeError):
            Action(id=True)
        with self.assertRaises(TypeError):
            Action(id=False)
        with self.assertRaises(TypeError):
            Action(id=3.14)
        with self.assertRaises(TypeError):
            Action(id=None)

    def test_id_setter_type_validation(self):
        """Setter must enforce type checking on reassignment."""
        action = Action(id=1)
        with self.assertRaises(TypeError):
            action.id = "invalid"


if __name__ == '__main__':
    unittest.main()
