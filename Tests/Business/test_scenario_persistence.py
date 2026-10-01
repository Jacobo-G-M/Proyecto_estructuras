import unittest
import os
import json
import tempfile
from datetime import datetime

from Models.event import Event
from Models.node import Node
from Models.report import Report
from Models.station import Station
from Models.zone import Zone
from Business.observatory import Observatory
from Business.historic import Historic
from Business.geographical_map import Geographical_map
from Business.Structures.avl import AVL
from Business.Structures.bst import BST
from Business.Structures.report_queue import Report_Queue
from Business.Rules.asociation import Association
from Business.Rules.metrics import Metrics
from Business.scenario_persistence import ScenarioPersistence


class TestScenarioPersistence(unittest.TestCase):
    """
    - Structural export and atomic topology reconstruction (round-trip).
    - Validation checks: BST global order, cycles, duplicate IDs, height/BF mismatches, priority checks.
    - Stress mode enforcement on unbalanced topologies.
    - Insertion sequence loading and AVL vs BST structural metrics comparison.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.temp_dir.name, "scenario.json")

        # Create a populated Observatory instance
        self.obs = Observatory()
        self.obs.limit = 3
        self.obs.max_time = 48.0
        self.obs.distance_epicenter = 40.0
        self.obs.max_tree_age = 72
        self.obs.clock_simulation = datetime(2026, 9, 30, 12, 0, 0)
        self.obs.stress_mode = False

        # Zones
        z1 = Zone(id=1, name="Zona Urbana Central", is_populated=True, ubication_x=(100.0, 300.0), ubication_y=(100.0, 300.0))
        self.obs.geographical_map = Geographical_map(zones=[z1])

        # Stations
        st1 = Station(id=1, name="Estacion Central", coords=(150.0, 150.0))
        st2 = Station(id=2, name="Estacion Norte", coords=(200.0, 250.0))
        self.obs.stations = [st1, st2]

        # Active events in AVL: balanced 3-node tree
        # K = (P, M, I)
        # Root: Ev 2 -> K = (2, 5.0, 2)
        # Left: Ev 1 -> K = (1, 3.0, 1)
        # Right: Ev 3 -> K = (3, 6.5, 3)
        ev1 = Event(id=1, priority=1, magnitude=3.0, depth=10.0, epicenter=(50.0, 50.0), date_time=datetime(2026, 9, 29, 8, 0, 0), review=1, attention_state="Reviewed", status="Active")
        ev2 = Event(id=2, priority=2, magnitude=5.0, depth=40.0, epicenter=(150.0, 150.0), date_time=datetime(2026, 9, 29, 10, 0, 0), review=1, attention_state="Pending", status="Active")
        ev3 = Event(id=3, priority=3, magnitude=6.5, depth=20.0, epicenter=(200.0, 200.0), date_time=datetime(2026, 9, 29, 12, 0, 0), review=1, attention_state="Pending", status="Active")

        ev1.add_origin_station(st1)
        ev2.add_origin_station(st1)

        self.obs.tree = AVL(id=1)
        self.obs.tree.insert(Node(id=2, event=ev2))
        self.obs.tree.insert(Node(id=1, event=ev1))
        self.obs.tree.insert(Node(id=3, event=ev3))
        self.obs.events_dict = {1: ev1, 2: ev2, 3: ev3}

        # Historic: archived and deleted
        self.obs.historic = Historic()
        ev_arch = Event(id=10, priority=1, magnitude=2.5, depth=15.0, epicenter=(80.0, 80.0), date_time=datetime(2026, 9, 20, 10, 0, 0), review=1, attention_state="Reviewed", status="Archived")
        ev_del = Event(id=99, priority=1, magnitude=1.8, depth=5.0, epicenter=(30.0, 30.0), date_time=datetime(2026, 9, 15, 10, 0, 0), review=1, attention_state="Pending", status="Deleted")
        self.obs.historic.archive_event(ev_arch)
        self.obs.historic.delete_event(ev_del)

        # Report Queue
        self.obs.report_queue = Report_Queue()
        r1 = Report(id=101, magnitude=4.2, depth=25.0, epicenter=(120.0, 180.0), date_time=datetime(2026, 9, 30, 11, 0, 0), review=1, origin_station=[st1])
        self.obs.report_queue.enqueue(r1)

        # Associations
        assoc = Association(assoc_id=1, chosen_reference=ev3)
        assoc.add_replica(ev2)
        self.obs.associations = [assoc]

        # Metrics
        self.obs.metrics = Metrics()
        self.obs.metrics.corrections_accepted = 2
        self.obs.metrics.register_case("LL")
        self.obs.metrics.register_turn("right")

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # Test 1: Full Round-Trip Export and Import
    # -------------------------------------------------------------------------
    def test_export_and_load_by_topology_roundtrip(self):
        """Verifies full round-trip export and atomic reconstruction preserves exact operational state."""
        # Export scenario to file
        self.obs.save_scenario(self.json_path)
        self.assertTrue(os.path.exists(self.json_path))

        # Create a fresh, empty target Observatory
        target = Observatory()
        success, errors = target.load_scenario_by_topology(self.json_path)

        self.assertTrue(success, f"Expected successful load, but got errors: {errors}")
        self.assertEqual(len(errors), 0)

        # Verify operational parameters
        self.assertEqual(target.limit, 3)
        self.assertEqual(target.max_time, 48.0)
        self.assertEqual(target.distance_epicenter, 40.0)
        self.assertEqual(target.max_tree_age, 72)
        self.assertEqual(target.clock_simulation, self.obs.clock_simulation)
        self.assertEqual(target.stress_mode, False)

        # Verify tree topology
        self.assertIsNotNone(target.tree)
        self.assertIsNotNone(target.tree.root)
        self.assertEqual(target.tree.root.id, 2)
        self.assertEqual(target.tree.root.left_son.id, 1)
        self.assertEqual(target.tree.root.right_son.id, 3)
        self.assertEqual(target.tree.height(), 1)
        self.assertEqual(len(target.events_dict), 3)

        # Verify in-order sequence
        inorder_ids = [n.id for n in target.tree.inorder()]
        self.assertEqual(inorder_ids, [1, 2, 3])

        # Verify historic
        self.assertIn(10, target.historic.archived)
        self.assertEqual(target.historic.archived[10].status, "Archived")
        self.assertIn(99, target.historic.deleted)
        self.assertEqual(target.historic.deleted[99].status, "Deleted")

        # Verify queue
        self.assertEqual(len(target.report_queue.view_all()), 1)
        self.assertEqual(target.report_queue.view_all()[0].id, 101)

        # Verify associations
        self.assertEqual(len(target.associations), 1)
        self.assertEqual(target.associations[0].chosen_reference.id, 3)
        self.assertEqual([r.id for r in target.associations[0].referenced_by], [2])

        # Verify metrics
        self.assertEqual(target.metrics.corrections_accepted, 2)
        self.assertEqual(target.metrics.cases["LL"], 1)
        self.assertEqual(target.metrics.turns["right"], 1)

    # -------------------------------------------------------------------------
    # Test 2: Atomic Rejection on BST Global Order Violation
    # -------------------------------------------------------------------------
    def test_load_by_topology_atomic_rejection_on_bst_violation(self):
        """Verifies that an inverted BST ordering causes atomic rejection without altering target scenario."""
        self.obs.save_scenario(self.json_path)

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Violate BST order: swap left and right child pointers on root (node 2)
        root_node = next(n for n in data["tree"]["nodes"] if n["id"] == 2)
        root_node["left_id"] = 3   # K(3) > K(2), illegal on left side
        root_node["right_id"] = 1  # K(1) < K(2), illegal on right side

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Target observatory with existing state
        initial_clock = self.obs.clock_simulation
        success, errors = self.obs.load_scenario_by_topology(self.json_path)

        self.assertFalse(success)
        self.assertTrue(any("BST order violation" in err for err in errors))
        # Ensure target observatory was NOT modified
        self.assertEqual(self.obs.clock_simulation, initial_clock)
        self.assertEqual(self.obs.tree.root.id, 2)
        self.assertEqual(self.obs.tree.root.left_son.id, 1)

    # -------------------------------------------------------------------------
    # Test 3: Atomic Rejection on Cycle in Topology
    # -------------------------------------------------------------------------
    def test_load_by_topology_atomic_rejection_on_cycle(self):
        """Verifies that a circular reference in tree links is rejected."""
        self.obs.save_scenario(self.json_path)

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Create cycle: node 1's right child points back to node 2
        node1 = next(n for n in data["tree"]["nodes"] if n["id"] == 1)
        node1["right_id"] = 2

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        target = Observatory()
        success, errors = target.load_scenario_by_topology(self.json_path)

        self.assertFalse(success)
        self.assertTrue(any("Cycle detected" in err or "exactly one parent" in err for err in errors))

    # -------------------------------------------------------------------------
    # Test 4: Atomic Rejection on ID Overlap between Catalogs
    # -------------------------------------------------------------------------
    def test_load_by_topology_atomic_rejection_on_catalog_overlap(self):
        """Verifies rejection when an ID is duplicated between active tree and historic archive."""
        self.obs.save_scenario(self.json_path)

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Duplicate active ID 1 into historic archived
        dup_ev = dict(data["tree"]["nodes"][0]["event"])
        dup_ev["id"] = 1
        data["historic"]["archived"].append(dup_ev)

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        target = Observatory()
        success, errors = target.load_scenario_by_topology(self.json_path)

        self.assertFalse(success)
        self.assertTrue(any("overlap between active and archived" in err for err in errors))

    # -------------------------------------------------------------------------
    # Test 5: Atomic Rejection on Stored Height or Balance Factor Mismatch
    # -------------------------------------------------------------------------
    def test_load_by_topology_atomic_rejection_on_height_mismatch(self):
        """Verifies rejection when stored node height differs from computed height."""
        self.obs.save_scenario(self.json_path)

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Tamper height of root node
        root_node = next(n for n in data["tree"]["nodes"] if n["id"] == 2)
        root_node["height"] = 99  # Actual is 1

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        target = Observatory()
        success, errors = target.load_scenario_by_topology(self.json_path)

        self.assertFalse(success)
        self.assertTrue(any("stored height 99 does not match calculated" in err for err in errors))

    # -------------------------------------------------------------------------
    # Test 6: Atomic Rejection on Stored Priority Mismatch
    # -------------------------------------------------------------------------
    def test_load_by_topology_atomic_rejection_on_priority_mismatch(self):
        """Verifies rejection when stored event priority does not match Section 4 rules."""
        self.obs.save_scenario(self.json_path)

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Event 1 has magnitude 3.0, depth 10.0, outside populated -> calculated priority is 1
        # Tamper stored priority to 3
        node1 = next(n for n in data["tree"]["nodes"] if n["id"] == 1)
        node1["event"]["priority"] = 3

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        target = Observatory()
        success, errors = target.load_scenario_by_topology(self.json_path)

        self.assertFalse(success)
        self.assertTrue(any("stored priority 3 does not match calculated priority 1" in err for err in errors))

    # -------------------------------------------------------------------------
    # Test 7: Stress Mode Enforcement on Unbalanced Topology
    # -------------------------------------------------------------------------
    def test_load_by_topology_stress_mode_handling(self):
        """
        An ordered but unbalanced topology (|BF| > 1) can ONLY be loaded
        when stress_mode is enabled.
        """
        # Create an unbalanced linear chain: 3 -> left 2 -> left 1 (|BF| at root = 2)
        ev1 = Event(id=1, priority=1, magnitude=3.0, depth=10.0, epicenter=(0.0, 0.0), date_time=datetime(2026, 9, 29, 8, 0, 0), review=1)
        ev2 = Event(id=2, priority=2, magnitude=5.0, depth=10.0, epicenter=(0.0, 0.0), date_time=datetime(2026, 9, 29, 9, 0, 0), review=1)
        ev3 = Event(id=3, priority=3, magnitude=6.5, depth=10.0, epicenter=(0.0, 0.0), date_time=datetime(2026, 9, 29, 10, 0, 0), review=1)

        unbalanced_data = {
            "version": "1.0",
            "simulation_clock": "2026-09-30T12:00:00",
            "stress_mode": False,
            "parameters": {"limit_L": 3, "max_time_W": 48.0, "distance_epicenter_R": 40.0, "max_tree_age_T": 72},
            "tree": {
                "root_id": 3,
                "nodes": [
                    {
                        "id": 3,
                        "left_id": 2,
                        "right_id": None,
                        "height": 2,
                        "balance_factor": 2,  # Left height is 1, right is -1 -> BF = 2
                        "event": ScenarioPersistence._serialize_event(ev3),
                    },
                    {
                        "id": 2,
                        "left_id": 1,
                        "right_id": None,
                        "height": 1,
                        "balance_factor": 1,
                        "event": ScenarioPersistence._serialize_event(ev2),
                    },
                    {
                        "id": 1,
                        "left_id": None,
                        "right_id": None,
                        "height": 0,
                        "balance_factor": 0,
                        "event": ScenarioPersistence._serialize_event(ev1),
                    },
                ],
            },
            "historic": {"archived": [], "deleted": []},
            "report_queue": [],
            "associations": [],
            "metrics": {},
        }

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(unbalanced_data, f)

        # Attempt to load in normal mode (stress_mode = False) -> MUST FAIL
        target_normal = Observatory()
        success, errors = target_normal.load_scenario_by_topology(self.json_path)
        self.assertFalse(success)
        self.assertTrue(any("Unbalanced topology" in err and "stress_mode" in err for err in errors))

        # Attempt to load with stress_mode = True -> MUST SUCCEED
        unbalanced_data["stress_mode"] = True
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(unbalanced_data, f)

        target_stress = Observatory()
        success, errors = target_stress.load_scenario_by_topology(self.json_path)
        self.assertTrue(success, f"Expected success in stress mode, got: {errors}")
        self.assertTrue(target_stress.stress_mode)
        self.assertEqual(target_stress.tree.root.id, 3)

    # -------------------------------------------------------------------------
    # Test 8: Load by Insertions (AVL vs BST Structural Comparison)
    # -------------------------------------------------------------------------
    def test_load_by_insertions_success_and_comparison(self):
        """
        Verifies loading an event sequence applies identical comparator to AVL and BST,
        highlighting AVL balancing advantage over BST.
        """
        # Ascending sequence of 5 events:
        # BST will degenerate into a skewed linked-list of height 4.
        # AVL will balance itself with height 2.
        events_payload = [
            {"id": 1, "priority": 1, "magnitude": 2.0, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:00:00"},
            {"id": 2, "priority": 1, "magnitude": 3.0, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:05:00"},
            {"id": 3, "priority": 2, "magnitude": 4.6, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:10:00"},
            {"id": 4, "priority": 2, "magnitude": 5.2, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:15:00"},
            {"id": 5, "priority": 3, "magnitude": 6.5, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:20:00"},
        ]

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(events_payload, f)

        result = self.obs.load_scenario_by_insertions(self.json_path)

        self.assertIn("avl", result)
        self.assertIn("bst", result)
        self.assertIn("metrics", result)

        metrics = result["metrics"]
        self.assertEqual(metrics["total_events"], 5)
        # AVL height must be 2, BST height must be 4
        self.assertEqual(metrics["avl_height"], 2)
        self.assertEqual(metrics["bst_height"], 4)
        self.assertLess(metrics["avl_height"], metrics["bst_height"])

        # AVL leaves must be greater than BST leaves (BST has only 1 leaf in a skewed chain)
        self.assertEqual(metrics["bst_leaves"], 1)
        self.assertGreater(metrics["avl_leaves"], metrics["bst_leaves"])

    # -------------------------------------------------------------------------
    # Test 9: Load by Insertions Invalidation on Duplicate ID
    # -------------------------------------------------------------------------
    def test_load_by_insertions_duplicate_id_invalidation(self):
        """A duplicate identifier in the insertion sequence invalidates the file."""
        events_payload = [
            {"id": 1, "priority": 1, "magnitude": 2.0, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:00:00"},
            {"id": 1, "priority": 1, "magnitude": 2.5, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:05:00"},
        ]

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(events_payload, f)

        with self.assertRaises(ValueError) as ctx:
            self.obs.load_scenario_by_insertions(self.json_path)

        self.assertIn("Duplicate event ID 1 found", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Test 10: Non-Existent and Malformed Files
    # -------------------------------------------------------------------------
    def test_non_existent_and_malformed_files(self):
        """Verifies graceful handling of non-existent or unparseable JSON files."""
        # Non-existent file
        success, errors = self.obs.load_scenario_by_topology("non_existent_file.json")
        self.assertFalse(success)
        self.assertTrue(any("not found" in err.lower() for err in errors))

        # Malformed file
        with open(self.json_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json content ...")

        success, errors = self.obs.load_scenario_by_topology(self.json_path)
        self.assertFalse(success)
        self.assertTrue(any("failed to parse" in err.lower() for err in errors))

    # -------------------------------------------------------------------------
    # Test 11: Load by Insertions with Optional AVL Adoption
    # -------------------------------------------------------------------------
    def test_load_by_insertions_with_adopt_avl(self):
        """Verifies that adopt_avl=True populates observatory.tree and events_dict."""
        events_payload = [
            {"id": 10, "priority": 1, "magnitude": 2.0, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:00:00"},
            {"id": 20, "priority": 2, "magnitude": 4.8, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:05:00"},
            {"id": 30, "priority": 3, "magnitude": 6.2, "depth": 10.0, "epicenter": [0.0, 0.0], "date_time": "2026-09-30T10:10:00"},
        ]
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(events_payload, f)

        target = Observatory()
        res = target.load_scenario_by_insertions(self.json_path, adopt_avl=True)

        self.assertIsNotNone(target.tree)
        self.assertIsNotNone(target.tree.root)
        self.assertEqual(len(target.events_dict), 3)
        self.assertIn(20, target.events_dict)
        self.assertEqual(target.tree.root.id, 20)

    # -------------------------------------------------------------------------
    # Test 12: Deep Multi-Level Tree Topology Reconstruction
    # -------------------------------------------------------------------------
    def test_deep_tree_height_reconstruction(self):
        """Verifies that bottom-up post-order height calculation correctly reconstructs deep trees."""
        deep_obs = Observatory()
        # Insert 7 nodes to create a 3-level tree (height 2)
        for i in range(1, 8):
            mag = 1.0 + (i * 0.4)
            p = deep_obs.calculate_priority(mag, 10.0, (0.0, 0.0))
            ev = Event(id=i, priority=p, magnitude=mag, depth=10.0, epicenter=(0.0, 0.0), date_time=datetime(2026, 9, 30, 10, i, 0), review=1)
            deep_obs.tree.insert(Node(id=i, event=ev))
            deep_obs.events_dict[i] = ev

        deep_obs.save_scenario(self.json_path)

        target = Observatory()
        success, errors = target.load_scenario_by_topology(self.json_path)
        self.assertTrue(success, f"Errors: {errors}")
        self.assertEqual(target.tree.height(), deep_obs.tree.height())
        self.assertEqual(len(target.events_dict), 7)


if __name__ == "__main__":
    unittest.main()

