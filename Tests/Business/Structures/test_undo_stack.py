import unittest
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
MODELS_DIR = os.path.join(PROJECT_ROOT, 'Models')
if MODELS_DIR not in sys.path:
    sys.path.insert(0, MODELS_DIR)

from Business.Structures.undo_stack import Undo_stack
from Models.action import Action


class TestUndoStack(unittest.TestCase):
    """Unit tests for the Undo_stack LIFO data structure."""

    def setUp(self):
        """Create sample Action instances and a fresh Undo_stack."""
        self.stack = Undo_stack()
        self.action1 = Action(id=1)
        self.action2 = Action(id=2)
        self.action3 = Action(id=3)

    def test_initial_stack_is_empty(self):
        """A new stack should be empty and have size 0."""
        self.assertTrue(self.stack.is_empty())
        self.assertEqual(self.stack.size(), 0)
        self.assertEqual(self.stack.actions, [])

    def test_stack_and_unstack_lifo_order(self):
        """Items pushed to the stack should be popped in Last-In-First-Out order."""
        self.stack.stack(self.action1)
        self.stack.stack(self.action2)
        self.assertFalse(self.stack.is_empty())
        self.assertEqual(self.stack.size(), 2)

        popped_first = self.stack.unstack()
        self.assertEqual(popped_first.id, self.action2.id)
        self.assertEqual(self.stack.size(), 1)

        popped_second = self.stack.unstack()
        self.assertEqual(popped_second.id, self.action1.id)
        self.assertTrue(self.stack.is_empty())
        self.assertEqual(self.stack.size(), 0)

    def test_unstack_from_empty_stack_raises_index_error(self):
        """Calling unstack on an empty stack must raise IndexError."""
        with self.assertRaises(IndexError):
            self.stack.unstack()

    def test_stack_invalid_type_raises_type_error(self):
        """Pushing an object that is not an Action instance must raise TypeError."""
        with self.assertRaises(TypeError):
            self.stack.stack("not_an_action")
        with self.assertRaises(TypeError):
            self.stack.stack(123)
        with self.assertRaises(TypeError):
            self.stack.stack(None)

    def test_actions_setter_valid(self):
        """Assigning a valid list of actions via property setter should update the stack."""
        self.stack.actions = [self.action1, self.action2]
        self.assertEqual(self.stack.size(), 2)
        self.assertEqual(self.stack.unstack().id, self.action2.id)

    def test_actions_setter_invalid_type_raises_type_error(self):
        """Assigning a non-list to actions property must raise TypeError."""
        with self.assertRaises(TypeError):
            self.stack.actions = "not_a_list"
        with self.assertRaises(TypeError):
            self.stack.actions = 42


if __name__ == '__main__':
    unittest.main()
