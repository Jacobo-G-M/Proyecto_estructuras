"""
Tests / Presentation / test_gui_scenarios.py
Automated UI / GUI Test Suite validating all 6 Section 16 cases
directly executed in SismoLabApp, Topbar, TreeView, MapView, EventsView, DashboardView, and QueriesView.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

import customtkinter as ctk

from Presentation.app import SismoLabApp
from Business.observatory import Observatory
from Business.scenario_persistence import ScenarioPersistence


SCENARIOS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saved_versions", "casos_de_prueba"))


class TestGUIScenarios(unittest.TestCase):
    """
    Validates end-to-end execution of the 6 Section 16 scenarios in the graphical interface.
    Tests user interactions: loading scenarios from the Topbar pill, switching views,
    clicking step-by-step queue buttons, triggering AVL stress recovery, mass archival,
    inspecting tree node properties, and rejecting corrupted files via GUI error dialogs.
    """

    @classmethod
    def setUpClass(cls):
        # Configure headless CustomTkinter environment
        ctk.set_appearance_mode("Dark")

    def setUp(self):
        self.obs = Observatory()
        self.app = SismoLabApp(self.obs)
        self.app.withdraw()  # Run headless without opening visible OS window

    def tearDown(self):
        try:
            self.app.destroy()
        except Exception:
            pass

    def test_caso1_gui_limites_y_empates(self):
        """
        SCENARIO 1: BOUNDARIES AND TIE-BREAKING in the GUI
        - Topology loading from Topbar.
        - TreeView rendering and verification of keys K=(P, M, I).
        - Event A (zone boundary x=300) classified with P=3.
        - Event B (outside zone) classified with P=2.
        - Event C (M=6.0) classified with P=3.
        - ID tie-break between Event D (ID 20) and Event E (ID 35) with same P=2, M=5.0.
        - Rendering and validation in MapView and DashboardView.
        """
        filepath = os.path.join(SCENARIOS_DIR, "caso1_limites_empates.json")
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(filepath, "caso1_limites_empates")
            self.app.update()

        # Verify synchronization in the Topbar
        self.assertEqual(self.app.topbar.current_scenario_name, "caso1_limites_empates")

        # 1. Verify Dashboard
        self.app.switch_view("dashboard")
        self.app.update()
        self.assertEqual(self.obs.metrics.active_events, 5)
        self.assertEqual(len(self.obs.events_dict), 5)

        # 2. Verify TreeView and K key properties
        self.app.switch_view("arboles")
        self.app.update()
        tree_view = self.app.views["arboles"]

        # Verify expected priorities
        ev_a = self.obs.events_dict[50]
        ev_b = self.obs.events_dict[10]
        ev_c = self.obs.events_dict[60]
        ev_d = self.obs.events_dict[20]
        ev_e = self.obs.events_dict[35]

        self.assertEqual(ev_a.priority, 3, "Evento A en borde de zona debe tener P=3")
        self.assertEqual(ev_b.priority, 2, "Evento B fuera de zona debe tener P=2")
        self.assertEqual(ev_c.priority, 3, "Evento C con M=6.0 debe tener P=3")
        self.assertEqual(ev_d.priority, 2, "Evento D debe tener P=2")
        self.assertEqual(ev_e.priority, 2, "Evento E debe tener P=2")

        # Verify tie-break in key K: (2, 5.0, 35) > (2, 5.0, 20)
        self.assertGreater(ev_e.get_key(), ev_d.get_key())

        # Test node selection in the TreeView Inspector
        tree_view.selected_event_id = 50
        tree_view._refresh_inspector()
        self.assertIn("(3, 4.5, 50)", tree_view.lbl_hero_tuple.cget("text"))

        # 3. Verify MapView
        self.app.switch_view("mapa")
        self.app.update()
        map_view = self.app.views["mapa"]
        self.assertEqual(len(self.obs.geographical_map.zones), 1)
        self.assertEqual(len(self.obs.stations), 1)

    def test_caso2_gui_correccion_y_reporte_antiguo(self):
        """
        SCENARIO 2: CORRECTION AND OUTDATED REPORT in the GUI
        - Initial state: Event 100 with M=4.8, P=2, Rev 1.
        - Processing Report 2 in EventsView (Step-by-step): Accepted correction to M=6.2, P=3, Rev 2.
        - Processing Report 3 in EventsView (Step-by-step): Discarded due to outdated revision (Rev 1).
        - Updated metrics and UI rendering in EventsView and TreeView.
        """
        filepath = os.path.join(SCENARIOS_DIR, "caso2_correccion_reporte_antiguo_inicial.json")
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(filepath, "caso2_correccion_reporte_antiguo_inicial")
            self.app.update()

        events_view = self.app.views["eventos"]
        self.app.switch_view("eventos")
        self.app.update()

        # Verify initial state of the queue
        self.assertEqual(len(self.obs.report_queue.current_reports), 2)
        ev100 = self.obs.events_dict[100]
        self.assertEqual(ev100.priority, 2)
        self.assertEqual(ev100.review, 1)
        self.assertEqual(ev100.get_key(), (2, 4.8, 100))

        # --- Step 1 in the GUI: Process Correction Report ---
        events_view._handle_step_queue()
        self.app.update()

        self.assertEqual(len(self.obs.report_queue.current_reports), 1)
        self.assertEqual(ev100.review, 2)
        self.assertEqual(ev100.priority, 3)
        self.assertEqual(ev100.magnitude, 6.2)
        self.assertEqual(ev100.get_key(), (3, 6.2, 100))
        self.assertEqual(self.obs.metrics.corrections_accepted, 1)

        # --- Step 2 in the GUI: Process Obsolete Old Report ---
        events_view._handle_step_queue()
        self.app.update()

        self.assertEqual(len(self.obs.report_queue.current_reports), 0)
        # The event MUST NOT revert to Rev 1
        self.assertEqual(ev100.review, 2)
        self.assertEqual(ev100.priority, 3)
        self.assertEqual(ev100.magnitude, 6.2)
        self.assertEqual(self.obs.metrics.discarded_reports, 1)

        # Verify that TreeView reflects the new key K=(3, 6.2, 100)
        self.app.switch_view("arboles")
        self.app.update()
        tree_view = self.app.views["arboles"]
        tree_view.selected_event_id = 100
        tree_view._refresh_inspector()
        self.assertIn("(3, 6.2, 100)", tree_view.lbl_hero_tuple.cget("text"))

    def test_caso3_gui_reporte_tardio_y_replicas(self):
        """
        SCENARIO 3: LATE REPORT AND REPLICA ASSOCIATION in the GUI
        - Topology loading prior to late event arrival (Events 1 and 2).
        - Event 1 is reference and Event 2 is its replica.
        - Late Event 3 arrives (occurred at 09:55, earlier than 1 and 2, higher magnitude M=6.1).
        - Step executed in EventsView: replicas are deterministically re-associated.
        - Event 3 becomes primary reference and Events 1 and 2 become its replicas.
        - MapView and QueriesView display updated association topology.
        """
        filepath = os.path.join(SCENARIOS_DIR, "caso3_reporte_tardio_antes.json")
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(filepath, "caso3_reporte_tardio_antes")
            self.app.update()

        # Verify operational parameters
        self.assertEqual(self.obs.max_time, 48.0)
        self.assertEqual(self.obs.distance_epicenter, 40.0)

        # Previous state: Event 1 as reference for Event 2
        self.assertEqual(len(self.obs.associations), 1)
        self.assertEqual(self.obs.associations[0].chosen_reference.id, 1)

        # Process in the GUI the arrival of late Event 3 from the report queue
        events_view = self.app.views["eventos"]
        self.app.switch_view("eventos")
        self.app.update()

        events_view._handle_step_queue()
        self.app.update()

        # Event 3 was registered in the observatory
        self.assertIn(3, self.obs.events_dict)

        # Deterministic reclustering: Event 3 is now the reference for 1 and 2
        self.assertEqual(len(self.obs.associations), 1)
        assoc = self.obs.associations[0]
        self.assertEqual(assoc.chosen_reference.id, 3)
        child_ids = sorted([r.id for r in assoc.referenced_by])
        self.assertEqual(child_ids, [1, 2])

        # Verify visualization in MapView
        self.app.switch_view("mapa")
        self.app.update()

        # Verify in QueriesView (Association Explorer)
        self.app.switch_view("consultas")
        self.app.update()
        report_assoc, _ = self.obs.query_event_associations(3)
        self.assertIsNone(report_assoc.get("chosen_reference"))
        replica_ids = [item["event"].id for item in report_assoc.get("referenced_by", [])]
        self.assertEqual(sorted(replica_ids), [1, 2])

        report_assoc_1, _ = self.obs.query_event_associations(1)
        self.assertIsNotNone(report_assoc_1.get("chosen_reference"))
        self.assertEqual(report_assoc_1["chosen_reference"]["event"].id, 3)

    def test_caso4_gui_rotaciones_y_recuperacion_estres(self):
        """
        SCENARIO 4: ROTATIONS (LL, RR, LR, RL) AND STRESS MODE RECOVERY in the GUI
        - Part A: Loading insertion sequence with verified elementary rotations.
        - Part B: Loading unbalanced stress mode file (|BF| > 1).
        - Topbar indicates 'Stress: Active' and enables 'Recover AVL Balance' button.
        - Recovery button executed in UI:
          * In-place tree rebalancing preserving object identity.
          * Stress mode deactivated ('Stress: Inactive').
          * BST ordering invariant preserved.
        """
        # Part A: Loading rotation sequence
        seq_path = os.path.join(SCENARIOS_DIR, "caso4_rotaciones_secuencia.json")
        self.assertTrue(os.path.exists(seq_path), f"File not found: {seq_path}")

        res = self.obs.load_scenario_by_insertions(seq_path, adopt_avl=True)
        self.assertIn("avl", res)
        self.assertIn("metrics", res)
        # Verify that all 4 types of rotations were registered
        for case in ["LL", "RR", "LR", "RL"]:
            self.assertGreater(self.obs.metrics.cases.get(case, 0), 0, f"Debe disparar caso {case}")

        # Part B: Stress mode and recovery
        stress_path = os.path.join(SCENARIOS_DIR, "caso4_estres_desbalanceado.json")
        self.assertTrue(os.path.exists(stress_path), f"File not found: {stress_path}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(stress_path, "caso4_estres_desbalanceado")
            self.app.update()

        # Verify that UI detects ACTIVE Stress Mode
        self.assertTrue(self.obs.stress_mode)
        self.assertEqual(self.app.topbar.switch_stress.get(), 1)
        self.assertEqual(self.app.topbar.btn_recover.cget("state"), "normal")

        # Verify imbalance in the tree (> 1)
        max_bf = max(abs(n.balance_factor()) for n in self.obs.tree.inorder())
        self.assertGreater(max_bf, 1, "El árbol en estrés debe estar desbalanceado (|FB| > 1)")

        # Execute Global Recovery in the GUI
        with patch("Presentation.Components.Molecules.recovery_modal.RecoveryReportModal"):
            self.app.topbar._on_recover_click()
            self.app.update()

        # Verify that the tree recovered the AVL balance (|FB| <= 1)
        self.assertFalse(self.obs.stress_mode)
        self.assertEqual(self.app.topbar.switch_stress.get(), 0)
        self.assertEqual(self.app.topbar.btn_recover.cget("state"), "disabled")

        max_bf_after = max(abs(n.balance_factor()) for n in self.obs.tree.inorder())
        self.assertLessEqual(max_bf_after, 1, "El árbol recuperado debe ser AVL válido (|FB| <= 1)")

        # Verify that the BST order remained intact
        inorder_keys = [n.get_key() for n in self.obs.tree.inorder()]
        self.assertEqual(inorder_keys, sorted(inorder_keys), "El orden BST debe preservarse")

    def test_caso5_gui_archivo_masivo_subarboles_y_undo(self):
        """
        SCENARIO 5: BULK SUBTREE ARCHIVING AND UNDO in the GUI
        - Two-branch topology:
          * Subtree A (root 12): 3 nodes, all P=1 and age 98h > T=72h (ELIGIBLE).
          * Subtree B (root 62): 3 nodes (60, 62, 70), age 98h, but node 70 has P=2 (NOT ELIGIBLE).
        - In EventsView, 'Ejecutar Archivo de Rama' is triggered:
          * 3 nodes in Subtree A (10, 12, 14) are archived.
          * Subtree B remains intact in active tree (60, 62, 70).
        - '↩ Deshacer' is executed in Topbar:
          * Subtree A is restored to active AVL tree.
        """
        filepath = os.path.join(SCENARIOS_DIR, "caso5_archivo_subarboles.json")
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(filepath, "caso5_archivo_subarboles")
            self.app.update()

        events_view = self.app.views["eventos"]
        self.app.switch_view("eventos")
        self.app.update()

        # Verify previous state: 7 active events, 0 archived
        self.assertEqual(len(self.obs.events_dict), 7)
        self.assertEqual(len(self.obs.historic.archived), 0)

        # Configure threshold T=72h and execute mass archive in the GUI
        events_view.archive_threshold_hours = 72
        events_view._handle_execute_archive()
        self.app.update()

        # Archived Subtree A: nodes 10, 12, 14 in historic
        self.assertEqual(len(self.obs.events_dict), 4)
        self.assertEqual(len(self.obs.historic.archived), 3)
        for nid in [10, 12, 14]:
            self.assertIn(nid, self.obs.historic.archived)
            self.assertNotIn(nid, self.obs.events_dict)

        # Subtree B remains active: nodes 60, 62, 70 (plus root 50)
        for nid in [50, 60, 62, 70]:
            self.assertIn(nid, self.obs.events_dict)

        # Test UNDO in the graphical interface (Topbar)
        self.app.topbar._on_undo()
        self.app.update()

        # Fully restored state
        self.assertEqual(len(self.obs.events_dict), 7)
        self.assertEqual(len(self.obs.historic.archived), 0)
        for nid in [10, 12, 14, 50, 60, 62, 70]:
            self.assertIn(nid, self.obs.events_dict)

    def test_caso6_gui_persistencia_consistencia_y_rechazo(self):
        """
        SCENARIO 6: PERSISTENCE, CONSISTENCY AND REJECTION in the GUI
        - Attempt loading intentionally corrupted files via Topbar:
          1. Violated BST ordering.
          2. Duplicate IDs between active and historic sets.
          3. Inconsistent heights / balance factors.
          4. Imbalance outside {-1, 0, 1} without active stress mode.
        - GUI catches the exception, displays error dialog (messagebox.showerror),
          and aborts load atomically leaving observatory state intact.
        """
        error_cases = [
            ("caso6_error_bst_invalido.json", "orden BST"),
            ("caso6_error_ids_duplicados.json", "duplicado"),
            ("caso6_error_alturas_inconsistentes.json", "altura"),
            ("caso6_error_desbalance_sin_estres.json", "stress_mode"),
        ]

        for filename, expected_keyword in error_cases:
            filepath = os.path.join(SCENARIOS_DIR, filename)
            self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

            events_before = len(self.obs.events_dict)

            with patch("tkinter.messagebox.showerror") as mock_err, \
                 patch("tkinter.messagebox.showinfo") as mock_info:
                self.app.topbar._load_specific_scenario(filepath, filename)
                self.app.update()

                # The GUI must have shown the error dialog to the user
                self.assertTrue(mock_err.called, f"Expected showerror dialog for {filename}")
                self.assertFalse(mock_info.called, f"showinfo should NOT be called for invalid {filename}")

                # The observatory must have aborted atomically without mutations
                self.assertEqual(
                    len(self.obs.events_dict),
                    events_before,
                    f"Observatory state must remain unmodified after rejected load of {filename}"
                )


if __name__ == "__main__":
    unittest.main()
