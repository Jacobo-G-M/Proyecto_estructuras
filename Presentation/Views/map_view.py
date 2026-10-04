"""
Presentation / Views / map_view.py
Geographic Map View (1000x1000 km) featuring layer toggles, interactive canvas, and inspector panel.
Faithful to the Figma/HTML design using standardized atomic tokens.
Connects with MapRenderer for live Cartesian projection, Pan & Zoom camera, and earthquake inspection.
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
from Presentation.Utils.map_renderer import MapRenderer


class MapView(ctk.CTkFrame):
    """
    Geographic Map View · 1000x1000 km.
    Provides 2D spatial visualization for seismic events, monitoring stations, zones,
    configurable coordinate reticle, Pan & Zoom navigation, and dynamic seismic event inspector.
    """
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color=BG_ROOT, corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory

        # Layer visibility toggle variables
        self.layer_zones = ctk.BooleanVar(value=True)
        self.layer_stations = ctk.BooleanVar(value=True)
        self.layer_active = ctk.BooleanVar(value=True)
        self.layer_archived = ctk.BooleanVar(value=False)
        self.layer_replicas = ctk.BooleanVar(value=True)

        # Reticle density and radius control variables
        self.grid_density = ctk.StringVar(value="100 km")
        self.radius_var = ctk.IntVar(value=60)
        self.selected_event = None
        self.selected_station = None
        self.selected_event_id = None

        # Camera Pan & Zoom state (x_min, x_max, y_min, y_max in km)
        self.view_bounds = (0.0, 1000.0, 0.0, 1000.0)
        self.zoom_level = 1.0

        self._build_ui()
        self.refresh()

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
            header, text="SISMOLAB · CARTOGRAFÍA REGIONAL",
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

        ctk.CTkLabel(
            title_section,
            text="Mapa que muestra sismos con retícula cada 100 km, filtros y medición.",
            font=ctk.CTkFont(family=FONT_MAIN, size=11),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(2, 0))

        header_pills = ctk.CTkFrame(header, fg_color="transparent")
        header_pills.pack(side="right", anchor="s")

        pill_stations = Card(header_pills, corner_radius=6, border_color=BORDER_SUBTLE)
        pill_stations.pack(side="left", padx=(0, 8))
        self.lbl_station_count = StyledLabel(pill_stations, text="0 estaciones · sin enlace", variant="mono", text_color=SUCCESS)
        self.lbl_station_count.pack(padx=10, pady=4)

        pill_counts = Card(header_pills, corner_radius=6, border_color=BORDER_SUBTLE)
        pill_counts.pack(side="left")
        self.lbl_header_counts = StyledLabel(
            pill_counts,
            text="0 activos · 0 archivados",
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

        self._build_map_canvas()
        self._build_layers_panel()
        self._build_inspector_panel()

        # ---------------------------------------------------------
        # 3. Footer Status Bar
        # ---------------------------------------------------------
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", pady=(12, 0))

        StyledLabel(
            footer,
            text="Rueda: Zoom · Clic Der / Rueda: Arrastrar · Clic Izq: Inspeccionar sismo",
            variant="mono",
            text_color=ACCENT_CYAN
        ).pack(side="left")
        
    # =============================================================
    # COLUMN 1: Layers & Reticle Panel
    # =============================================================
    def _build_layers_panel(self):
        header_box = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        header_box.pack(fill="x", padx=14, pady=(14, 8))

        StyledLabel(header_box, text="Mostrar elementos", variant="h3").pack(side="left")

        self._create_layer_row(self.left_panel, WARNING, "Zonas", self.layer_zones)
        self._create_layer_row(self.left_panel, ACCENT_CYAN, "Estaciones", self.layer_stations)
        self.toggle_active = self._create_layer_row(self.left_panel, DANGER, "Sismos activos", self.layer_active)
        self._create_layer_row(self.left_panel, TEXT_MUTED, "Archivados", self.layer_archived)
        self.toggle_replicas = self._create_layer_row(self.left_panel, ACCENT_AMBER, "Réplicas / R", self.layer_replicas)

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

    def _create_layer_row(self, master, dot_color: str, title: str, variable: ctk.BooleanVar):
        """Constructs an individual layer toggle row with indicator dot, title, and switch."""
        row = Card(master, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE, height=44)
        row.pack(fill="x", padx=12, pady=3)
        row.pack_propagate(False)

        dot = StatusDot(row, width=8, height=8, corner_radius=4, fg_color=dot_color)
        dot.pack(side="left", padx=(12, 8))

        StyledLabel(row, text=title, variant="h3").pack(side="left")

        switch = CapsuleToggle(
            row,
            variable=variable,
            command=self._on_layer_toggle
        )
        switch.pack(side="right", padx=(0, 10))
        return switch

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
    # COLUMN 2: Map Canvas, Zoom Toolbar & Legend
    # =============================================================
    def _build_map_canvas(self):
        top_bar = ctk.CTkFrame(self.center_panel, fg_color="transparent")
        top_bar.pack(fill="x", padx=14, pady=(12, 8))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left")

        StyledLabel(title_box, text="Plano 0–1000 km · Gran Escala", variant="h3").pack(side="left")

        right_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_box.pack(side="right")

        # Zoom Toolbar Controls
        zoom_pill = Card(right_box, fg_color=BG_SURFACE, corner_radius=6, border_color=BORDER_SUBTLE)
        zoom_pill.pack(side="left", padx=(0, 10))

        self.lbl_zoom = StyledLabel(zoom_pill, text="1.0x", variant="mono", text_color=ACCENT_CYAN)
        self.lbl_zoom.pack(side="left", padx=(8, 6))

        btn_zoom_out = SecondaryButton(
            zoom_pill, text="-", width=26, height=22, corner_radius=4,
            command=self._zoom_out
        )
        btn_zoom_out.pack(side="left", padx=2, pady=2)

        btn_zoom_in = SecondaryButton(
            zoom_pill, text="+", width=26, height=22, corner_radius=4,
            command=self._zoom_in
        )
        btn_zoom_in.pack(side="left", padx=2, pady=2)

        btn_zoom_reset = SecondaryButton(
            zoom_pill, text="⟲", width=26, height=22, corner_radius=4,
            command=self._zoom_reset
        )
        btn_zoom_reset.pack(side="left", padx=(2, 4), pady=2)

        # Dual-pill cursor coordinate display (bg-input and cyan)

        coords_pill = Card(right_box, fg_color=ACCENT_CYAN, corner_radius=4, border_width=0)
        coords_pill.pack(side="left")
        self.lbl_cursor_coords = StyledLabel(
            coords_pill,
            text="(0.0, 0.0) km",
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

        # Canvas event bindings for Zoom, Pan, Motion, Click
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom(1.25, center_km=MapRenderer.px_to_km(e.x, e.y, self.canvas_width, self.canvas_height, self.view_bounds)))
        self.canvas.bind("<Button-5>", lambda e: self._zoom(1.0 / 1.25, center_km=MapRenderer.px_to_km(e.x, e.y, self.canvas_width, self.canvas_height, self.view_bounds)))
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)

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

        self.dot_inspector = StatusDot(header_inspector, size=10, fg_color=TEXT_MUTED)
        self.dot_inspector.pack(side="left", padx=(0, 8))

        self.lbl_inspector_title = StyledLabel(
            header_inspector,
            text="Sin selección",
            variant="h3"
        )
        self.lbl_inspector_title.pack(side="left")

        # Stat Callout Box (Magnitude, Priority, Coordinates, Depth)
        stat_box = Card(card_inspector, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE)
        stat_box.pack(fill="x", padx=14, pady=(12, 8))

        self.lbl_stat_mag = ctk.CTkLabel(
            stat_box,
            text="--",
            font=ctk.CTkFont(family=FONT_MONO, size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.lbl_stat_mag.pack(pady=(10, 2))

        self.lbl_stat_coords = StyledLabel(
            stat_box,
            text="Selecciona un sismo o estación en el mapa",
            variant="caption",
            text_color=TEXT_MUTED
        )
        self.lbl_stat_coords.pack(pady=(0, 10))

        # Structured Key-Value inspection table
        table_box = Card(card_inspector, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE)
        table_box.pack(fill="x", padx=14, pady=4)

        self.lbl_row_radio = self._add_table_row(table_box, "Radio R", "--", ACCENT_CYAN)
        self.lbl_row_candidatos = self._add_table_row(table_box, "Candidatos en R", "--", ACCENT_AMBER)
        self.lbl_row_referencia = self._add_table_row(table_box, "Referencia", "--", TEXT_PRIMARY)
        self.lbl_row_zona = self._add_table_row(table_box, "Zona", "--", WARNING)
        self.lbl_row_estacion = self._add_table_row(table_box, "Estación cerc.", "--", TEXT_PRIMARY)
        self.lbl_row_estado = self._add_table_row(table_box, "Estado", "--", ACCENT_AMBER, is_last=True)

        # Radius R interactive slider
        slider_box = ctk.CTkFrame(card_inspector, fg_color="transparent")
        slider_box.pack(fill="x", padx=14, pady=(12, 14))

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
        self.lbl_measure_pair = StyledLabel(row1, text="--", variant="mono", text_color=TEXT_PRIMARY)
        self.lbl_measure_pair.pack(side="right")

        row2 = ctk.CTkFrame(measure_box, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=3)
        StyledLabel(row2, text="Distancia", variant="mono", text_color=TEXT_MUTED).pack(side="left")
        self.lbl_measure_dist = StyledLabel(row2, text="--", variant="mono", text_color=ACCENT_CYAN)
        self.lbl_measure_dist.pack(side="right")

        row3 = ctk.CTkFrame(measure_box, fg_color="transparent")
        row3.pack(fill="x", padx=12, pady=(3, 8))
        StyledLabel(row3, text="Δt ventana W", variant="mono", text_color=TEXT_MUTED).pack(side="left")
        self.lbl_measure_window = StyledLabel(row3, text="--", variant="mono", text_color=TEXT_PRIMARY)
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
    # Camera Pan & Zoom Handlers
    # =============================================================
    def _zoom_reset(self):
        """Resets camera to full overview (0 to 1000 km)."""
        self.view_bounds = (0.0, 1000.0, 0.0, 1000.0)
        self.zoom_level = 1.0
        self._update_zoom_label()
        self._redraw_map()

    def _zoom(self, factor: float, center_km: tuple = None):
        """Zooms by factor (>1 zooms in, <1 zooms out), optionally keeping center_km fixed."""
        x_min, x_max, y_min, y_max = self.view_bounds
        curr_span_x = x_max - x_min
        curr_span_y = y_max - y_min

        new_span_x = curr_span_x / factor
        new_span_y = curr_span_y / factor

        # Clamp zoom limits: between 1x (span 1000 km) and 12x (span ~80 km)
        if new_span_x >= 1000.0:
            self._zoom_reset()
            return
        if new_span_x < 80.0:
            new_span_x = 80.0
            new_span_y = 80.0

        if center_km is None:
            cx = (x_min + x_max) / 2.0
            cy = (y_min + y_max) / 2.0
        else:
            cx, cy = center_km

        ratio_x = (cx - x_min) / curr_span_x
        ratio_y = (cy - y_min) / curr_span_y

        new_x_min = cx - ratio_x * new_span_x
        new_x_max = new_x_min + new_span_x
        new_y_min = cy - ratio_y * new_span_y
        new_y_max = new_y_min + new_span_y

        # Clamp viewport inside [0, 1000]
        if new_x_min < 0:
            new_x_max += (0 - new_x_min)
            new_x_min = 0.0
        if new_x_max > 1000:
            new_x_min -= (new_x_max - 1000)
            new_x_max = 1000.0

        if new_y_min < 0:
            new_y_max += (0 - new_y_min)
            new_y_min = 0.0
        if new_y_max > 1000:
            new_y_min -= (new_y_max - 1000)
            new_y_max = 1000.0

        self.view_bounds = (max(0.0, new_x_min), min(1000.0, new_x_max), max(0.0, new_y_min), min(1000.0, new_y_max))
        self.zoom_level = 1000.0 / (self.view_bounds[1] - self.view_bounds[0])
        self._update_zoom_label()
        self._redraw_map()

    def _zoom_in(self):
        self._zoom(1.35)

    def _zoom_out(self):
        self._zoom(1.0 / 1.35)

    def _update_zoom_label(self):
        self.lbl_zoom.configure(text=f"{self.zoom_level:.1f}x")

    def _on_mouse_wheel(self, event):
        """Zoom in/out with the mouse wheel centered on the current cursor position."""
        w = getattr(self, "canvas_width", self.canvas.winfo_width())
        h = getattr(self, "canvas_height", self.canvas.winfo_height())
        km_x, km_y = MapRenderer.px_to_km(event.x, event.y, w, h, view_bounds=self.view_bounds)

        factor = 1.25 if event.delta > 0 else (1.0 / 1.25)
        self._zoom(factor, center_km=(km_x, km_y))

    def _on_pan_start(self, event):
        """Records initial drag position for panning."""
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self._pan_start_bounds = self.view_bounds

    def _on_pan_move(self, event):
        """Smoothly pans camera across the map in kilometers based on mouse drag."""
        if not hasattr(self, "_pan_start_bounds"):
            return

        w = getattr(self, "canvas_width", self.canvas.winfo_width())
        h = getattr(self, "canvas_height", self.canvas.winfo_height())
        usable_w = max(1, w - MapRenderer.MARGIN_LEFT - MapRenderer.MARGIN_RIGHT)
        usable_h = max(1, h - MapRenderer.MARGIN_TOP - MapRenderer.MARGIN_BOTTOM)

        dx_px = event.x - self._pan_start_x
        dy_px = event.y - self._pan_start_y

        span_x = self._pan_start_bounds[1] - self._pan_start_bounds[0]
        span_y = self._pan_start_bounds[3] - self._pan_start_bounds[2]

        d_km_x = (dx_px / usable_w) * span_x
        d_km_y = -(dy_px / usable_h) * span_y

        new_x_min = self._pan_start_bounds[0] - d_km_x
        new_x_max = self._pan_start_bounds[1] - d_km_x
        new_y_min = self._pan_start_bounds[2] - d_km_y
        new_y_max = self._pan_start_bounds[3] - d_km_y

        if new_x_min < 0:
            new_x_max += (0 - new_x_min)
            new_x_min = 0.0
        if new_x_max > 1000:
            new_x_min -= (new_x_max - 1000)
            new_x_max = 1000.0

        if new_y_min < 0:
            new_y_max += (0 - new_y_min)
            new_y_min = 0.0
        if new_y_max > 1000:
            new_y_min -= (new_y_max - 1000)
            new_y_max = 1000.0

        self.view_bounds = (max(0.0, new_x_min), min(1000.0, new_x_max), max(0.0, new_y_min), min(1000.0, new_y_max))
        self._redraw_map()

    # =============================================================
    # Event Handlers & Controllers
    # =============================================================
    def _on_radius_slider_change(self, value):
        """Synchronizes slider value with radius labels and triggers map redraw."""
        r_km = int(value)
        self.lbl_radius_val.configure(text=f"{r_km}km")
        self.lbl_row_radio.configure(text=f"{r_km} km dibujado")
        if self.selected_event:
            self._update_candidate_counts()
        self._redraw_map()

    def inspect_event(self, event):
        """
        Dynamically updates the inspector panel with earthquake details and triggers a map re-render.
        Accepts either an Event domain object or an event-like dictionary.
        """
        if event is None:
            return

        self.selected_event = event
        self.selected_station = None

        eid = getattr(event, "id", None) or event.get("id", "--")
        mag = float(getattr(event, "magnitude", None) or event.get("magnitude", 0.0))
        priority = int(getattr(event, "priority", None) or event.get("priority", 1))
        depth = float(getattr(event, "depth", None) or event.get("depth", 0.0))
        epicenter = getattr(event, "epicenter", None) or event.get("epicenter", (0.0, 0.0))
        state = getattr(event, "attention_state", None) or event.get("attention_state", "Pending")
        status = getattr(event, "status", None) or event.get("status", "Active")

        self.selected_event_id = str(eid)
        self.lbl_inspector_title.configure(text=f"Inspección · EV-{eid}")

        # Priority indicator color
        if priority >= 3:
            dot_color = DANGER
        elif priority == 2:
            dot_color = WARNING
        else:
            dot_color = SUCCESS
        self.dot_inspector.configure(fg_color=dot_color)

        self.lbl_stat_mag.configure(text=f"M {mag:.1f} · P{priority}")
        self.lbl_stat_coords.configure(text=f"({epicenter[0]:.1f}, {epicenter[1]:.1f}) km · {depth:.1f} km prof")

        # Closest station detection
        stations = getattr(self.observatory, "stations", []) if self.observatory else []
        closest_st, st_dist = MapRenderer.find_nearest_station(epicenter[0], epicenter[1], stations)

        if closest_st:
            st_text = f"{closest_st.name} · Δ {st_dist:.1f} km"
            self.lbl_measure_pair.configure(text=f"EV-{eid} → {closest_st.name}")
            self.lbl_measure_dist.configure(text=f"{st_dist:.1f} km")
        else:
            st_text = "Sin estaciones registradas"
            self.lbl_measure_pair.configure(text=f"EV-{eid} → --")
            self.lbl_measure_dist.configure(text="--")

        self.lbl_row_estacion.configure(text=st_text)

        # Zone detection
        zone_name = "Fuera de zona delimitada"
        if self.observatory and self.observatory.geographical_map:
            for z in self.observatory.geographical_map.zones:
                if z.contains(epicenter[0], epicenter[1]):
                    zone_name = f"{z.name} · {'POB' if z.is_populated else 'NO-POB'}"
                    break
        self.lbl_row_zona.configure(text=zone_name)

        # Dynamic association & replica lookup
        ref_text = "Sin réplicas (origen)"
        if self.observatory and hasattr(self.observatory, "associations") and self.observatory.associations:
            for assoc in self.observatory.associations:
                reps = getattr(assoc, "referenced_by", [])
                if any(getattr(r, "id", None) == eid for r in reps):
                    parent = assoc.chosen_reference
                    if parent:
                        p_dist = MapRenderer.distance_km(parent.epicenter, epicenter)
                        dt_h = 0.0
                        if hasattr(event, "date_time") and hasattr(parent, "date_time") and event.date_time and parent.date_time:
                            dt_h = abs((event.date_time - parent.date_time).total_seconds()) / 3600.0
                        ref_text = f"Réplica EV-{parent.id} · {p_dist:.1f}km"
                    break
                elif getattr(assoc.chosen_reference, "id", None) == eid:
                    if reps:
                        ref_text = f"Referencia ({len(reps)} réplicas)"
                    break

        self.lbl_row_referencia.configure(text=ref_text)
        self.lbl_row_estado.configure(text=f"{state.upper()} · arch: {'sí' if status == 'Archived' else 'no'}")

        # Elapsed time window W against simulation clock
        sim_clock = getattr(self.observatory, "clock_simulation", None) if self.observatory else None
        ev_dt = getattr(event, "date_time", None)
        max_w = getattr(self.observatory, "max_time", 48.0) if self.observatory else 48.0
        if sim_clock and ev_dt:
            delta_h = max(0.0, (sim_clock - ev_dt).total_seconds() / 3600.0)
            in_w = "dentro ✓" if delta_h <= max_w else "fuera ✗"
            self.lbl_measure_window.configure(text=f"{delta_h:.1f} h · {in_w}")
        else:
            self.lbl_measure_window.configure(text="--")

        self.lbl_row_radio.configure(text=f"{self.radius_var.get()} km dibujado")
        self._update_candidate_counts()
        self._redraw_map()

    def inspect_station(self, station):
        """
        Dynamically updates the inspector panel with monitoring station details.
        """
        if station is None:
            return

        self.selected_station = station
        self.selected_event = None
        self.selected_event_id = None

        sid = getattr(station, "id", None)
        sname = getattr(station, "name", f"S-{sid}")
        coords = getattr(station, "coords", (0.0, 0.0))

        self.lbl_inspector_title.configure(text=f"Estación · {sname}")
        self.dot_inspector.configure(fg_color=ACCENT_CYAN)

        self.lbl_stat_mag.configure(text=f"{sname} · ID {sid}")
        self.lbl_stat_coords.configure(text=f"({coords[0]:.1f}, {coords[1]:.1f}) km · Monitoreo")

        # Zone detection
        zone_name = "Fuera de zona delimitada"
        if self.observatory and self.observatory.geographical_map:
            for z in self.observatory.geographical_map.zones:
                if z.contains(coords[0], coords[1]):
                    zone_name = f"{z.name} · {'POB' if z.is_populated else 'NO-POB'}"
                    break
        self.lbl_row_zona.configure(text=zone_name)

        # Nearest active event to this station
        active_events = [ev for ev in self.observatory.events_dict.values() if ev.status == "Active"] if self.observatory else []
        closest_ev = MapRenderer.find_nearest_event(coords[0], coords[1], active_events)
        if closest_ev:
            ev_dist = MapRenderer.distance_km(coords, closest_ev.epicenter)
            self.lbl_row_estacion.configure(text=f"EV-{closest_ev.id} · Δ {ev_dist:.1f} km")
            self.lbl_measure_pair.configure(text=f"{sname} → EV-{closest_ev.id}")
            self.lbl_measure_dist.configure(text=f"{ev_dist:.1f} km")
        else:
            self.lbl_row_estacion.configure(text="Sin sismos cercanos")
            self.lbl_measure_pair.configure(text=f"{sname} → --")
            self.lbl_measure_dist.configure(text="--")

        self.lbl_row_radio.configure(text="N/A (Estación)")
        rep_count = len(getattr(station, "my_reports", []))
        self.lbl_row_candidatos.configure(text=f"{rep_count} reportes emitidos")
        self.lbl_row_referencia.configure(text=f"Coords ({coords[0]:.1f}, {coords[1]:.1f})")
        self.lbl_row_estado.configure(text="OPERATIVA · link OK")
        self.lbl_measure_window.configure(text="Enlace activo ✓")

        self._redraw_map()

    def _clear_inspector(self):
        """Clears inspector panel to empty state when no event or station is selected."""
        self.selected_event = None
        self.selected_station = None
        self.selected_event_id = None
        self.lbl_inspector_title.configure(text="Sin selección")
        self.dot_inspector.configure(fg_color=TEXT_MUTED)
        self.lbl_stat_mag.configure(text="--")
        self.lbl_stat_coords.configure(text="Selecciona un sismo o estación en el mapa")
        self.lbl_row_radio.configure(text="--")
        self.lbl_row_candidatos.configure(text="--")
        self.lbl_row_referencia.configure(text="--")
        self.lbl_row_zona.configure(text="--")
        self.lbl_row_estacion.configure(text="--")
        self.lbl_row_estado.configure(text="--")
        self.lbl_measure_pair.configure(text="--")
        self.lbl_measure_dist.configure(text="--")
        self.lbl_measure_window.configure(text="--")

    def _update_header_counts(self):
        """Updates header metrics dynamically based on current observatory state."""
        if not hasattr(self, "lbl_station_count") or not hasattr(self, "lbl_header_counts"):
            return

        stations = getattr(self.observatory, "stations", []) if self.observatory else []
        active_events = [ev for ev in self.observatory.events_dict.values() if ev.status == "Active"] if self.observatory else []
        archived_count = len(self.observatory.historic.archived) if (self.observatory and self.observatory.historic and hasattr(self.observatory.historic, "archived")) else 0

        st_status = "link OK" if len(stations) > 0 else "sin enlace"
        self.lbl_station_count.configure(text=f"{len(stations)} estaciones · {st_status}")
        self.lbl_header_counts.configure(text=f"{len(active_events)} activos · {archived_count} archivados")

    def _update_candidate_counts(self):
        """Calculates and updates candidate earthquakes inside radius R."""
        if not self.selected_event or not self.observatory:
            self.lbl_row_candidatos.configure(text="0 en radio R")
            return

        cx, cy = self.selected_event.epicenter
        r_km = self.radius_var.get()
        cands = 0

        for other in self.observatory.events_dict.values():
            if other.id != self.selected_event.id and other.status == "Active":
                if MapRenderer.distance_km((cx, cy), other.epicenter) <= r_km:
                    cands += 1

        self.lbl_row_candidatos.configure(text=f"{cands} en radio R")

    def _on_canvas_resize(self, event):
        """Handles responsive canvas dimensions and triggers re-render."""
        self.canvas_width = event.width
        self.canvas_height = event.height
        self._redraw_map()

    def _on_canvas_motion(self, event):
        """Tracks cursor motion over the canvas and updates real-time coordinate readout in km."""
        w = getattr(self, "canvas_width", self.canvas.winfo_width())
        h = getattr(self, "canvas_height", self.canvas.winfo_height())
        km_x, km_y = MapRenderer.px_to_km(event.x, event.y, w, h, view_bounds=self.view_bounds)
        self.lbl_cursor_coords.configure(text=f"({km_x:.1f}, {km_y:.1f}) km")

    def _on_canvas_click(self, event):
        """Handles canvas click events to inspect earthquake nodes or stations."""
        w = getattr(self, "canvas_width", self.canvas.winfo_width())
        h = getattr(self, "canvas_height", self.canvas.winfo_height())
        km_x, km_y = MapRenderer.px_to_km(event.x, event.y, w, h, view_bounds=self.view_bounds)

        if not self.observatory:
            return

        tolerance_km = max(10.0, 35.0 / self.zoom_level)
        candidates = []

        # 1. Active earthquakes
        if self.layer_active.get():
            active_events = [ev for ev in self.observatory.events_dict.values() if ev.status == "Active"]
            closest_ev = MapRenderer.find_nearest_event(km_x, km_y, active_events, max_dist_km=tolerance_km)
            if closest_ev:
                dist = MapRenderer.distance_km((km_x, km_y), closest_ev.epicenter)
                candidates.append((dist, "event", closest_ev))

        # 2. Archived earthquakes
        if self.layer_archived.get() and self.observatory.historic and hasattr(self.observatory.historic, "archived"):
            arch_events = list(self.observatory.historic.archived.values())
            closest_arch = MapRenderer.find_nearest_event(km_x, km_y, arch_events, max_dist_km=tolerance_km)
            if closest_arch:
                dist = MapRenderer.distance_km((km_x, km_y), closest_arch.epicenter)
                candidates.append((dist, "event", closest_arch))

        # 3. Monitoring stations
        if self.layer_stations.get():
            stations = getattr(self.observatory, "stations", []) or []
            closest_st, st_dist = MapRenderer.find_nearest_station(km_x, km_y, stations, max_dist_km=tolerance_km)
            if closest_st:
                candidates.append((st_dist, "station", closest_st))

        if candidates:
            candidates.sort(key=lambda c: c[0])
            best_type, best_item = candidates[0][1], candidates[0][2]
            if best_type == "event":
                self.inspect_event(best_item)
            elif best_type == "station":
                self.inspect_station(best_item)

    def _on_layer_toggle(self):
        """Handles visibility state changes for any of the layer toggles."""
        # When active earthquakes are turned off, automatically turn off and lock replicas
        if not self.layer_active.get():
            self.layer_replicas.set(False)
            if hasattr(self, "toggle_replicas"):
                self.toggle_replicas.set(False)
                self.toggle_replicas.set_enabled(False)
        else:
            # Re-enable the replicas toggle so user can interact with it again
            if hasattr(self, "toggle_replicas"):
                self.toggle_replicas.set_enabled(True)

        self._redraw_map()

    def _on_grid_toggle(self, value):
        """Handles changes in the reticle density setting."""
        self._redraw_map()

    def _redraw_map(self):
        """Integration hook with MapRenderer to redraw all active layers."""
        if not hasattr(self, "canvas"):
            return

        w = getattr(self, "canvas_width", self.canvas.winfo_width())
        h = getattr(self, "canvas_height", self.canvas.winfo_height())

        zones = []
        stations = []
        active_events = []
        archived_events = []

        if self.observatory:
            if self.observatory.geographical_map:
                zones = self.observatory.geographical_map.zones
            stations = self.observatory.stations or []
            active_events = [ev for ev in self.observatory.events_dict.values() if ev.status == "Active"]
            if self.observatory.historic and hasattr(self.observatory.historic, "archived"):
                archived_events = list(self.observatory.historic.archived.values())

        self._update_header_counts()

        MapRenderer.render(
            canvas=self.canvas,
            canvas_w=w,
            canvas_h=h,
            zones=zones,
            stations=stations,
            active_events=active_events,
            archived_events=archived_events,
            grid_density=self.grid_density.get(),
            show_zones=self.layer_zones.get(),
            show_stations=self.layer_stations.get(),
            show_active=self.layer_active.get(),
            show_archived=self.layer_archived.get(),
            show_replicas=self.layer_replicas.get(),
            selected_event=self.selected_event,
            selected_station_id=self.selected_station.id if self.selected_station else None,
            radius_km=self.radius_var.get(),
            view_bounds=self.view_bounds
        )

    def refresh(self):
        """Refreshes header metrics and triggers a map re-render."""
        self._update_header_counts()

        # If previous selected event still exists, re-inspect it
        if self.selected_event and self.observatory:
            all_events = dict(self.observatory.events_dict)
            if self.observatory.historic and hasattr(self.observatory.historic, "archived"):
                all_events.update(self.observatory.historic.archived)
            if self.selected_event.id in all_events:
                self.inspect_event(all_events[self.selected_event.id])
                return

        # If previous selected station still exists, re-inspect it
        if self.selected_station and self.observatory:
            stations = getattr(self.observatory, "stations", []) or []
            for st in stations:
                if st.id == self.selected_station.id:
                    self.inspect_station(st)
                    return

        # Fallback to inspecting highest priority active event, or first station
        if self.observatory and self.observatory.events_dict:
            active_events = [ev for ev in self.observatory.events_dict.values() if ev.status == "Active"]
            if active_events:
                active_events.sort(key=lambda ev: (-getattr(ev, "priority", 1), -getattr(ev, "magnitude", 0.0)))
                self.inspect_event(active_events[0])
                return

        if self.observatory and getattr(self.observatory, "stations", []):
            self.inspect_station(self.observatory.stations[0])
            return

        self._clear_inspector()
        self._redraw_map()