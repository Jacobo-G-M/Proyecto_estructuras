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

from Business.Structures.report_queue import Report_Queue
from Models.report import Report


class TestReportQueue(unittest.TestCase):
    """Unit tests for the Report_Queue FIFO data structure."""

    def setUp(self):
        """Create sample Report objects and a fresh Report_Queue instance."""
        self.queue = Report_Queue()
        self.report1 = Report(
            id=1,
            magnitude=5.2,
            depth=12.0,
            epicenter=(10.0, 20.0),
            date_time=datetime(2026, 1, 1, 10, 0, 0),
            review=0
        )
        self.report2 = Report(
            id=2,
            magnitude=6.1,
            depth=15.5,
            epicenter=(11.0, 21.0),
            date_time=datetime(2026, 1, 2, 11, 0, 0),
            review=1
        )
        self.report3 = Report(
            id=3,
            magnitude=4.8,
            depth=8.0,
            epicenter=(12.0, 22.0),
            date_time=datetime(2026, 1, 3, 12, 0, 0),
            review=0
        )

    def test_initial_queue_is_empty(self):
        """A new queue should be empty and have length 0."""
        self.assertTrue(self.queue.is_empty())
        self.assertEqual(len(self.queue.current_reports), 0)
        self.assertEqual(self.queue.view_all(), [])

    def test_enqueue_and_dequeue_fifo_order(self):
        """Items enqueued should be dequeued in First-In-First-Out order."""
        self.queue.enqueue(self.report1)
        self.queue.enqueue(self.report2)
        self.assertFalse(self.queue.is_empty())
        self.assertEqual(len(self.queue.current_reports), 2)

        dequeued_first = self.queue.dequeue()
        self.assertEqual(dequeued_first.id, self.report1.id)
        self.assertEqual(len(self.queue.current_reports), 1)

        dequeued_second = self.queue.dequeue()
        self.assertEqual(dequeued_second.id, self.report2.id)
        self.assertTrue(self.queue.is_empty())

    def test_dequeue_from_empty_queue_raises_index_error(self):
        """Calling dequeue on an empty queue must raise IndexError."""
        with self.assertRaises(IndexError):
            self.queue.dequeue()

    def test_enqueue_invalid_type_raises_type_error(self):
        """Enqueueing an object that is not a Report instance must raise TypeError."""
        with self.assertRaises(TypeError):
            self.queue.enqueue("not_a_report")
        with self.assertRaises(TypeError):
            self.queue.enqueue(123)
        with self.assertRaises(TypeError):
            self.queue.enqueue(None)

    def test_view_all_returns_shallow_copy(self):
        """view_all should return a copy, not the internal list reference."""
        self.queue.enqueue(self.report1)
        copy_list = self.queue.view_all()
        self.assertEqual(copy_list, [self.report1])

        # Modifying copy_list should not affect internal reports
        copy_list.append(self.report2)
        self.assertEqual(len(self.queue.current_reports), 1)

    def test_add_in_position_valid(self):
        """Inserting at valid indices should place elements at the expected positions."""
        self.queue.enqueue(self.report1)
        self.queue.enqueue(self.report3)

        # Insert at index 1 (between report1 and report3)
        self.queue.add_in_position(self.report2, 1)
        self.assertEqual(self.queue.current_reports[0].id, self.report1.id)
        self.assertEqual(self.queue.current_reports[1].id, self.report2.id)
        self.assertEqual(self.queue.current_reports[2].id, self.report3.id)

    def test_add_in_position_invalid_type_raises_type_error(self):
        """Adding a non-Report at a position must raise TypeError."""
        with self.assertRaises(TypeError):
            self.queue.add_in_position("invalid", 0)

    def test_add_in_position_out_of_bounds_raises_index_error(self):
        """Adding at negative or exceeding indices must raise IndexError."""
        with self.assertRaises(IndexError):
            self.queue.add_in_position(self.report1, -1)
        with self.assertRaises(IndexError):
            self.queue.add_in_position(self.report1, 5)

    def test_current_reports_setter(self):
        """The current_reports property setter should replace the internal list."""
        self.queue.current_reports = [self.report1, self.report2]
        self.assertEqual(len(self.queue.current_reports), 2)
        self.assertEqual(self.queue.dequeue().id, self.report1.id)


if __name__ == '__main__':
    unittest.main()
