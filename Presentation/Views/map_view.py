"""
Geographic Map View (1000x1000 km) featuring layer toggles, interactive canvas, and inspector panel.
Faithful to the Figma/HTML design using standardized atomic tokens.
"""

import tkinter as tk
import customtkinter as ctk

from Presentation.Components import (
    Card, StyledLabel, StatusDot, PrimaryButton, SecondaryButton,
    CapsuleToggle, Divider
)
from Presentation.Components.theme import (
    BG_ROOT, BG_SURFACE, BG_CARD, BG_INPUT, BG_MUTED, BG_HOVER,
    ACCENT_CYAN, ACCENT_CYAN_HOVER, ACCENT_AMBER,
    BORDER_SUBTLE, BORDER_LINE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_INVERSE,
    WARNING, DANGER, SUCCESS,
    FONT_MAIN, FONT_MONO
)


class MapView(ctk.CTkFrame):
    """
    Geographic Map View · 1000x1000 km.
    Provides 2D spatial visualization for seismic events, monitoring stations, zones,
    configurable coordinate reticle, and seismic event inspector.
    """
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color=BG_ROOT, corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory

        # Layer visibility toggle variables
        self.layer_zones = ctk.BooleanVar(value=True)
        self.layer_stations = ctk.BooleanVar(value=True)
        self.layer_active = ctk.BooleanVar(value=True)
        self.layer_archived = ctk.BooleanVar(value=True)
        self.layer_replicas = ctk.BooleanVar(value=True)

        # Reticle density and radius control variables
        self.grid_density = ctk.StringVar(value="100 km")
        self.radius_var = ctk.IntVar(value=60)
        self.selected_event_id = "EV-1042"

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # ---------------------------------------------------------
        # 1. Main Header Section
        # ---------------------------------------------------------
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        title_section = ctk.CTkFrame(header, fg_color="transparent")
        title_section.pack(side="left")

        ctk.CTkLabel(
            title_section,
            text="PRESENTATION / VIEWS / MAP_VIEW.PY · EXPANDIDO",
            font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
            text_color=ACCENT_CYAN
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_section,
            text="Mapa Geográfico · 1000 × 1000 km",
            font=ctk.CTkFont(family=FONT_MAIN, size=22, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            title_section,
            text="Visor proyectado con retícula cada 100 km, capas conmutables y medición. Render: map_renderer.py.",
            font=ctk.CTkFont(family=FONT_MAIN, size=11),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        header_pills = ctk.CTkFrame(header, fg_color="transparent")
        header_pills.pack(side="right", anchor="s")

        pill_stations = Card(header_pills, corner_radius=6, border_color=BORDER_SUBTLE)
        pill_stations.pack(side="left", padx=(0, 8))
        StyledLabel(pill_stations, text="5 estaciones · link OK", variant="mono", text_color=SUCCESS).pack(padx=10, pady=4)

        pill_counts = Card(header_pills, corner_radius=6, border_color=BORDER_SUBTLE)
        pill_counts.pack(side="left")
        self.lbl_header_counts = StyledLabel(
            pill_counts,
            text="248 activos · 61 archivados",
            variant="mono",
            text_color=TEXT_MUTED
        )
        self.lbl_header_counts.pack(padx=10, pady=4)

        # ---------------------------------------------------------
        # 2. Main Grid Layout (3 Columns)
        # ---------------------------------------------------------
        main_grid = ctk.CTkFrame(container, fg_color="transparent")
        main_grid.pack(fill="both", expand=True)

        main_grid.grid_columnconfigure(0, weight=0)  # Column 1: Layers (260px)
        main_grid.grid_columnconfigure(1, weight=1)  # Column 2: Canvas (Flexible)
        main_grid.grid_columnconfigure(2, weight=0)  # Column 3: Inspector (300px)
        main_grid.grid_rowconfigure(0, weight=1)

        self.left_panel = Card(main_grid, width=260)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.center_panel = Card(main_grid)
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=5)

        self.right_panel = ctk.CTkFrame(main_grid, fg_color="transparent", width=300)
        self.right_panel.grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        self._build_layers_panel()
        self._build_map_canvas()
        self._build_inspector_panel()

        # ---------------------------------------------------------
        # 3. Footer Status Bar
        # ---------------------------------------------------------
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", pady=(12, 0))

        StyledLabel(
            footer,
            text="map_view.py consume Observatory.get_map_snapshot() · toggle_layer() · inspect_quake(id, R) → candidatos",
            variant="mono",
            text_color=TEXT_MUTED
        ).pack(side="left")

        StyledLabel(
            footer,
            text="tooltip (x,y) en vivo · R dibujado · candidatos en amarillo",
            variant="mono",
            text_color=TEXT_MUTED
        ).pack(side="right")

    # =============================================================
    # COLUMN 1: Layers & Reticle Panel
    # =============================================================
    def _build_layers_panel(self):
        header_box = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        header_box.pack(fill="x", padx=14, pady=(14, 8))

        StyledLabel(header_box, text="Capas · Layer Toggles", variant="h3").pack(side="left")
        StyledLabel(header_box, text="map_renderer.py", variant="mono", text_color=TEXT_MUTED).pack(side="right")

        self._create_layer_row(self.left_panel, WARNING, "Zonas", "4 rect · pob/no-pob", self.layer_zones)
        self._create_layer_row(self.left_panel, ACCENT_CYAN, "Estaciones", "5 fijas · S-N/S-C", self.layer_stations)
        self._create_layer_row(self.left_panel, DANGER, "Sismos activos", "radio ∝ M · P1/P2/P3", self.layer_active)
        self._create_layer_row(self.left_panel, TEXT_MUTED, "Archivados", "huecos grises", self.layer_archived)
        self._create_layer_row(self.left_panel, ACCENT_AMBER, "Réplicas / R", "vectores → ref", self.layer_replicas)

        # Reticle density selection
        reticle_box = Card(self.left_panel, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE)
        reticle_box.pack(fill="x", padx=12, pady=(12, 12))

        StyledLabel(reticle_box, text="RETÍCULA", variant="caption").pack(anchor="w", padx=10, pady=(8, 4))

        reticle_btns_box = ctk.CTkFrame(reticle_box, fg_color="transparent")
        reticle_btns_box.pack(anchor="w", padx=10, pady=(2, 10))

        self.grid_buttons = {}
        for density in ["100 km", "50 km", "off"]:
            btn = SecondaryButton(
                reticle_btns_box,
                text=density,
                width=62,
                height=26,
                command=lambda d=density: self._set_grid_density(d)
            )
            btn.pack(side="left", padx=(0, 6))
            self.grid_buttons[density] = btn

        self._set_grid_density("100 km")

    def _create_layer_row(self, master, dot_color: str, title: str, subtitle: str, variable: ctk.BooleanVar):
        """Constructs an individual layer toggle row with indicator dot, titles, and switch."""
        row = Card(master, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE, height=54)
        row.pack(fill="x", padx=12, pady=4)
        row.pack_propagate(False)

        dot = StatusDot(row, width=10, height=10, corner_radius=5, fg_color=dot_color)
        dot.pack(side="left", padx=(12, 8))

        text_box = ctk.CTkFrame(row, fg_color="transparent")
        text_box.pack(side="left", fill="y", pady=5)

        StyledLabel(text_box, text=title, variant="h3").pack(anchor="w")
        StyledLabel(text_box, text=subtitle, variant="caption").pack(anchor="w")

        switch = CapsuleToggle(
            row,
            variable=variable,
            command=self._on_layer_toggle
        )
        switch.pack(side="right", padx=(0, 10))

    def _set_grid_density(self, density: str):
        """Updates the active reticle density state and highlights the corresponding button."""
        self.grid_density.set(density)
        for key, btn in self.grid_buttons.items():
            if key == density:
                btn.configure(
                    fg_color=ACCENT_CYAN,
                    hover_color=ACCENT_CYAN_HOVER,
                    text_color=TEXT_INVERSE,
                    border_width=0
                )
            else:
                btn.configure(
                    fg_color=BG_SURFACE,
                    hover_color=BG_HOVER,
                    text_color=TEXT_MUTED,
                    border_color=BORDER_SUBTLE,
                    border_width=1
                )
        self._on_grid_toggle(density)

    # =============================================================
    # COLUMN 2: Map Canvas & Legend
    # =============================================================
    def _build_map_canvas(self):
        top_bar = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        top_bar.pack(fill="x", padx=14, pady=(12, 8))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        StyledLabel(title_box, text="Plano 0-1000 km", variant="h3").pack(side="left")

        # Dual-pill cursor coordinate display (bg-input and cyan)
        cursor_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        cursor_box.pack(side="right")
      
        coords_pill = Card(cursor_box, fg_color=ACCENT_CYAN, corner_radius=4, border_width=0)
        coords_pill.pack(side="left")
        self.lbl_cursor_coords = StyledLabel(
            coords_pill,
            text="(512.4, 401.7) km",
            variant="mono",
            text_color=TEXT_INVERSE
        )
        self.lbl_cursor_coords.pack(padx=8, pady=3)

        # Main Tkinter canvas for geographic rendering
        self.canvas = tk.Canvas(
            self.center_panel,
            bg="#0a141f",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(4, 6))

        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Bottom legend bar
        legend_card = Card(self.center_panel, fg_color=BG_ROOT, corner_radius=8, border_color=BORDER_SUBTLE)
        legend_card.pack(fill="x", padx=14, pady=(0, 10))

        left_legend = ctk.CTkFrame(legend_card, fg_color="transparent")
        left_legend.pack(side="left", padx=10, pady=4)

        legend_items = [
            ("▭ poblada", WARNING),
            ("▭ no-poblada", TEXT_MUTED),
            ("▲ estación", ACCENT_CYAN),
            ("● activo P3", DANGER),
            ("○ archivado", TEXT_MUTED),
            ("┄ réplica→ref", ACCENT_AMBER)
        ]

        for text, color in legend_items:
            StyledLabel(left_legend, text=text, text_color=color, variant="caption").pack(side="left", padx=5)

    # =============================================================
    # COLUMN 3: Map Inspector & Quick Measurement
    # =============================================================
    def _build_inspector_panel(self):
        # ---------------------------------------------------------
        # Card 1: Seismic Event Inspector
        # ---------------------------------------------------------
        card_inspector = Card(self.right_panel, corner_radius=12)
        card_inspector.pack(fill="x", pady=(0, 14))

        header_inspector = ctk.CTkFrame(card_inspector, fg_color="transparent")
        header_inspector.pack(fill="x", padx=14, pady=(14, 0))

        self.dot_inspector = StatusDot(header_inspector, size=10, fg_color=DANGER)
        self.dot_inspector.pack(side="left", padx=(0, 8))

        self.lbl_inspector_title = StyledLabel(
            header_inspector,
            text=f"Inspección · {self.selected_event_id}",
            variant="h3"
        )
        self.lbl_inspector_title.pack(side="left")

        # Stat Callout Box (Magnitude, Priority, Coordinates, Depth)
        stat_box = Card(card_inspector, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE)
        stat_box.pack(fill="x", padx=14, pady=(12, 8))

        self.lbl_stat_mag = ctk.CTkLabel(
            stat_box,
            text="M 6.1 · P3",
            font=ctk.CTkFont(family=FONT_MONO, size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.lbl_stat_mag.pack(pady=(10, 2))

        self.lbl_stat_coords = StyledLabel(
            stat_box,
            text="(412.0, 388.0) km · 22.4 km prof",
            variant="caption",
            text_color=TEXT_MUTED
        )
        self.lbl_stat_coords.pack(pady=(0, 10))

        # Structured Key-Value inspection table
        table_box = Card(card_inspector, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE)
        table_box.pack(fill="x", padx=14, pady=4)

        self.lbl_row_radio = self._add_table_row(table_box, "Radio R", "60 km dibujado", ACCENT_CYAN)
        self.lbl_row_candidatos = self._add_table_row(table_box, "Candidatos en R", "3 → 1 en amarillo", ACCENT_AMBER)
        self.lbl_row_referencia = self._add_table_row(table_box, "Referencia", "EV-1039 · 42km · 6h", TEXT_PRIMARY)
        self.lbl_row_zona = self._add_table_row(table_box, "Zona", "Z-01 VALLE · POB", WARNING)
        self.lbl_row_estacion = self._add_table_row(table_box, "Estación cerc.", "S-N1 · Δ 18.2 km", TEXT_PRIMARY)
        self.lbl_row_estado = self._add_table_row(table_box, "Estado", "PENDIENTE · arch: no", ACCENT_AMBER, is_last=True)

        # Radius R interactive slider
        slider_box = ctk.CTkFrame(card_inspector, fg_color="transparent")
        slider_box.pack(fill="x", padx=14, pady=(12, 6))

        StyledLabel(slider_box, text="R", variant="mono", text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))

        self.slider_r = ctk.CTkSlider(
            slider_box,
            from_=10,
            to=150,
            number_of_steps=28,
            variable=self.radius_var,
            command=self._on_radius_slider_change,
            height=14,
            button_length=14,
            button_corner_radius=7,
            button_color="#ffffff",
            button_hover_color=ACCENT_CYAN,
            progress_color=ACCENT_CYAN,
            fg_color=BG_MUTED
        )
        self.slider_r.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.lbl_radius_val = StyledLabel(
            slider_box,
            text=f"{self.radius_var.get()}km",
            variant="mono",
            text_color=TEXT_PRIMARY
        )
        self.lbl_radius_val.pack(side="right")

        # "Set as Reference" action trigger button
        self.btn_reference = PrimaryButton(
            card_inspector,
            text="Fijar como Referencia",
            command=self._on_set_reference
        )
        self.btn_reference.pack(fill="x", padx=14, pady=(8, 14))

        # ---------------------------------------------------------
        # Card 2: Quick Measurement (Euclidean Distance & W Window)
        # ---------------------------------------------------------
        card_measure = Card(self.right_panel, corner_radius=12)
        card_measure.pack(fill="x")

        StyledLabel(
            card_measure,
            text="MEDICIÓN RÁPIDA",
            variant="tag",
            text_color=TEXT_MUTED
        ).pack(anchor="w", padx=14, pady=(14, 6))

        measure_box = Card(card_measure, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE)
        measure_box.pack(fill="x", padx=14, pady=(0, 14))

        row1 = ctk.CTkFrame(measure_box, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(8, 3))
        StyledLabel(row1, text="A → B", variant="mono", text_color=TEXT_MUTED).pack(side="left")
        self.lbl_measure_pair = StyledLabel(row1, text="EV-1042 → S-N1", variant="mono", text_color=TEXT_PRIMARY)
        self.lbl_measure_pair.pack(side="right")

        row2 = ctk.CTkFrame(measure_box, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=3)
        StyledLabel(row2, text="Distancia", variant="mono", text_color=TEXT_MUTED).pack(side="left")
        self.lbl_measure_dist = StyledLabel(row2, text="18.2 km", variant="mono", text_color=ACCENT_CYAN)
        self.lbl_measure_dist.pack(side="right")

        row3 = ctk.CTkFrame(measure_box, fg_color="transparent")
        row3.pack(fill="x", padx=12, pady=(3, 8))
        StyledLabel(row3, text="Δt ventana W", variant="mono", text_color=TEXT_MUTED).pack(side="left")
        self.lbl_measure_window = StyledLabel(row3, text="6 h · dentro ✓", variant="mono", text_color=TEXT_PRIMARY)
        self.lbl_measure_window.pack(side="right")

    def _add_table_row(self, master, label: str, value: str, value_color: str, is_last: bool = False):
        """Creates a clean inspection table row with a subtle horizontal divider."""
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(6, 6))

        lbl_k = StyledLabel(row, text=label, variant="mono", text_color=TEXT_MUTED)
        lbl_k.pack(side="left")

        lbl_v = StyledLabel(row, text=value, variant="mono", text_color=value_color)
        lbl_v.pack(side="right")

        if not is_last:
            div = Divider(master, orientation="horizontal")
            div.pack(fill="x")

        return lbl_v

    # =============================================================
    # Event Handlers & Controllers
    # =============================================================
    def _on_radius_slider_change(self, value):
        """Synchronizes slider value with radius labels and triggers map redraw."""
        r_km = int(value)
        self.lbl_radius_val.configure(text=f"{r_km}km")
        self.lbl_row_radio.configure(text=f"{r_km} km dibujado")
        self._redraw_map()

    def _on_set_reference(self):
        """Sets the currently inspected event as the replica reference origin."""
        print(f"[MapView] Reference set: {self.selected_event_id}")

    def inspect_event(self, event_data: dict):
        """
        Dynamically updates the inspector panel with event details.
        event_data: {
            'id': 'EV-1042', 'mag': 6.1, 'p': 3, 'x': 412.0, 'y': 388.0, 'depth': 22.4,
            'candidatos': '3 → 1 en amarillo', 'referencia': 'EV-1039 · 42km · 6h',
            'zona': 'Z-01 VALLE · POB', 'estacion': 'S-N1 · Δ 18.2 km', 'estado': 'PENDIENTE'
        }
        """
        self.selected_event_id = event_data.get("id", "--")
        self.lbl_inspector_title.configure(text=f"Inspección · {self.selected_event_id}")
        self.lbl_stat_mag.configure(text=f"M {event_data.get('mag', 0.0)} · P{event_data.get('p', 1)}")
        self.lbl_stat_coords.configure(
            text=f"({event_data.get('x', 0.0):.1f}, {event_data.get('y', 0.0):.1f}) km · {event_data.get('depth', 0.0)} km prof"
        )
        self.lbl_row_candidatos.configure(text=event_data.get("candidatos", "--"))
        self.lbl_row_referencia.configure(text=event_data.get("referencia", "--"))
        self.lbl_row_zona.configure(text=event_data.get("zona", "--"))
        self.lbl_row_estacion.configure(text=event_data.get("estacion", "--"))
        self.lbl_row_estado.configure(text=event_data.get("estado", "--"))
        self._redraw_map()

    def _on_canvas_resize(self, event):
        """Handles responsive canvas dimensions and triggers re-render."""
        self.canvas_width = event.width
        self.canvas_height = event.height
        self._redraw_map()

    def _on_canvas_motion(self, event):
        """Tracks cursor motion over the canvas and updates coordinate readout in km."""
        pass

    def _on_canvas_click(self, event):
        """Handles canvas click events to inspect earthquake nodes or stations."""
        pass

    def _on_layer_toggle(self):
        """Handles visibility state changes for any of the layer toggles."""
        self._redraw_map()

    def _on_grid_toggle(self, value):
        """Handles changes in the reticle density setting."""
        self._redraw_map()

    def _redraw_map(self):
        """Integration hook with MapRenderer to redraw all active layers."""
        pass

    def refresh(self):
        """Refreshes header metrics and triggers a map re-render."""
        pass