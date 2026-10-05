"""
Tests / Presentation / test_map_radius_control.py
Unit tests verifying the MapView interactive radius slider preview and explicit confirmation functionality.
"""

import unittest
from datetime import datetime
import customtkinter as ctk

from Business.observatory import Observatory
from Models.event import Event
from Presentation.Views.map_view import MapView


class TestMapRadiusControl(unittest.TestCase):
    """Verifies that slider drag only previews radius R and clicking button commits it globally."""

    @classmethod
    def setUpClass(cls):
        # Headless root for CustomTkinter widgets
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.obs = Observatory()
        self.map_view = MapView(self.root, observatory=self.obs)

    def test_initial_state_matches_observatory_distance_epicenter(self):
        """Slider and button should initialize to current observatory distance_epicenter (40 km)."""
        self.assertEqual(self.obs.distance_epicenter, 40.0)
        self.assertEqual(self.map_view.radius_var.get(), 40)
        self.assertEqual(self.map_view.btn_apply_r.cget("state"), "disabled")
        self.assertIn("40", self.map_view.btn_apply_r.cget("text"))

    def test_slider_change_previews_without_altering_observatory(self):
        """Changing the slider must update UI preview but leave observatory.distance_epicenter unchanged."""
        self.map_view.slider_r.set(70)
        self.map_view._on_radius_slider_change(70)

        # Global parameter should remain 40.0
        self.assertEqual(self.obs.distance_epicenter, 40.0)

        # Confirmation button should activate with new target value
        self.assertEqual(self.map_view.btn_apply_r.cget("state"), "normal")
        self.assertIn("70", self.map_view.btn_apply_r.cget("text"))

        # Row label should indicate preview mode
        self.assertIn("Previa", self.map_view.lbl_row_radio.cget("text"))

    def test_returning_slider_to_official_resets_button_to_disabled(self):
        """Returning slider to official value disables the button again."""
        self.map_view.slider_r.set(85)
        self.map_view._on_radius_slider_change(85)
        self.assertEqual(self.map_view.btn_apply_r.cget("state"), "normal")

        # Return to 40
        self.map_view.slider_r.set(40)
        self.map_view._on_radius_slider_change(40)
        self.assertEqual(self.map_view.btn_apply_r.cget("state"), "disabled")
        self.assertIn("40", self.map_view.btn_apply_r.cget("text"))
        self.assertIn("Oficial", self.map_view.lbl_row_radio.cget("text"))

    def test_applying_radius_commits_global_parameter_and_updates_associations(self):
        """Clicking confirmation button commits change to observatory and updates replica associations."""
        ev1 = Event(id=1, priority=3, magnitude=6.0, depth=10.0, epicenter=(500.0, 500.0), date_time=datetime(2026, 10, 4, 10, 0), review=0)
        ev2 = Event(id=2, priority=1, magnitude=4.0, depth=10.0, epicenter=(500.0, 560.0), date_time=datetime(2026, 10, 4, 12, 0), review=0)
        self.obs.events_dict[1] = ev1
        self.obs.events_dict[2] = ev2
        self.obs.update_associations()

        self.map_view.inspect_event(ev1)
        self.assertIn("0 en radio R", self.map_view.lbl_row_candidatos.cget("text"))
        self.assertIn("Sin réplicas", self.map_view.lbl_row_referencia.cget("text"))

        # Preview 70 km
        self.map_view.slider_r.set(70)
        self.map_view._on_radius_slider_change(70)
        self.assertEqual(self.obs.distance_epicenter, 40.0)
        self.assertIn("1 en radio R", self.map_view.lbl_row_candidatos.cget("text"))
        self.assertIn("Sin réplicas", self.map_view.lbl_row_referencia.cget("text"))

        # Commit via button handler
        self.map_view._on_apply_global_radius()
        self.assertEqual(self.obs.distance_epicenter, 70.0)
        self.assertEqual(self.map_view.btn_apply_r.cget("state"), "disabled")
        self.assertIn("70", self.map_view.btn_apply_r.cget("text"))
        self.assertIn("Oficial", self.map_view.lbl_row_radio.cget("text"))
        self.assertIn("1 réplicas", self.map_view.lbl_row_referencia.cget("text"))

        # Check undo recording
        last_action = self.obs.undo_stack.actions[-1]
        self.assertEqual(last_action.action_type, "UPDATE_PARAMETER")
        self.assertIn("70.0", last_action.description)


if __name__ == "__main__":
    unittest.main()
