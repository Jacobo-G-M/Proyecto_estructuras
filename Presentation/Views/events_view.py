import customtkinter as ctk

FONT_MAIN = "Segoe UI"

class EventsView(ctk.CTkFrame):
    """
    Vista de Gestión de Eventos · CRUD + Cola.
    Scaffold listo para que el equipo integre el formulario de creación, edición y cola de reportes.
    """
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color="#070c12", corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header, text="SISMOLAB · GESTIÓN DE EVENTOS",
            font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#22d3ee"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header, text="Gestión de Eventos · CRUD + Cola",
            font=ctk.CTkFont(family=FONT_MAIN, size=22, weight="bold"), text_color="#e8eef3"
        ).pack(anchor="w", pady=(2, 0))
        
        ctk.CTkLabel(
            header, text="Registro manual de eventos, administración de la cola de reportes y procesamiento paso a paso.",
            font=ctk.CTkFont(family=FONT_MAIN, size=11), text_color="#8a9bb0"
        ).pack(anchor="w", pady=(2, 0))

        # Tarjeta contenedora
        card = ctk.CTkFrame(container, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=12)
        card.pack(fill="both", expand=True)

        center_box = ctk.CTkFrame(card, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center_box, text="⚡", font=ctk.CTkFont(size=44)).pack(pady=10)
        ctk.CTkLabel(
            center_box, text="Módulo Gestión de Eventos · Listo para Integrar",
            font=ctk.CTkFont(family=FONT_MAIN, size=18, weight="bold"), text_color="#e8eef3"
        ).pack()
        
        ctk.CTkLabel(
            center_box,
            text="Tu equipo puede programar esta vista editando el archivo:\n"
                 "Presentation/Views/events_view.py\n\n"
                 "Aquí se integrarán los formularios de inserción/edición de eventos,\n"
                 "la tabla de eventos activos y los controles para procesar la cola de reportes.",
            font=ctk.CTkFont(family=FONT_MAIN, size=12), text_color="#8a9bb0", justify="center"
        ).pack(pady=12)

    def refresh(self):
        pass
