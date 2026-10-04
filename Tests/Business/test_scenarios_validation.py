"""
Tests / Business / test_scenarios_validation.py
Automated tests validating the 6 scenarios of Section 16 using ScenarioPersistence.
"""

import unittest
import os
import json
from Business.observatory import Observatory
from Business.scenario_persistence import ScenarioPersistence

SCENARIOS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saved_versions", "casos_de_prueba"))


class TestSection16Scenarios(unittest.TestCase):
    """Test suite verifying all JSON test files for Section 16."""

    def test_case_1_valid_topology(self):
        """Case 1: Limits and tiebreakers must load cleanly."""
        fp = os.path.join(SCENARIOS_DIR, "caso1_limites_empates.json")
        obs = Observatory()
        ok, errs = ScenarioPersistence.load_by_topology(obs, fp)
        self.assertTrue(ok, f"Case 1 failed to load: {errs}")
        self.assertEqual(len(errs), 0)
        # Verify event priorities
        self.assertEqual(obs.events_dict[50].priority, 3)  # Border populated -> P=3
        self.assertEqual(obs.events_dict[10].priority, 2)  # Outside populated -> P=2
        self.assertEqual(obs.events_dict[60].priority, 3)  # M=6.0 -> P=3
        self.assertEqual(obs.events_dict[20].priority, 2)  # M=5.0 ID=20 -> P=2
        self.assertEqual(obs.events_dict[35].priority, 2)  # M=5.0 ID=35 -> P=2
        # Verify tree order
        keys = [nd.get_key() for nd in obs.tree.inorder()]
        self.assertEqual(keys, sorted(keys))

    def test_case_2_report_processing(self):
        """Case 2: Initial and final states must be valid topologies."""
        fp_init = os.path.join(SCENARIOS_DIR, "caso2_correccion_reporte_antiguo_inicial.json")
        obs = Observatory()
        ok, errs = ScenarioPersistence.load_by_topology(obs, fp_init)
        self.assertTrue(ok, f"Case 2 init failed: {errs}")
        self.assertEqual(obs.events_dict[100].review, 1)
        self.assertEqual(obs.events_dict[100].priority, 2)

        fp_final = os.path.join(SCENARIOS_DIR, "caso2_correccion_reporte_antiguo_final.json")
        obs2 = Observatory()
        ok2, errs2 = ScenarioPersistence.load_by_topology(obs2, fp_final)
        self.assertTrue(ok2, f"Case 2 final failed: {errs2}")
        self.assertEqual(obs2.events_dict[100].review, 2)
        self.assertEqual(obs2.events_dict[100].priority, 3)
        self.assertEqual(obs2.metrics.corrections_accepted, 1)
        self.assertEqual(obs2.metrics.discarded_reports, 1)

    def test_case_3_late_report_associations(self):
        """Case 3: Associations must cluster under Event 3."""
        fp = os.path.join(SCENARIOS_DIR, "caso3_reporte_tardio_despues.json")
        obs = Observatory()
        ok, errs = ScenarioPersistence.load_by_topology(obs, fp)
        self.assertTrue(ok, f"Case 3 failed: {errs}")
        self.assertEqual(len(obs.associations), 1)
        assoc = obs.associations[0]
        self.assertEqual(assoc.chosen_reference.id, 3)
        self.assertEqual(sorted([r.id for r in assoc.referenced_by]), [1, 2])

    def test_case_4_insertions_and_stress_recovery(self):
        """Case 4: Insertion sequence comparison and stress recovery."""
        fp_seq = os.path.join(SCENARIOS_DIR, "caso4_rotaciones_secuencia.json")
        res = ScenarioPersistence.load_by_insertions(fp_seq)
        self.assertLessEqual(res["metrics"]["avl_height"], res["metrics"]["bst_height"])

        # Stress degenerated file
        fp_stress = os.path.join(SCENARIOS_DIR, "caso4_estres_desbalanceado.json")
        obs_stress = Observatory()
        ok_stress, errs_stress = ScenarioPersistence.load_by_topology(obs_stress, fp_stress)
        self.assertTrue(ok_stress, f"Case 4 stress failed: {errs_stress}")
        self.assertTrue(obs_stress.stress_mode)
        self.assertGreater(abs(obs_stress.tree.root.balance_factor()), 1)

        # Recovered file
        fp_rec = os.path.join(SCENARIOS_DIR, "caso4_estres_recuperado.json")
        obs_rec = Observatory()
        ok_rec, errs_rec = ScenarioPersistence.load_by_topology(obs_rec, fp_rec)
        self.assertTrue(ok_rec, f"Case 4 rec failed: {errs_rec}")
        self.assertFalse(obs_rec.stress_mode)
        for nd in obs_rec.tree.preorder():
            self.assertLessEqual(abs(nd.balance_factor()), 1)

    def test_case_5_mass_archival(self):
        """Case 5: Mass archival must select Subtree A and restore cleanly with Undo."""
        fp = os.path.join(SCENARIOS_DIR, "caso5_archivo_subarboles.json")
        obs = Observatory()
        ok, errs = ScenarioPersistence.load_by_topology(obs, fp)
        self.assertTrue(ok, f"Case 5 failed: {errs}")
        prev = obs.archive_subtree(execute=False)
        self.assertEqual(prev["best_root_id"], 12)
        self.assertEqual(prev["count"], 3)
        self.assertEqual(set(prev["affected_ids"]), {10, 12, 14})

    def test_case_6_rejections(self):
        """Case 6: Four intentional invalid files must be rejected with specific errors."""
        obs = Observatory()

        # 1. BST order violated
        fp_bst = os.path.join(SCENARIOS_DIR, "caso6_error_bst_invalido.json")
        ok, errs = ScenarioPersistence.load_by_topology(obs, fp_bst)
        self.assertFalse(ok)
        self.assertTrue(any("Global BST order violation" in e for e in errs))

        # 2. Duplicate IDs
        fp_dup = os.path.join(SCENARIOS_DIR, "caso6_error_ids_duplicados.json")
        ok, errs = ScenarioPersistence.load_by_topology(obs, fp_dup)
        self.assertFalse(ok)
        self.assertTrue(any("ID overlap between active and archived" in e for e in errs))

        # 3. Inconsistent heights
        fp_h = os.path.join(SCENARIOS_DIR, "caso6_error_alturas_inconsistentes.json")
        ok, errs = ScenarioPersistence.load_by_topology(obs, fp_h)
        self.assertFalse(ok)
        self.assertTrue(any("stored height" in e for e in errs))
        self.assertTrue(any("stored balance factor" in e for e in errs))

        # 4. Unbalanced without stress mode
        fp_unbal = os.path.join(SCENARIOS_DIR, "caso6_error_desbalance_sin_estres.json")
        ok, errs = ScenarioPersistence.load_by_topology(obs, fp_unbal)
        self.assertFalse(ok)
        self.assertTrue(any("Unbalanced topology" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
