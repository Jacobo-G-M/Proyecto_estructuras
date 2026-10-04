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
        CASO 1: LÍMITES Y EMPATES en la GUI
        - Carga de topología desde la Topbar.
        - Renderizado en TreeView y verificación de claves K=(P, M, I).
        - Evento A (borde de zona x=300) clasificado con P=3.
        - Evento B (fuera de zona) clasificado con P=2.
        - Evento C (M=6.0) clasificado con P=3.
        - Desempate por ID entre Evento D (ID 20) y Evento E (ID 35) con misma P=2, M=5.0.
        - Renderizado y validación en MapView y DashboardView.
        """
        filepath = os.path.join(SCENARIOS_DIR, "caso1_limites_empates.json")
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(filepath, "caso1_limites_empates")
            self.app.update()

        # Verificar sincronización en la Topbar
        self.assertEqual(self.app.topbar.current_scenario_name, "caso1_limites_empates")

        # 1. Verificar Dashboard
        self.app.switch_view("dashboard")
        self.app.update()
        self.assertEqual(self.obs.metrics.active_events, 5)
        self.assertEqual(len(self.obs.events_dict), 5)

        # 2. Verificar TreeView y propiedades de claves K
        self.app.switch_view("arboles")
        self.app.update()
        tree_view = self.app.views["arboles"]

        # Verificar prioridades esperadas
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

        # Verificar desempate en la clave K: (2, 5.0, 35) > (2, 5.0, 20)
        self.assertGreater(ev_e.get_key(), ev_d.get_key())

        # Probar selección de nodo en el Inspector de TreeView
        tree_view.selected_event_id = 50
        tree_view._refresh_inspector()
        self.assertIn("(3, 4.5, 50)", tree_view.lbl_hero_tuple.cget("text"))

        # 3. Verificar MapView
        self.app.switch_view("mapa")
        self.app.update()
        map_view = self.app.views["mapa"]
        self.assertEqual(len(self.obs.geographical_map.zones), 1)
        self.assertEqual(len(self.obs.stations), 1)

    def test_caso2_gui_correccion_y_reporte_antiguo(self):
        """
        CASO 2: CORRECCIÓN Y REPORTE ANTIGUO en la GUI
        - Estado inicial: Evento 100 con M=4.8, P=2, Rev 1.
        - Procesamiento de Reporte 2 en EventsView (Paso a Paso): Corrección aceptada a M=6.2, P=3, Rev 2.
        - Procesamiento de Reporte 3 en EventsView (Paso a Paso): Descarte por revisión obsoleta (Rev 1).
        - Métricas actualizadas y visualización en EventsView y TreeView.
        """
        filepath = os.path.join(SCENARIOS_DIR, "caso2_correccion_reporte_antiguo_inicial.json")
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(filepath, "caso2_correccion_reporte_antiguo_inicial")
            self.app.update()

        events_view = self.app.views["eventos"]
        self.app.switch_view("eventos")
        self.app.update()

        # Verificar estado inicial de la cola
        self.assertEqual(len(self.obs.report_queue.current_reports), 2)
        ev100 = self.obs.events_dict[100]
        self.assertEqual(ev100.priority, 2)
        self.assertEqual(ev100.review, 1)
        self.assertEqual(ev100.get_key(), (2, 4.8, 100))

        # --- Paso 1 en la GUI: Procesar Reporte de Corrección ---
        events_view._handle_step_queue()
        self.app.update()

        self.assertEqual(len(self.obs.report_queue.current_reports), 1)
        self.assertEqual(ev100.review, 2)
        self.assertEqual(ev100.priority, 3)
        self.assertEqual(ev100.magnitude, 6.2)
        self.assertEqual(ev100.get_key(), (3, 6.2, 100))
        self.assertEqual(self.obs.metrics.corrections_accepted, 1)

        # --- Paso 2 en la GUI: Procesar Reporte Antiguo Obsoleto ---
        events_view._handle_step_queue()
        self.app.update()

        self.assertEqual(len(self.obs.report_queue.current_reports), 0)
        # El evento NO debe revertir a Rev 1
        self.assertEqual(ev100.review, 2)
        self.assertEqual(ev100.priority, 3)
        self.assertEqual(ev100.magnitude, 6.2)
        self.assertEqual(self.obs.metrics.discarded_reports, 1)

        # Verificar que TreeView refleja la nueva clave K=(3, 6.2, 100)
        self.app.switch_view("arboles")
        self.app.update()
        tree_view = self.app.views["arboles"]
        tree_view.selected_event_id = 100
        tree_view._refresh_inspector()
        self.assertIn("(3, 6.2, 100)", tree_view.lbl_hero_tuple.cget("text"))

    def test_caso3_gui_reporte_tardio_y_replicas(self):
        """
        CASO 3: REPORTE TARDÍO Y ASOCIACIÓN DE RÉPLICAS en la GUI
        - Carga de topología antes de la llegada tardía (Eventos 1 y 2).
        - Evento 1 es referencia y Evento 2 es su réplica.
        - Llega Evento 3 tardío (ocurrió a las 09:55, anterior a 1 y 2, con mayor magnitud M=6.1).
        - Se ejecuta paso en EventsView: se reasocian réplicas determinísticamente.
        - Evento 3 pasa a ser referencia principal y Eventos 1 y 2 pasan a ser sus réplicas.
        - MapView y QueriesView reflejan la nueva estructura de asociaciones.
        """
        filepath = os.path.join(SCENARIOS_DIR, "caso3_reporte_tardio_antes.json")
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(filepath, "caso3_reporte_tardio_antes")
            self.app.update()

        # Verificar parámetros operativos
        self.assertEqual(self.obs.max_time, 48.0)
        self.assertEqual(self.obs.distance_epicenter, 40.0)

        # Estado previo: Evento 1 como referencia de Evento 2
        self.assertEqual(len(self.obs.associations), 1)
        self.assertEqual(self.obs.associations[0].chosen_reference.id, 1)

        # Procesar en la GUI la llegada del Evento 3 tardío desde la cola de reportes
        events_view = self.app.views["eventos"]
        self.app.switch_view("eventos")
        self.app.update()

        events_view._handle_step_queue()
        self.app.update()

        # El Evento 3 fue registrado en el observatorio
        self.assertIn(3, self.obs.events_dict)

        # Reclustering determinista: Evento 3 es ahora la referencia de 1 y 2
        self.assertEqual(len(self.obs.associations), 1)
        assoc = self.obs.associations[0]
        self.assertEqual(assoc.chosen_reference.id, 3)
        child_ids = sorted([r.id for r in assoc.referenced_by])
        self.assertEqual(child_ids, [1, 2])

        # Verificar visualización en MapView
        self.app.switch_view("mapa")
        self.app.update()

        # Verificar en QueriesView (Association Explorer)
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
        CASO 4: ROTACIONES (LL, RR, LR, RL) Y RECUPERACIÓN DE MODO ESTRÉS en la GUI
        - Parte A: Carga de secuencia de inserciones con rotaciones elementales verificadas.
        - Parte B: Carga de archivo en modo estrés desbalanceado (|FB| > 1).
        - Topbar muestra 'Estrés: Activo' y habilita el botón 'Recuperar Equilibrio AVL'.
        - Se ejecuta el botón de recuperación en la interfaz:
          * Árbol rebalanceado in-situ sin perder identidades.
          * Modo estrés desactivado ('Estrés: Inactivo').
          * Consistencia de orden BST preservada.
        """
        # Parte A: Carga de secuencia de rotaciones
        seq_path = os.path.join(SCENARIOS_DIR, "caso4_rotaciones_secuencia.json")
        self.assertTrue(os.path.exists(seq_path), f"File not found: {seq_path}")

        res = self.obs.load_scenario_by_insertions(seq_path, adopt_avl=True)
        self.assertIn("avl", res)
        self.assertIn("metrics", res)
        # Verificar que se registraron los 4 tipos de rotaciones
        for case in ["LL", "RR", "LR", "RL"]:
            self.assertGreater(self.obs.metrics.cases.get(case, 0), 0, f"Debe disparar caso {case}")

        # Parte B: Modo estrés y recuperación
        stress_path = os.path.join(SCENARIOS_DIR, "caso4_estres_desbalanceado.json")
        self.assertTrue(os.path.exists(stress_path), f"File not found: {stress_path}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(stress_path, "caso4_estres_desbalanceado")
            self.app.update()

        # Verificar que la UI detecta Modo Estrés ACTIVO
        self.assertTrue(self.obs.stress_mode)
        self.assertEqual(self.app.topbar.switch_stress.get(), 1)
        self.assertEqual(self.app.topbar.btn_recover.cget("state"), "normal")

        # Verificar desbalance en el árbol (> 1)
        max_bf = max(abs(n.balance_factor()) for n in self.obs.tree.inorder())
        self.assertGreater(max_bf, 1, "El árbol en estrés debe estar desbalanceado (|FB| > 1)")

        # Ejecutar Recuperación Global en la GUI
        with patch("Presentation.Components.Molecules.recovery_modal.RecoveryReportModal"):
            self.app.topbar._on_recover_click()
            self.app.update()

        # Verificar que el árbol recuperó el equilibrio AVL (|FB| <= 1)
        self.assertFalse(self.obs.stress_mode)
        self.assertEqual(self.app.topbar.switch_stress.get(), 0)
        self.assertEqual(self.app.topbar.btn_recover.cget("state"), "disabled")

        max_bf_after = max(abs(n.balance_factor()) for n in self.obs.tree.inorder())
        self.assertLessEqual(max_bf_after, 1, "El árbol recuperado debe ser AVL válido (|FB| <= 1)")

        # Verificar que el orden BST se mantuvo intacto
        inorder_keys = [n.get_key() for n in self.obs.tree.inorder()]
        self.assertEqual(inorder_keys, sorted(inorder_keys), "El orden BST debe preservarse")

    def test_caso5_gui_archivo_masivo_subarboles_y_undo(self):
        """
        CASO 5: ARCHIVO MASIVO DE SUBÁRBOLES Y DESHACER en la GUI
        - Topología con dos ramas:
          * Subárbol A (raíz 12): 3 nodos, todos P=1 y antigüedad 98h > T=72h (ELEGIBLE).
          * Subárbol B (raíz 62): 3 nodos (60, 62, 70), antigüedad 98h, pero nodo 70 tiene P=2 (NO ELEGIBLE).
        - En EventsView se ejecuta 'Ejecutar Archivo de Rama':
          * Se archivan los 3 nodos del Subárbol A (10, 12, 14).
          * El Subárbol B permanece intacto en el árbol activo (60, 62, 70).
        - Se ejecuta '↩ Deshacer' en la Topbar:
          * Se restaura el Subárbol A al árbol activo AVL.
        """
        filepath = os.path.join(SCENARIOS_DIR, "caso5_archivo_subarboles.json")
        self.assertTrue(os.path.exists(filepath), f"File not found: {filepath}")

        with patch("tkinter.messagebox.showinfo"):
            self.app.topbar._load_specific_scenario(filepath, "caso5_archivo_subarboles")
            self.app.update()

        events_view = self.app.views["eventos"]
        self.app.switch_view("eventos")
        self.app.update()

        # Verificar estado previo: 7 eventos activos, 0 archivados
        self.assertEqual(len(self.obs.events_dict), 7)
        self.assertEqual(len(self.obs.historic.archived), 0)

        # Configurar umbral T=72h y ejecutar archivo masivo en la GUI
        events_view.archive_threshold_hours = 72
        events_view._handle_execute_archive()
        self.app.update()

        # Subárbol A archivado: nodos 10, 12, 14 en histórico
        self.assertEqual(len(self.obs.events_dict), 4)
        self.assertEqual(len(self.obs.historic.archived), 3)
        for nid in [10, 12, 14]:
            self.assertIn(nid, self.obs.historic.archived)
            self.assertNotIn(nid, self.obs.events_dict)

        # Subárbol B permanece en activo: nodos 60, 62, 70 (más raíz 50)
        for nid in [50, 60, 62, 70]:
            self.assertIn(nid, self.obs.events_dict)

        # Probar DESHACER en la interfaz gráfica (Topbar)
        self.app.topbar._on_undo()
        self.app.update()

        # Estado completamente restaurado
        self.assertEqual(len(self.obs.events_dict), 7)
        self.assertEqual(len(self.obs.historic.archived), 0)
        for nid in [10, 12, 14, 50, 60, 62, 70]:
            self.assertIn(nid, self.obs.events_dict)

    def test_caso6_gui_persistencia_consistencia_y_rechazo(self):
        """
        CASO 6: PERSISTENCIA, CONSISTENCIA Y RECHAZO en la GUI
        - Intentar cargar por Topbar archivos corruptos intencionalmente:
          1. Orden BST violado.
          2. IDs duplicados entre activo e histórico.
          3. Alturas / factores de balance inconsistentes.
          4. Desbalance fuera de {-1, 0, 1} sin modo estrés habilitado.
        - La GUI debe capturar el error, desplegar cuadro de diálogo de error (messagebox.showerror),
          y abortar la carga atómicamente dejando el estado del observatorio intacto.
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

                # La GUI debe haber mostrado el diálogo de error al usuario
                self.assertTrue(mock_err.called, f"Expected showerror dialog for {filename}")
                self.assertFalse(mock_info.called, f"showinfo should NOT be called for invalid {filename}")

                # El observatorio debe haber abortado atómicamente sin mutaciones
                self.assertEqual(
                    len(self.obs.events_dict),
                    events_before,
                    f"Observatory state must remain unmodified after rejected load of {filename}"
                )


if __name__ == "__main__":
    unittest.main()
