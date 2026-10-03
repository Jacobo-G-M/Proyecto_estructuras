import customtkinter as ctk
from Presentation.Components.sidebar import Sidebar
from Presentation.Components.topbar import Topbar
from Presentation.Views.tree_view import TreeView
from Presentation.Utils.demo_data import load_demo_data

class SismoLabApp(ctk.CTk):
    def __init__(self, observatory):
        super().__init__()
        self.observatory = observatory

        # Cargar datos operativos de demostración si el catálogo está vacío
        load_demo_data(self.observatory)

        # Configuración principal de la ventana
        self.title("SismoLab AVL - Observatorio Sismológico")
        self.geometry("1440x812")
        self.minsize(1100, 720)
        self.configure(fg_color="#070c12")

        # Grid de la ventana
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Panel Izquierdo conectado)
        self.sidebar = Sidebar(self, app=self, observatory=self.observatory, width=280)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Contenedor derecho (Topbar + Vistas)
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.grid(row=0, column=1, sticky="nsew")
        self.right_container.grid_columnconfigure(0, weight=1)
        self.right_container.grid_rowconfigure(1, weight=1)

        # 2. Topbar (Barra Superior conectada)
        self.topbar = Topbar(self.right_container, app=self, observatory=self.observatory, height=60)
        self.topbar.grid(row=0, column=0, sticky="ew")

        # 3. Vista Principal (TreeView conectado)
        self.current_view = TreeView(self.right_container, app=self, observatory=self.observatory)
        self.current_view.grid(row=1, column=0, sticky="nsew")

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
