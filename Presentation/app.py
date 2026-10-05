import os
import re
import json
from tkinter import messagebox, simpledialog
import customtkinter as ctk
from Presentation.Components.sidebar import Sidebar
from Presentation.Components.topbar import Topbar
from Presentation.Views.tree_view import TreeView
from Presentation.Views.dashboard_view import DashboardView
from Presentation.Views.map_view import MapView
from Presentation.Views.events_view import EventsView
from Presentation.Views.queries_view import QueriesView

class SismoLabApp(ctk.CTk):
    def __init__(self, observatory):
        # Optimized visual scale for greater readability and interface clarity
        ctk.set_appearance_mode("Dark")
        ctk.set_widget_scaling(1.15)
        ctk.set_window_scaling(1.0)

        super().__init__()
        self.observatory = observatory
        self._last_saved_signature = ""

        # Configure official application icon (taskbar and title)
        ico_path = os.path.join(os.path.dirname(__file__), "Assets", "logo.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # Connect initial persistence: Load the latest saved version instead of demo data
        self._load_latest_version_or_init()

        # Main window configuration (adaptable to laptops and standard screens)
        self.title("SismoLab AVL - Observatorio Sismológico")
        self.geometry("1366x768")
        self.minsize(1024, 660)
        self.configure(fg_color="#070c12")

        # Interceptar el evento de cierre de ventana para alertar si hay cambios sin guardar
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # Main window grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Interactive and compact Left Panel)
        self.sidebar = Sidebar(self, app=self, observatory=self.observatory, width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 2. Right Container (Topbar + Views)
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.grid(row=0, column=1, sticky="nsew")
        self.right_container.grid_columnconfigure(0, weight=1)
        self.right_container.grid_rowconfigure(1, weight=1)

        # 3. Topbar (Simulation Top Bar)
        self.topbar = Topbar(self.right_container, app=self, observatory=self.observatory, height=60)
        self.topbar.grid(row=0, column=0, sticky="ew")

        # 4. Registration and Management of Modular Views
        self.views = {
            "dashboard": DashboardView(self.right_container, app=self, observatory=self.observatory),
            "arboles": TreeView(self.right_container, app=self, observatory=self.observatory),
            "mapa": MapView(self.right_container, app=self, observatory=self.observatory),
            "eventos": EventsView(self.right_container, app=self, observatory=self.observatory),
            "consultas": QueriesView(self.right_container, app=self, observatory=self.observatory),
        }

        self.current_view_key = None
        self.current_view = None

        # Show Dashboard view by default
        self.switch_view("dashboard")

        # Registrar la firma del estado cargado inicialmente como base guardada
        self.capture_saved_state()

    def _load_latest_version_or_init(self):
        """
        Locates and loads the most recently modified persistent version in saved_versions/.
        If no versions exist, initializes a clean scenario without injecting demo data.
        """
        target_dir = getattr(self.observatory, "VERSIONS_DIR", None)
        if not target_dir:
            target_dir = os.path.abspath("saved_versions")
        os.makedirs(target_dir, exist_ok=True)

        json_files = []
        try:
            for f in os.listdir(target_dir):
                if f.lower().endswith(".json"):
                    full_p = os.path.join(target_dir, f)
                    if os.path.isfile(full_p):
                        json_files.append(full_p)
        except Exception:
            pass

        if json_files:
            # Select the most recently saved file
            latest_file = max(json_files, key=os.path.getmtime)
            stem = os.path.splitext(os.path.basename(latest_file))[0]
            ok = False
            try:
                ok, errors = self.observatory.load_scenario_by_topology(latest_file)
            except Exception:
                ok = False

            if not ok:
                try:
                    res = self.observatory.load_scenario_by_insertions(latest_file, adopt_avl=True)
                    ok = bool(res and "avl" in res)
                except Exception:
                    ok = False

            if ok:
                self.observatory.current_scenario_name = stem
                self.observatory.current_scenario_filepath = os.path.abspath(latest_file)
                if hasattr(self.observatory, 'undo_stack') and self.observatory.undo_stack:
                    self.observatory.undo_stack.clear()
            else:
                self.observatory.current_scenario_name = "Sin_titulo"
                self.observatory.current_scenario_filepath = None
        else:
            self.observatory.current_scenario_name = "Sin_titulo"
            self.observatory.current_scenario_filepath = None

    def _get_current_state_signature(self) -> str:
        """Serializa de forma determinista el estado actual para detectar modificaciones."""
        try:
            if hasattr(self.observatory, '_serialize_scenario'):
                data = self.observatory._serialize_scenario()
                data.pop("version_meta", None)
                return json.dumps(data, sort_keys=True, ensure_ascii=False)
        except Exception:
            pass
        return ""

    def capture_saved_state(self):
        """Updates the base signature corresponding to the saved or loaded version."""
        self._last_saved_signature = self._get_current_state_signature()

    def has_unsaved_changes(self) -> bool:
        """Checks whether the observatory has unsaved changes relative to the saved/loaded version."""
        return self._get_current_state_signature() != self._last_saved_signature

    def save_current_scenario(self) -> bool:
        """Saves the current version to disk. If no file is associated, prompts for a name."""
        filepath = getattr(self.observatory, "current_scenario_filepath", None)
        target_dir = getattr(self.observatory, "VERSIONS_DIR", None)
        if not target_dir:
            target_dir = os.path.abspath("saved_versions")
        os.makedirs(target_dir, exist_ok=True)

        if not filepath:
            name = getattr(self.observatory, "current_scenario_name", None)
            if not name or name in ("Sin_titulo", "Demo Activo", "Nuevo_Escenario"):
                prompt = simpledialog.askstring(
                    "Guardar Versión",
                    "Ingresa un nombre para guardar la versión actual:",
                    parent=self
                )
                if not prompt or not prompt.strip():
                    return False
                name = prompt.strip()
            clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name.replace(" ", "_"))
            filepath = os.path.join(target_dir, f"{clean_name}.json")

        try:
            self.observatory.save_scenario(filepath)
            self.capture_saved_state()
            name = os.path.splitext(os.path.basename(filepath))[0]
            if hasattr(self, "topbar") and self.topbar:
                self.topbar.current_scenario_filepath = os.path.abspath(filepath)
                self.topbar.set_scenario_name(name)
            return True
        except Exception as ex:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar la versión actual:\n{ex}")
            return False

    def _on_close_window(self):
        """
        Intercepts the window close event (WM_DELETE_WINDOW).
        If modifications occurred after loading or saving the version,
        prompts the user to save changes before closing.
        """
        if self.has_unsaved_changes():
            current_name = getattr(self.observatory, "current_scenario_name", "Versión Actual")
            resp = messagebox.askyesnocancel(
                "Guardar Cambios Pendientes",
                f"Has realizado modificaciones en '{current_name}'.\n\n¿Deseas guardar la versión actual antes de salir?",
                icon="warning"
            )
            # resp == True  -> Guardar y salir
            # resp == False -> Salir sin guardar
            # resp is None -> Cancel close and remain in application
            if resp is None:
                return
            elif resp is True:
                saved = self.save_current_scenario()
                if not saved:
                    return

        self.destroy()

    def switch_view(self, view_key: str):
        """
        Dynamically switches the active view in the application.
        Allows modular views to be plugged in cleanly.
        """
        if view_key not in self.views:
            return

        # Hide preview if it exists
        if self.current_view is not None:
            self.current_view.grid_remove()

        # Show the new selected view
        self.current_view_key = view_key
        self.current_view = self.views[view_key]
        self.current_view.grid(row=1, column=0, sticky="nsew")

        # Notify the sidebar to update the cyan highlight
        if hasattr(self, "sidebar") and self.sidebar:
            self.sidebar.set_active(view_key)

        # Refresh data of the newly mounted view
        if hasattr(self.current_view, "refresh"):
            self.current_view.refresh()

    def refresh_all(self):
        """Notifies and updates all views and components with the latest state."""
        if hasattr(self, "topbar") and self.topbar:
            self.topbar.refresh()
        if hasattr(self, "sidebar") and self.sidebar:
            self.sidebar.refresh()
        if hasattr(self, "current_view") and hasattr(self.current_view, "refresh"):
            self.current_view.refresh()

    def run(self):
        self.mainloop()
