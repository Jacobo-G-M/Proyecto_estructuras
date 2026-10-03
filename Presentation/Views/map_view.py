import customtkinter as ctk

FONT_MAIN = "Segoe UI"

class MapView(ctk.CTkFrame):
    """
    Vista del Mapa Geográfico · 1000x1000 km.
    Scaffold listo para que el equipo integre el lienzo cartográfico y las estaciones.
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
            header, text="PRESENTATION / VIEWS / MAP_VIEW.PY",
            font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#22d3ee"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header, text="Mapa Geográfico · 1000x1000 km",
            font=ctk.CTkFont(family=FONT_MAIN, size=22, weight="bold"), text_color="#e8eef3"
        ).pack(anchor="w", pady=(2, 0))
        
        ctk.CTkLabel(
            header, text="Visualización bidimensional de estaciones sismológicas, zonas pobladas y epicentros.",
            font=ctk.CTkFont(family=FONT_MAIN, size=11), text_color="#8a9bb0"
        ).pack(anchor="w", pady=(2, 0))

        # Tarjeta contenedora
        card = ctk.CTkFrame(container, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=12)
        card.pack(fill="both", expand=True)

        center_box = ctk.CTkFrame(card, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center_box, text="🗺️", font=ctk.CTkFont(size=44)).pack(pady=10)
        ctk.CTkLabel(
            center_box, text="Módulo Mapa Geográfico · Listo para Integrar",
            font=ctk.CTkFont(family=FONT_MAIN, size=18, weight="bold"), text_color="#e8eef3"
        ).pack()
        
        ctk.CTkLabel(
            center_box,
            text="Tu equipo puede programar esta vista editando el archivo:\n"
                 "Presentation/Views/map_view.py\n\n"
                 "Aquí se integrará el Canvas con el plano cartesiano de 1000x1000 km,\n"
                 "la representación de polígonos de zonas pobladas y las estaciones de monitoreo.",
            font=ctk.CTkFont(family=FONT_MAIN, size=12), text_color="#8a9bb0", justify="center"
        ).pack(pady=12)

    def refresh(self):
        pass
