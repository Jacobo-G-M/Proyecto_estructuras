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
        # Escala visual optimizada para mayor legibilidad y claridad de interfaz
        ctk.set_appearance_mode("Dark")
        ctk.set_widget_scaling(1.15)
        ctk.set_window_scaling(1.0)

        super().__init__()
        self.observatory = observatory
        self._last_saved_signature = ""

        # Configurar icono oficial de la aplicación (barra de tareas y título)
        ico_path = os.path.join(os.path.dirname(__file__), "Assets", "logo.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # Conectar persistencia inicial: Cargar la última versión guardada en lugar de datos demo
        self._load_latest_version_or_init()

        # Configuración principal de la ventana (adaptable a laptops y pantallas estándar)
        self.title("SismoLab AVL - Observatorio Sismológico")
        self.geometry("1366x768")
        self.minsize(1024, 660)
        self.configure(fg_color="#070c12")

        # Interceptar el evento de cierre de ventana para alertar si hay cambios sin guardar
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # Grid principal de la ventana
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Panel Izquierdo Interactivo y compacto)
        self.sidebar = Sidebar(self, app=self, observatory=self.observatory, width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 2. Contenedor Derecho (Topbar + Vistas)
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.grid(row=0, column=1, sticky="nsew")
        self.right_container.grid_columnconfigure(0, weight=1)
        self.right_container.grid_rowconfigure(1, weight=1)

        # 3. Topbar (Barra Superior de Simulación)
        self.topbar = Topbar(self.right_container, app=self, observatory=self.observatory, height=60)
        self.topbar.grid(row=0, column=0, sticky="ew")

        # 4. Registro y Gestión de Vistas Modulares
        self.views = {
            "dashboard": DashboardView(self.right_container, app=self, observatory=self.observatory),
            "arboles": TreeView(self.right_container, app=self, observatory=self.observatory),
            "mapa": MapView(self.right_container, app=self, observatory=self.observatory),
            "eventos": EventsView(self.right_container, app=self, observatory=self.observatory),
            "consultas": QueriesView(self.right_container, app=self, observatory=self.observatory),
        }

        self.current_view_key = None
        self.current_view = None

        # Mostrar por defecto la vista de Dashboard
        self.switch_view("dashboard")

        # Registrar la firma del estado cargado inicialmente como base guardada
        self.capture_saved_state()

    def _load_latest_version_or_init(self):
        """
        Localiza y carga la última versión persistente guardada en saved_versions/
        ordenada por fecha de modificación más reciente. Si no existen versiones,
        inicializa un escenario limpio sin inyectar datos de demostración.
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
            # Seleccionar el archivo guardado más recientemente
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
        """Actualiza la firma base correspondiente a la versión guardada o cargada."""
        self._last_saved_signature = self._get_current_state_signature()

    def has_unsaved_changes(self) -> bool:
        """Verifica si el observatorio tiene cambios respecto a la versión guardada/cargada."""
        return self._get_current_state_signature() != self._last_saved_signature

    def save_current_scenario(self) -> bool:
        """Guarda la versión actual en disco. Si no tiene archivo asociado, solicita nombre."""
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
        Intercepta el evento de cierre de ventana (WM_DELETE_WINDOW).
        Si se han producido modificaciones después de cargar o guardar la versión,
        muestra una alerta preguntando si desea guardar la versión actual.
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
            # resp is None  -> Cancelar cierre y permanecer en la aplicación
            if resp is None:
                return
            elif resp is True:
                saved = self.save_current_scenario()
                if not saved:
                    return

        self.destroy()

    def switch_view(self, view_key: str):
        """
        Cambia dinámicamente la vista activa en la aplicación.
        Permite a cualquier miembro del equipo integrar su pantalla de forma desacoplada.
        """
        if view_key not in self.views:
            return

        # Ocultar la vista previa si existe
        if self.current_view is not None:
            self.current_view.grid_remove()

        # Mostrar la nueva vista seleccionada
        self.current_view_key = view_key
        self.current_view = self.views[view_key]
        self.current_view.grid(row=1, column=0, sticky="nsew")

        # Notificar a la barra lateral para actualizar el resaltado cian
        if hasattr(self, "sidebar") and self.sidebar:
            self.sidebar.set_active(view_key)

        # Refrescar datos de la vista recién montada
        if hasattr(self.current_view, "refresh"):
            self.current_view.refresh()

    def refresh_all(self):
        """Notifica y actualiza todas las vistas y componentes con el estado más reciente."""
        if hasattr(self, "topbar") and self.topbar:
            self.topbar.refresh()
        if hasattr(self, "sidebar") and self.sidebar:
            self.sidebar.refresh()
        if hasattr(self, "current_view") and hasattr(self.current_view, "refresh"):
            self.current_view.refresh()

    def run(self):
        self.mainloop()
