import unittest
from datetime import datetime, timedelta
from Business.observatory import Observatory
from Models.station import Station


class TestObservatoryGlobalRecovery(unittest.TestCase):
    def setUp(self):
        self.obs = Observatory()
        self.station = Station(1, "S-01", (100.0, 100.0))
        self.obs.stations = [self.station]

    def test_global_recovery_reports_changes_and_costs(self):
        # 1. Enable stress mode
        self.obs.stress_mode = True
        self.assertTrue(self.obs.stress_mode)

        # 2. Add events in sequential order to force topological imbalances
        base_time = self.obs.clock_simulation - timedelta(hours=4)
        for i in range(1, 12):
            self.obs.create_event(
                event_id=200 + i,
                magnitude=3.0 + (i * 0.2),
                depth=10.0,
                epicenter=(150.0 + i, 150.0 + i),
                date_time=base_time - timedelta(minutes=i * 5),
                station=self.station
            )

        # 3. Verify tree has imbalanced nodes while stress is active
        imbalanced_nodes = [
            n for n in self.obs.tree.inorder()
            if abs(n.balance_factor()) > 1
        ]
        self.assertGreater(len(imbalanced_nodes), 0)

        # 4. Execute global recovery
        report = self.obs.global_recovery()

        # 5. Verify the report structure and returned metrics
        self.assertTrue(report.get("success"))
        self.assertIn("rotations", report)
        self.assertIn("cases", report)
        self.assertIn("turns", report)
        self.assertGreater(report.get("total_rotations", 0), 0)
        self.assertGreater(report.get("total_turns", 0), 0)
        self.assertGreater(report.get("imbalanced_count", 0), 0)
        self.assertEqual(report.get("imbalanced_after", -1), 0)
        self.assertGreaterEqual(report.get("pre_height", 0), report.get("post_height", 0))
        self.assertGreaterEqual(report.get("elapsed_ms", 0), 0.0)
        self.assertTrue(report.get("in_place"))
        self.assertTrue(report.get("paused_queue"))

        # 6. Verify structural and balance invariants post-recovery
        self.assertFalse(self.obs.stress_mode)
        audit = self.obs.verify_structure()
        self.assertFalse(any(e.startswith("Error") for e in audit))

    def test_global_recovery_on_already_balanced_tree(self):
        base_time = self.obs.clock_simulation - timedelta(hours=2)
        # Normal mode insertion (auto-balanced AVL)
        self.obs.stress_mode = False
        for i in range(1, 5):
            self.obs.create_event(
                event_id=300 + i,
                magnitude=4.0,
                depth=15.0,
                epicenter=(200.0, 200.0),
                date_time=base_time - timedelta(minutes=i * 10),
                station=self.station
            )

        report = self.obs.global_recovery()
        self.assertTrue(report.get("success"))
        self.assertEqual(report.get("imbalanced_count", -1), 0)
        self.assertEqual(report.get("imbalanced_after", -1), 0)
        self.assertFalse(self.obs.stress_mode)


if __name__ == "__main__":
    unittest.main()
