import customtkinter as ctk
from Presentation.Components.sidebar import Sidebar
from Presentation.Components.topbar import Topbar
from Presentation.Views.tree_view import TreeView
from Presentation.Views.dashboard_view import DashboardView
from Presentation.Views.map_view import MapView
from Presentation.Views.events_view import EventsView
from Presentation.Views.queries_view import QueriesView
from Presentation.Utils.demo_data import load_demo_data

class SismoLabApp(ctk.CTk):
    def __init__(self, observatory):
        # Escala visual global para mejorar la legibilidad y soporte de alta resolución
        ctk.set_widget_scaling(1.15)
        ctk.set_window_scaling(1.0)

        super().__init__()
        self.observatory = observatory

        # Cargar datos operativos de demostración si el catálogo está vacío
        load_demo_data(self.observatory)

        # Configuración principal de la ventana
        self.title("SismoLab AVL - Observatorio Sismológico")
        self.geometry("1440x812")
        self.minsize(1100, 720)
        self.configure(fg_color="#070c12")

        # Grid principal de la ventana
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Panel Izquierdo Interactivo)
        self.sidebar = Sidebar(self, app=self, observatory=self.observatory, width=280)
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
