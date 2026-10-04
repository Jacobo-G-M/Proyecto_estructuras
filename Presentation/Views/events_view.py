import math
from datetime import datetime
import customtkinter as ctk

from Models.station import Station
from Models.report import Report
from Presentation.Components.theme import (
    FONT_MAIN, FONT_MONO,
    BG_ROOT, BG_SURFACE, BG_SURFACE_ALT,
    BORDER_SUBTLE, BORDER_STRONG, BORDER_FOCUS,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_INVERSE,
    ACCENT_CYAN, ACCENT_CYAN_HOVER,
    SUCCESS, WARNING, DANGER, INFO,
    RADIUS_SM, RADIUS_MD, RADIUS_LG
)
from Presentation.Components import (
    Card, PrimaryButton, SecondaryButton, DangerButton, GhostButton,
    StatusBadge, BadgeVariant
)

class EventsView(ctk.CTkFrame):
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color=BG_ROOT, corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory

        # Variables de control
        self.active_catalog_tab = "activos"
        self.burst_running = False
        self.burst_speed_ms = 400
        self.archive_threshold_hours = 72

        # Cargar reportes de demostración en la cola si está vacía
        self._ensure_demo_queue()

        # Construir UI
        self._build_ui()
        self.refresh()

    # =========================================================================
    # CONSTRUCCIÓN DE LA INTERFAZ
    # =========================================================================

    def _build_ui(self):
        # Contenedor con scroll vertical para adaptarse a cualquier resolución
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Encabezado de la Vista
        self._build_header(self.scroll_container)

        # 2. Grid de 3 Columnas
        columns_grid = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        columns_grid.pack(fill="both", expand=True, pady=(0, 15))
        columns_grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="col_events")

        # Columna 1: Formulario CRUD
        self.col_form = self._build_crud_form(columns_grid)
        self.col_form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Columna 2: Gestor de Ráfagas FIFO
        self.col_queue = self._build_queue_manager(columns_grid)
        self.col_queue.grid(row=0, column=1, sticky="nsew", padx=4)

        # Columna 3: Archivo de Subárboles y Catálogos
        self.col_archive = self._build_archive_panel(columns_grid)
        self.col_archive.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        # 3. Barra de Estado / Footer
        self._build_footer(self.scroll_container)

    # -------------------------------------------------------------------------
    # 1. Encabezado
    # -------------------------------------------------------------------------
    def _build_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        lbl_title = ctk.CTkLabel(
            header_frame,
            text="Gestión de Eventos",
            font=ctk.CTkFont(family=FONT_MAIN, size=22, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        lbl_title.pack(anchor="w", pady=(2, 0))

    # -------------------------------------------------------------------------
    # Columna 1: Formulario de Evento · CRUD
    # -------------------------------------------------------------------------
    def _build_crud_form(self, parent) -> ctk.CTkFrame:
        card = Card(parent, fg_color="#0e1620", border_color="#1e2d3d", corner_radius=12)
        card.pack_propagate(True)

        # Header de tarjeta
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 10))

        lbl_card_title = ctk.CTkLabel(
            header, text="Formulario de Evento",
            font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"), text_color=TEXT_PRIMARY
        )
        lbl_card_title.pack(side="left")

        self.badge_valid = ctk.CTkLabel(
            header, text="✓ válido",
            font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
            text_color=SUCCESS, fg_color="#0c281a", corner_radius=4
        )
        self.badge_valid.pack(side="right", ipadx=6, ipady=2)

        # Campos de entrada
        form_body = ctk.CTkFrame(card, fg_color="transparent")
        form_body.pack(fill="x", padx=16, pady=4)

        # 1. ID
        self.entry_id = self._create_form_row(form_body, "ID", "1 – 999999", "1043", ACCENT_CYAN)
        self.entry_id.bind("<KeyRelease>", lambda e: self._on_form_change())

        # 2. Magnitud M
        self.entry_mag = self._create_form_row(form_body, "Magnitud M", "-2.0 a 10.0", "5.4", ACCENT_CYAN)
        self.entry_mag.bind("<KeyRelease>", lambda e: self._on_form_change())

        # 3. Profundidad
        self.entry_depth = self._create_form_row(form_body, "Profundidad", "0.0 – 700.0 km", "12.5", ACCENT_CYAN)
        self.entry_depth.bind("<KeyRelease>", lambda e: self._on_form_change())

        # 4. Coord X
        self.entry_x = self._create_form_row(form_body, "Coord X", "0.0 – 1000.0", "412.0", ACCENT_CYAN)
        self.entry_x.bind("<KeyRelease>", lambda e: self._on_form_change())

        # 5. Coord Y
        self.entry_y = self._create_form_row(form_body, "Coord Y", "0.0 – 1000.0", "388.0", ACCENT_CYAN)
        self.entry_y.bind("<KeyRelease>", lambda e: self._on_form_change())

        # 6. Estación (OptionMenu)
        row_station = ctk.CTkFrame(form_body, fg_color="transparent")
        row_station.pack(fill="x", pady=3)
        lbls_st = ctk.CTkFrame(row_station, fg_color="transparent")
        lbls_st.pack(fill="x")
        ctk.CTkLabel(lbls_st, text="Estación", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_SECONDARY).pack(side="left")
        self.lbl_station_count = ctk.CTkLabel(lbls_st, text="5 fijas", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED)
        self.lbl_station_count.pack(side="right")

        station_names = [st.name for st in getattr(self.observatory, 'stations', [])] or ["S-N1", "S-N2", "S-C1", "S-S1", "S-E1"]
        self.option_station = ctk.CTkOptionMenu(
            row_station,
            values=station_names,
            fg_color="#101922",
            button_color="#1a2736",
            button_hover_color="#24384e",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            corner_radius=RADIUS_SM,
            height=30
        )
        self.option_station.pack(fill="x", pady=(2, 0))

        # 7. Fecha y Hora
        row_dt = ctk.CTkFrame(form_body, fg_color="transparent")
        row_dt.pack(fill="x", pady=3)
        lbls_dt = ctk.CTkFrame(row_dt, fg_color="transparent")
        lbls_dt.pack(fill="x")
        ctk.CTkLabel(lbls_dt, text="Fecha (UTC)", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_SECONDARY).pack(side="left")
        ctk.CTkLabel(lbls_dt, text="Hora (UTC)", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_SECONDARY).pack(side="right", padx=10)

        inputs_dt = ctk.CTkFrame(row_dt, fg_color="transparent")
        inputs_dt.pack(fill="x", pady=(2, 0))
        inputs_dt.grid_columnconfigure((0, 1), weight=1, uniform="dt")

        f_date = ctk.CTkFrame(inputs_dt, fg_color="transparent")
        f_date.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        btn_d_down = ctk.CTkButton(f_date, text="◀", width=20, fg_color="#1a2736", hover_color="#24384e", text_color="#fff", command=lambda: self._step_datetime(days=-1))
        btn_d_down.pack(side="left")
        self.entry_date = ctk.CTkEntry(f_date, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, text_color=TEXT_PRIMARY, font=ctk.CTkFont(family=FONT_MONO, size=11), height=30)
        self.entry_date.pack(side="left", fill="x", expand=True, padx=2)
        btn_d_up = ctk.CTkButton(f_date, text="▶", width=20, fg_color="#1a2736", hover_color="#24384e", text_color="#fff", command=lambda: self._step_datetime(days=1))
        btn_d_up.pack(side="left")

        f_time = ctk.CTkFrame(inputs_dt, fg_color="transparent")
        f_time.grid(row=0, column=1, sticky="ew", padx=(2, 0))
        btn_t_down = ctk.CTkButton(f_time, text="◀", width=20, fg_color="#1a2736", hover_color="#24384e", text_color="#fff", command=lambda: self._step_datetime(hours=-1))
        btn_t_down.pack(side="left")
        self.entry_time = ctk.CTkEntry(f_time, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, text_color=TEXT_PRIMARY, font=ctk.CTkFont(family=FONT_MONO, size=11), height=30)
        self.entry_time.pack(side="left", fill="x", expand=True, padx=2)
        btn_t_up = ctk.CTkButton(f_time, text="▶", width=20, fg_color="#1a2736", hover_color="#24384e", text_color="#fff", command=lambda: self._step_datetime(hours=1))
        btn_t_up.pack(side="left")

        # 8. Prioridad Calculada (Display)
        row_p = ctk.CTkFrame(form_body, fg_color="transparent")
        row_p.pack(fill="x", pady=3)
        lbls_p = ctk.CTkFrame(row_p, fg_color="transparent")
        lbls_p.pack(fill="x")
        ctk.CTkLabel(lbls_p, text="Prioridad", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_SECONDARY).pack(side="left")

        self.lbl_p_calc = ctk.CTkLabel(
            row_p,
            text="Alto",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color=ACCENT_CYAN,
            fg_color="#101922",
            corner_radius=RADIUS_SM,
            height=30,
            anchor="w",
            padx=10
        )
        self.lbl_p_calc.pack(fill="x", pady=(2, 0))

        # Mensaje de retroalimentación de formulario
        self.lbl_form_msg = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(family=FONT_MAIN, size=11), text_color=TEXT_MUTED
        )
        self.lbl_form_msg.pack(fill="x", padx=16, pady=(4, 0))

        # Botones de Acción (Fila 1)
        btn_grid1 = ctk.CTkFrame(card, fg_color="transparent")
        btn_grid1.pack(fill="x", padx=16, pady=(8, 4))
        btn_grid1.grid_columnconfigure((0, 1), weight=1, uniform="crud1")

        self.btn_create = PrimaryButton(
            btn_grid1,
            text="Crear",
            command=self._handle_create_event
        )
        self.btn_create.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_edit = SecondaryButton(
            btn_grid1,
            text="Modificar / Corregir",
            command=self._handle_edit_event
        )
        self.btn_edit.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Botones de Acción (Fila 2)
        btn_grid2 = ctk.CTkFrame(card, fg_color="transparent")
        btn_grid2.pack(fill="x", padx=16, pady=(0, 10))
        btn_grid2.grid_columnconfigure((0, 1, 2), weight=1, uniform="crud2")

        btn_clear = GhostButton(
            btn_grid2,
            text="Limpiar",
            command=self._clear_form
        )
        btn_clear.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        btn_review = ctk.CTkButton(
            btn_grid2,
            text="✓ Marcar Revisado",
            fg_color="transparent",
            text_color=SUCCESS,
            border_color=SUCCESS,
            border_width=1,
            hover_color="#0c281a",
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            height=32,
            corner_radius=RADIUS_SM,
            command=self._handle_mark_reviewed
        )
        btn_review.grid(row=0, column=1, sticky="ew", padx=3)

        btn_delete = DangerButton(
            btn_grid2,
            text="Eliminar",
            height=32,
            command=self._handle_delete_event
        )
        btn_delete.grid(row=0, column=2, sticky="ew", padx=(3, 0))



        return card

    def _create_form_row(self, parent, label_text: str, range_text: str, default_val: str, range_color: str) -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

        lbls = ctk.CTkFrame(row, fg_color="transparent")
        lbls.pack(fill="x")
        ctk.CTkLabel(lbls, text=label_text, font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_SECONDARY).pack(side="left")
        ctk.CTkLabel(lbls, text=range_text, font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=range_color).pack(side="right")

        entry = ctk.CTkEntry(
            row,
            fg_color="#0b131c",
            border_color="#1e2d3d",
            border_width=1,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            corner_radius=RADIUS_SM,
            height=30
        )
        entry.insert(0, default_val)
        entry.pack(fill="x", pady=(2, 0))
        return entry

    # ---------------------------------------------------------
    # Columna 2: Cola FIFO · Gestor de Ráfagas
    # ---------------------------------------------------------
    def _build_queue_manager(self, parent) -> ctk.CTkFrame:
        card = Card(parent, fg_color="#0e1620", border_color="#1e2d3d", corner_radius=12)

        # Header de tarjeta
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 10))

        ctk.CTkLabel(
            header, text="Gestor de reportes",
            font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(side="left")

        self.lbl_queue_count = ctk.CTkLabel(
            header, text="0 en cola",
            font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
            text_color=WARNING, fg_color="#2a1608", corner_radius=4
        )
        self.lbl_queue_count.pack(side="right", ipadx=6, ipady=2)

        # Botones de control de procesamiento
        btn_grid = ctk.CTkFrame(card, fg_color="transparent")
        btn_grid.pack(fill="x", padx=16, pady=4)
        btn_grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="queue_ctrl")

        self.btn_step = PrimaryButton(
            btn_grid,
            text="▶ Paso a Paso",
            height=34,
            command=self._handle_step_queue
        )
        self.btn_step.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_burst = ctk.CTkButton(
            btn_grid,
            text="● Continuo",
            fg_color=SUCCESS,
            hover_color="#27ae60",
            text_color="#ffffff",
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            height=34,
            corner_radius=RADIUS_SM,
            command=self._handle_toggle_burst
        )
        self.btn_burst.grid(row=0, column=1, sticky="ew", padx=2)

        self.btn_pause = SecondaryButton(
            btn_grid,
            text="❚❚ Pausar",
            height=34,
            command=self._handle_pause_burst
        )
        self.btn_pause.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        # Control de velocidad
        speed_frame = ctk.CTkFrame(card, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, corner_radius=RADIUS_MD)
        speed_frame.pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(
            speed_frame, text="Velocidad",
            font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_SECONDARY
        ).pack(side="left", padx=10, pady=8)

        self.slider_speed = ctk.CTkSlider(
            speed_frame,
            from_=100, to=1500,
            number_of_steps=14,
            progress_color=SUCCESS,
            button_color="#ffffff",
            button_hover_color=ACCENT_CYAN,
            command=self._on_speed_change
        )
        self.slider_speed.set(self.burst_speed_ms)
        self.slider_speed.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_speed_val = ctk.CTkLabel(
            speed_frame, text=f"{self.burst_speed_ms} ms",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=TEXT_PRIMARY
        )
        self.lbl_speed_val.pack(side="right", padx=10)

        # Lista de reportes en cola (FIFO)
        self.frame_queue_items = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            height=260,
            corner_radius=0
        )
        self.frame_queue_items.pack(fill="both", expand=True, padx=16, pady=(4, 8))

        # Consola / Log en vivo de decisiones y rotaciones
        self.log_box = ctk.CTkTextbox(
            card,
            fg_color="#070c12",
            border_color="#1e2d3d",
            border_width=1,
            text_color="#22d3ee",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            height=110,
            corner_radius=RADIUS_MD
        )
        self.log_box.pack(fill="x", padx=16, pady=(0, 6))
        self.log_box.insert("end", "[14:31:02] Sistema listo. Esperando eventos o ráfagas en cola FIFO...\n")



        return card

    # ---------------------------------------------------------
    # Columna 3: Archivar Rama + Catálogos
    # ---------------------------------------------------------
    def _build_archive_panel(self, parent) -> ctk.CTkFrame:
        container = ctk.CTkFrame(parent, fg_color="transparent")

        # Tarjeta 1: Archivar Rama · Eventos Antiguos
        card_archive = Card(container, fg_color="#0e1620", border_color="#1e2d3d", corner_radius=12)
        card_archive.pack(fill="x", pady=(0, 12))

        header_arch = ctk.CTkFrame(card_archive, fg_color="transparent")
        header_arch.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            header_arch, text="Archivar Rama · Eventos Antiguos",
            font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(side="left")

        self.b_eligible = ctk.CTkFrame(header_arch, fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1, corner_radius=RADIUS_MD)
        self.b_eligible.pack(side="right")
        self.lbl_eligible_badge = ctk.CTkLabel(
            self.b_eligible, text="T=72h · 0 elegibles",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=WARNING
        )
        self.lbl_eligible_badge.pack(padx=10, pady=5)

        # Slider Umbral T
        slider_t_box = ctk.CTkFrame(card_archive, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, corner_radius=RADIUS_MD)
        slider_t_box.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(slider_t_box, text="Umbral T", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_SECONDARY).pack(side="left", padx=10, pady=8)
        self.slider_t = ctk.CTkSlider(
            slider_t_box,
            from_=1, to=168,
            number_of_steps=167,
            progress_color=WARNING,
            button_color="#ffffff",
            button_hover_color=WARNING,
            command=self._on_t_change
        )
        self.slider_t.set(self.archive_threshold_hours)
        self.slider_t.pack(side="left", fill="x", expand=True, padx=8)

        self.lbl_t_val = ctk.CTkLabel(
            slider_t_box, text=f"{self.archive_threshold_hours} h",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=TEXT_PRIMARY
        )
        self.lbl_t_val.pack(side="right", padx=10)

        # Tarjeta resultado de análisis (Ámbar)
        self.frame_eligibility_result = ctk.CTkFrame(
            card_archive,
            fg_color="#20180a",
            border_color="#ffb020",
            border_width=1,
            corner_radius=RADIUS_MD
        )
        self.frame_eligibility_result.pack(fill="x", padx=16, pady=6)

        self.lbl_elig_root = ctk.CTkLabel(
            self.frame_eligibility_result,
            text="Raíz candidata: Analizar primero",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color="#ffb020"
        )
        self.lbl_elig_root.pack(anchor="w", padx=10, pady=(8, 2))

        self.lbl_elig_detail = ctk.CTkLabel(
            self.frame_eligibility_result,
            text="Haz clic en 'Analizar Elegibilidad' para evaluar.",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=300
        )
        self.lbl_elig_detail.pack(anchor="w", padx=10, pady=(1, 8))

        # Botón Ejecutar Archivo Masivo
        self.btn_exec_archive = ctk.CTkButton(
            card_archive,
            text="Ejecutar Archivo de Rama",
            fg_color="#181308",
            hover_color="#2a200e",
            text_color="#ffb020",
            border_color="#ffb020",
            border_width=1,
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            height=34,
            corner_radius=RADIUS_SM,
            command=self._handle_execute_archive
        )
        self.btn_exec_archive.pack(fill="x", padx=16, pady=(4, 14))

        # Tarjeta 2: Catálogo de Eventos (Segmented Tabs + Lista)
        card_catalog = Card(container, fg_color="#0e1620", border_color="#1e2d3d", corner_radius=12)
        card_catalog.pack(fill="both", expand=True)

        # Pestañas Activos / Archivados / Eliminados
        tabs_box = ctk.CTkFrame(card_catalog, fg_color="#101922", corner_radius=RADIUS_SM)
        tabs_box.pack(fill="x", padx=16, pady=(16, 8))
        tabs_box.grid_columnconfigure((0, 1, 2), weight=1, uniform="cat_tab")

        self.btn_tab_activos = ctk.CTkButton(
            tabs_box, text="Activos 0",
            fg_color=ACCENT_CYAN, text_color=TEXT_INVERSE,
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            height=28, corner_radius=RADIUS_SM,
            command=lambda: self._switch_catalog_tab("activos")
        )
        self.btn_tab_activos.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        self.btn_tab_archiv = ctk.CTkButton(
            tabs_box, text="Archiv. 0",
            fg_color="transparent", text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            height=28, corner_radius=RADIUS_SM,
            command=lambda: self._switch_catalog_tab("archivados")
        )
        self.btn_tab_archiv.grid(row=0, column=1, sticky="ew", padx=2, pady=2)

        self.btn_tab_elim = ctk.CTkButton(
            tabs_box, text="Elim. 0",
            fg_color="transparent", text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            height=28, corner_radius=RADIUS_SM,
            command=lambda: self._switch_catalog_tab("eliminados")
        )
        self.btn_tab_elim.grid(row=0, column=2, sticky="ew", padx=2, pady=2)

        # Lista de eventos scrolleable
        self.frame_catalog_items = ctk.CTkScrollableFrame(
            card_catalog,
            fg_color="transparent",
            height=180,
            corner_radius=0
        )
        self.frame_catalog_items.pack(fill="both", expand=True, padx=16, pady=(4, 6))



        return container

    # ---------------------------------------------------------
    # 3. Footer
    # ---------------------------------------------------------
    def _build_footer(self, parent):
        pass

    # =========================================================================
    # LÓGICA DE ACTUALIZACIÓN Y SINCRONIZACIÓN DE LA VISTA
    # =========================================================================

    def refresh(self):
        """Refresca todos los datos visuales de la vista con el estado del observatorio."""
        if not self.observatory:
            return

        # 1. Actualizar contador de cola
        queue_size = len(self.observatory.report_queue.current_reports) if self.observatory.report_queue else 0
        self.lbl_queue_count.configure(text=f"{queue_size} en cola")

        # 2. Renderizar lista de reportes en cola
        self._render_queue_items()

        # 3. Renderizar catálogo de eventos (Activos / Archivados / Eliminados)
        self._render_catalog_items()

        # 4. Actualizar contadores en pestañas
        n_act = len(self.observatory.events_dict) if hasattr(self.observatory, 'events_dict') else 0
        n_arc = len(self.observatory.historic.archived) if (self.observatory.historic and hasattr(self.observatory.historic, 'archived')) else 0
        n_del = len(self.observatory.historic.deleted) if (self.observatory.historic and hasattr(self.observatory.historic, 'deleted')) else 0

        self.btn_tab_activos.configure(text=f"Activos {n_act}")
        self.btn_tab_archiv.configure(text=f"Archiv. {n_arc}")
        self.btn_tab_elim.configure(text=f"Elim. {n_del}")

        # 5. Evaluar elegibilidad según el umbral de prueba actual del previsualizador
        self._check_eligible_badge()
        self._handle_analyze_archive()

    def _render_queue_items(self):
        """Dibuja las tarjetas de los reportes en espera en la cola FIFO."""
        for widget in self.frame_queue_items.winfo_children():
            widget.destroy()

        if not self.observatory.report_queue or self.observatory.report_queue.is_empty():
            box_empty = ctk.CTkFrame(self.frame_queue_items, fg_color="transparent")
            box_empty.pack(fill="x", pady=20)
            ctk.CTkLabel(
                box_empty, text="Cola vacía · No hay reportes pendientes",
                font=ctk.CTkFont(family=FONT_MAIN, size=12), text_color=TEXT_MUTED
            ).pack()
            btn_load_burst = ctk.CTkButton(
                box_empty, text="Cargar Ráfaga de Prueba (6 reportes)",
                fg_color="#101922", hover_color="#1e2d3d", text_color=ACCENT_CYAN,
                font=ctk.CTkFont(family=FONT_MONO, size=11),
                command=self._load_demo_burst
            )
            btn_load_burst.pack(pady=8)
            return

        reports = self.observatory.report_queue.current_reports
        for idx, rep in enumerate(reports[:8]):
            is_head = (idx == 0)
            item_frame = ctk.CTkFrame(
                self.frame_queue_items,
                fg_color="#0b131c",
                border_color=ACCENT_CYAN if is_head else "#1e2d3d",
                border_width=1,
                corner_radius=RADIUS_MD
            )
            item_frame.pack(fill="x", pady=2.5)

            # Icono con ID
            icon_box = ctk.CTkFrame(item_frame, width=32, height=32, fg_color="#13202e", border_color="#1e2d3d", border_width=1, corner_radius=16)
            icon_box.pack(side="left", padx=8, pady=6)
            icon_box.pack_propagate(False)
            ctk.CTkLabel(icon_box, text=str(rep.id), font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"), text_color=TEXT_PRIMARY).place(relx=0.5, rely=0.5, anchor="center")

            # Información principal
            info_box = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True, padx=4)

            lbl_t = ctk.CTkLabel(
                info_box,
                text=f"R-{rep.id}  rev{rep.review} · M{rep.magnitude}",
                font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                text_color=TEXT_PRIMARY,
                anchor="w"
            )
            lbl_t.pack(anchor="w")

            st_name = rep.origin_station[0].name if (rep.origin_station and hasattr(rep.origin_station[0], 'name')) else "Estación"
            ctk.CTkLabel(
                info_box,
                text=f"{st_name} · {rep.epicenter}",
                font=ctk.CTkFont(family=FONT_MONO, size=10),
                text_color=TEXT_MUTED,
                anchor="w"
            ).pack(anchor="w")

            # Badge de previsión
            badge_text, badge_color = self._preview_report_badge(rep)
            badge_lbl = ctk.CTkLabel(
                item_frame, text=badge_text,
                font=ctk.CTkFont(family=FONT_MONO, size=9, weight="bold"),
                text_color="#ffffff", fg_color=badge_color, corner_radius=4
            )
            badge_lbl.pack(side="right", padx=8, ipadx=5, ipady=1)

    def _preview_report_badge(self, report: Report) -> tuple[str, str]:
        """Calcula visualmente la etiqueta esperada para el reporte."""
        if not self.observatory:
            return ("PEND", TEXT_MUTED)
        if self.observatory.historic and hasattr(self.observatory.historic, 'deleted') and report.id in self.observatory.historic.deleted:
            return ("DESCARTADO", DANGER)

        event, is_archived = self.observatory._find_event(report.id)
        if event is None:
            return ("ALTA", DANGER)
        elif report.review > event.review:
            return ("CORRECCIÓN", ACCENT_CYAN)
        elif report.review == event.review:
            if self.observatory._has_same_physical_data(report, event):
                return ("CONFIRM", "#22d3ee")
            else:
                return ("CONFLICTO", WARNING)
        else:
            return ("ANTIGUO", TEXT_MUTED)

    def _render_catalog_items(self):
        """Renderiza la lista de eventos en el catálogo seleccionado (Activos, Archivados o Eliminados)."""
        for widget in self.frame_catalog_items.winfo_children():
            widget.destroy()

        if not self.observatory:
            return

        events_to_show = []
        if self.active_catalog_tab == "activos":
            events_to_show = list(self.observatory.events_dict.values())
        elif self.active_catalog_tab == "archivados" and self.observatory.historic:
            events_to_show = list(self.observatory.historic.archived.values())
        elif self.active_catalog_tab == "eliminados" and self.observatory.historic:
            events_to_show = list(self.observatory.historic.deleted.values())

        if not events_to_show:
            ctk.CTkLabel(
                self.frame_catalog_items,
                text=f"No hay eventos en '{self.active_catalog_tab}'",
                font=ctk.CTkFont(family=FONT_MAIN, size=11), text_color=TEXT_MUTED
            ).pack(pady=20)
            return

        for ev in events_to_show[:20]:
            row = ctk.CTkFrame(self.frame_catalog_items, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, corner_radius=RADIUS_SM)
            row.pack(fill="x", pady=2)

            # Funciones de hover
            def on_enter(e, r=row):
                r.configure(fg_color="#182736")
            def on_leave(e, r=row):
                r.configure(fg_color="#0b131c")

            row.bind("<Button-1>", lambda e, event_obj=ev: self._load_event_into_form(event_obj))
            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)

            lbl_id = ctk.CTkLabel(
                row, text=f"EV-{ev.id}",
                font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                text_color=TEXT_PRIMARY
            )
            lbl_id.pack(side="left", padx=8, pady=4)
            lbl_id.bind("<Button-1>", lambda e, event_obj=ev: self._load_event_into_form(event_obj))
            lbl_id.bind("<Enter>", on_enter)
            lbl_id.bind("<Leave>", on_leave)

            k_tuple = ev.get_key() if hasattr(ev, 'get_key') else f"P{ev.priority}"
            lbl_k = ctk.CTkLabel(
                row, text=str(k_tuple),
                font=ctk.CTkFont(family=FONT_MONO, size=11),
                text_color=ACCENT_CYAN
            )
            lbl_k.pack(side="left", padx=6)
            lbl_k.bind("<Button-1>", lambda e, event_obj=ev: self._load_event_into_form(event_obj))
            lbl_k.bind("<Enter>", on_enter)
            lbl_k.bind("<Leave>", on_leave)

            # Status Badge a la derecha
            if ev.status == "Deleted":
                b_text, b_color = "ELIM", DANGER
            elif ev.status == "Archived":
                b_text, b_color = "→ arch", TEXT_MUTED
            elif ev.attention_state == "Reviewed":
                b_text, b_color = "REV ✓", SUCCESS
            else:
                b_text, b_color = "PEND", WARNING

            badge = ctk.CTkLabel(
                row, text=b_text,
                font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                text_color=b_color
            )
            badge.pack(side="right", padx=8)
            badge.bind("<Button-1>", lambda e, event_obj=ev: self._load_event_into_form(event_obj))
            badge.bind("<Enter>", on_enter)
            badge.bind("<Leave>", on_leave)

    def _switch_catalog_tab(self, tab: str):
        """Cambia la pestaña activa del catálogo de eventos."""
        self.active_catalog_tab = tab

        # Estilizar pestañas
        self.btn_tab_activos.configure(
            fg_color=ACCENT_CYAN if tab == "activos" else "transparent",
            text_color=TEXT_INVERSE if tab == "activos" else TEXT_SECONDARY,
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold" if tab == "activos" else "normal")
        )
        self.btn_tab_archiv.configure(
            fg_color=ACCENT_CYAN if tab == "archivados" else "transparent",
            text_color=TEXT_INVERSE if tab == "archivados" else TEXT_SECONDARY,
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold" if tab == "archivados" else "normal")
        )
        self.btn_tab_elim.configure(
            fg_color=ACCENT_CYAN if tab == "eliminados" else "transparent",
            text_color=TEXT_INVERSE if tab == "eliminados" else TEXT_SECONDARY,
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold" if tab == "eliminados" else "normal")
        )

        self._render_catalog_items()

    def _check_eligible_badge(self):
        """Actualiza el badge T=X en el encabezado con el umbral de prueba."""
        if not self.observatory:
            return
        t_val = self.archive_threshold_hours
        try:
            res = self.observatory.archive_subtree(execute=False, max_age_hours=t_val)
            cnt = res["count"] if res else 0
        except Exception:
            cnt = 0
        self.lbl_eligible_badge.configure(text=f"T={t_val}h · {cnt} elegibles")

    # =========================================================================
    # ACCIONES DEL FORMULARIO CRUD
    # =========================================================================

    def _step_datetime(self, days=0, hours=0):
        try:
            date_part = self.entry_date.get().strip()
            time_part = self.entry_time.get().strip()
            if not date_part or not time_part:
                dt = self.observatory.clock_simulation if self.observatory else datetime.now()
            else:
                dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
            
            from datetime import timedelta
            dt += timedelta(days=days, hours=hours)
            
            self.entry_date.delete(0, "end")
            self.entry_date.insert(0, dt.strftime("%Y-%m-%d"))
            self.entry_time.delete(0, "end")
            self.entry_time.insert(0, dt.strftime("%H:%M:%S"))
        except ValueError:
            pass

    def _on_form_change(self):
        """Se ejecuta al modificar campos clave para recalcular la prioridad y validar."""
        try:
            mag = float(self.entry_mag.get().strip())
            depth = float(self.entry_depth.get().strip())
            x = float(self.entry_x.get().strip())
            y = float(self.entry_y.get().strip())

            # Validar rangos obligatorios del PDF
            is_valid = (-2.0 <= mag <= 10.0) and (0.0 <= depth <= 700.0) and (0.0 <= x <= 1000.0) and (0.0 <= y <= 1000.0)
            if is_valid:
                p = self.observatory.calculate_priority(mag, depth, (x, y)) if self.observatory else 1
                p_text = "Alto" if p == 3 else "Media" if p == 2 else "Baja"
                self.lbl_p_calc.configure(text=p_text, text_color=ACCENT_CYAN)
                self.badge_valid.configure(text="✓ válido", text_color=SUCCESS, fg_color="#0c281a")
            else:
                self.badge_valid.configure(text="✕ rango fuera", text_color=WARNING, fg_color="#2a1608")
        except ValueError:
            self.badge_valid.configure(text="✕ entrada incompleta", text_color=TEXT_MUTED, fg_color="#101922")

    def _handle_create_event(self):
        """Valida y crea manualmente un evento en el observatorio."""
        try:
            eid = int(self.entry_id.get().strip())
            mag = float(self.entry_mag.get().strip())
            depth = float(self.entry_depth.get().strip())
            x = float(self.entry_x.get().strip())
            y = float(self.entry_y.get().strip())

            date_part = self.entry_date.get().strip()
            time_part = self.entry_time.get().strip()
            if not date_part or not time_part:
                raise ValueError("La fecha y la hora no pueden estar vacías.")
            try:
                dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("Formato de fecha u hora inválido. Usa YYYY-MM-DD y HH:MM:SS")

            st_name = self.option_station.get()
            station_obj = None
            if self.observatory and self.observatory.stations:
                for s in self.observatory.stations:
                    if s.name == st_name:
                        station_obj = s
                        break
            if station_obj is None:
                station_obj = Station(id=1, name=st_name, coords=(x, y))

            ev = self.observatory.create_event(
                event_id=eid,
                magnitude=mag,
                depth=depth,
                epicenter=(x, y),
                date_time=dt,
                station=station_obj
            )

            if ev is not None:
                self._show_msg(f"Evento {eid} creado exitosamente con prioridad {ev.priority}.", SUCCESS)
                self._log(f"[CREACIÓN] Evento {eid} registrado en AVL K={ev.get_key()}", SUCCESS)
                self.refresh()
                if self.app and hasattr(self.app, 'refresh_all'):
                    self.app.refresh_all()
            else:
                self._show_msg(f"No se pudo crear: el ID {eid} ya existe o viola validaciones.", DANGER)
        except Exception as ex:
            self._show_msg(f"Error al crear: {ex}", DANGER)

    def _handle_edit_event(self):
        """Modifica un evento existente en el catálogo activo."""
        try:
            eid = int(self.entry_id.get().strip())
            mag = float(self.entry_mag.get().strip())
            depth = float(self.entry_depth.get().strip())
            x = float(self.entry_x.get().strip())
            y = float(self.entry_y.get().strip())

            date_part = self.entry_date.get().strip()
            time_part = self.entry_time.get().strip()
            if not date_part or not time_part:
                raise ValueError("La fecha y la hora no pueden estar vacías.")
            try:
                dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("Formato de fecha u hora inválido. Usa YYYY-MM-DD y HH:MM:SS")

            ev = self.observatory.edit_event(
                event_id=eid,
                new_magnitude=mag,
                new_depth=depth,
                new_epicenter=(x, y),
                new_date_time=dt
            )

            if ev is not None:
                self._show_msg(f"Evento {eid} modificado. Nueva revisión: {ev.review}.", SUCCESS)
                self._log(f"[CORRECCIÓN] Evento {eid} actualizado a rev{ev.review} K={ev.get_key()}", ACCENT_CYAN)
                self.refresh()
                if self.app and hasattr(self.app, 'refresh_all'):
                    self.app.refresh_all()
            else:
                self._show_msg(f"Error: Evento {eid} no encontrado en catálogo activo.", WARNING)
        except Exception as ex:
            self._show_msg(f"Error en modificación: {ex}", DANGER)

    def _handle_mark_reviewed(self):
        """Marca el evento actual como 'Reviewed'."""
        try:
            eid = int(self.entry_id.get().strip())
            success = self.observatory.mark_as_reviewed(eid)
            if success:
                self._show_msg(f"Evento {eid} marcado como 'Reviewed'.", SUCCESS)
                self._log(f"[ESTADO] Evento {eid} pasó a 'Reviewed' ✓", SUCCESS)
                self.refresh()
                if self.app and hasattr(self.app, 'refresh_all'):
                    self.app.refresh_all()
            else:
                self._show_msg(f"No se encontró el evento {eid}.", WARNING)
        except Exception as ex:
            self._show_msg(f"Error al marcar revisado: {ex}", DANGER)

    def _handle_delete_event(self):
        """Elimina individualmente un evento activo."""
        try:
            eid = int(self.entry_id.get().strip())
            ev = self.observatory.remove_event(eid)
            if ev is not None:
                self._show_msg(f"Evento {eid} eliminado y retirado a histórico.", DANGER)
                self._log(f"[ELIMINACIÓN] Evento {eid} retirado del AVL.", DANGER)
                self.refresh()
                if self.app and hasattr(self.app, 'refresh_all'):
                    self.app.refresh_all()
            else:
                self._show_msg(f"Evento {eid} no encontrado.", WARNING)
        except Exception as ex:
            self._show_msg(f"Error al eliminar: {ex}", DANGER)

    def _load_event_into_form(self, ev):
        """Carga los atributos de un evento en los campos del formulario."""
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, str(ev.id))

        self.entry_mag.delete(0, "end")
        self.entry_mag.insert(0, str(ev.magnitude))

        self.entry_depth.delete(0, "end")
        self.entry_depth.insert(0, str(ev.depth))

        self.entry_x.delete(0, "end")
        self.entry_x.insert(0, str(ev.epicenter[0]))

        self.entry_y.delete(0, "end")
        self.entry_y.insert(0, str(ev.epicenter[1]))

        if hasattr(ev, 'origin_stations') and ev.origin_stations:
            st = ev.origin_stations[0]
            st_name = st.name if hasattr(st, 'name') else str(st)
            if st_name in self.option_station.cget("values"):
                self.option_station.set(st_name)

        if hasattr(ev, 'date_time'):
            self.entry_date.delete(0, "end")
            self.entry_date.insert(0, ev.date_time.strftime("%Y-%m-%d"))
            self.entry_time.delete(0, "end")
            self.entry_time.insert(0, ev.date_time.strftime("%H:%M:%S"))

        self._on_form_change()
        self._show_msg(f"Cargado evento EV-{ev.id} en formulario.", TEXT_SECONDARY)

        # Consulta técnica detallada usando query_event (profundidad, factor balance, rol de réplica/referencia)
        if self.observatory and hasattr(self.observatory, 'query_event'):
            info = self.observatory.query_event(ev.id)
            if info:
                nm = info.get("node_metrics") or {}
                d_str = f"prof_árbol={nm.get('depth', '-')}" if nm else ""
                bf_str = f"FB={nm.get('balance_factor', '-')}" if nm else ""
                assoc = info.get("associations")
                role_str = f"rol={assoc.get('role', 'Normal')}" if assoc else ""
                meta = " · ".join([s for s in [d_str, bf_str, role_str] if s])
                if meta:
                    self._log(f"[CONSULTA EV-{ev.id}] {meta}", ACCENT_CYAN)

    def _clear_form(self):
        """Limpia los campos del formulario y restablece valores predeterminados."""
        self.entry_id.delete(0, "end")
        self.entry_mag.delete(0, "end")
        self.entry_depth.delete(0, "end")
        self.entry_x.delete(0, "end")
        self.entry_y.delete(0, "end")

        if self.observatory:
            cur_date = self.observatory.clock_simulation.strftime("%Y-%m-%d")
            cur_time = self.observatory.clock_simulation.strftime("%H:%M:%S")
        else:
            cur_date = "2025-06-13"
            cur_time = "15:00:00"

        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, cur_date)
        self.entry_time.delete(0, "end")
        self.entry_time.insert(0, cur_time)

        self.lbl_p_calc.configure(text="P=auto", text_color=TEXT_MUTED)
        self.lbl_form_msg.configure(text="")
        self.badge_valid.configure(text="formulario limpio", text_color=TEXT_MUTED, fg_color="#101922")

    def _show_msg(self, text: str, color: str):
        self.lbl_form_msg.configure(text=text, text_color=color)

    # =========================================================================
    # ACCIONES DE LA COLA FIFO Y RÁFAGAS
    # =========================================================================

    def _handle_step_queue(self):
        """Procesa un solo reporte de la cabeza de la cola."""
        if not self.observatory or not self.observatory.report_queue or self.observatory.report_queue.is_empty():
            self._log("[COLA] Cola vacía. No hay reportes para procesar.", TEXT_MUTED)
            return

        res = self.observatory.process_report_step()
        if res:
            decision = res.get("decision", "Procesado")
            time_now = datetime.now().strftime("%H:%M:%S")
            rep_id = res.get("event_id")
            rot_info = ""
            if res.get("rotations"):
                rot_info = f" · rot {res['rotations']}"
            
            self._log(f"[{time_now}] R-{rep_id} → {decision}{rot_info}", ACCENT_CYAN)
            self.refresh()
            if self.app and hasattr(self.app, 'refresh_all'):
                self.app.refresh_all()

    def _handle_toggle_burst(self):
        """Inicia el modo continuo de procesamiento de ráfagas."""
        if self.burst_running:
            return
        self.burst_running = True
        self.btn_burst.configure(text="● Corriendo...", fg_color=WARNING)
        self._burst_tick()

    def _burst_tick(self):
        """Tick recurrente para procesar la cola paso a paso a la velocidad configurada."""
        if not self.burst_running:
            return

        if self.observatory and self.observatory.report_queue and not self.observatory.report_queue.is_empty():
            self._handle_step_queue()
            self.after(self.burst_speed_ms, self._burst_tick)
        else:
            self._handle_pause_burst()
            self._log("[RÁFAGA] Ráfaga completada. Cola vacía.", SUCCESS)

    def _handle_pause_burst(self):
        """Pausa el modo continuo."""
        self.burst_running = False
        self.btn_burst.configure(text="● Continuo", fg_color=SUCCESS)

    def _on_speed_change(self, value):
        self.burst_speed_ms = int(value)
        self.lbl_speed_val.configure(text=f"{self.burst_speed_ms} ms")

    def _log(self, text: str, color_hint: str = None):
        """Inserta una línea en la consola de log en vivo."""
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def _ensure_demo_queue(self):
        """Carga reportes de prueba en la cola si actualmente está vacía."""
        if not self.observatory:
            return
        if self.observatory.report_queue is None:
            from Business.Structures.report_queue import Report_Queue
            self.observatory.report_queue = Report_Queue()

    def _load_demo_burst(self):
        """Carga una ráfaga representativa de 6 reportes (Alta, Confirm, Conflicto, Antiguo)."""
        if not self.observatory or not self.observatory.stations:
            return

        st1 = self.observatory.stations[0]
        st2 = self.observatory.stations[1] if len(self.observatory.stations) > 1 else st1
        now = self.observatory.clock_simulation

        demo_reports = [
            Report(id=881, magnitude=5.4, depth=15.0, epicenter=(412.0, 388.0), date_time=now, review=2, origin_station=[st1]),
            Report(id=42,  magnitude=6.1, depth=18.0, epicenter=(410.0, 390.0), date_time=now, review=1, origin_station=[st2]),
            Report(id=10,  magnitude=5.8, depth=22.0, epicenter=(412.0, 388.0), date_time=now, review=1, origin_station=[st1]),
            Report(id=31,  magnitude=4.8, depth=45.0, epicenter=(200.0, 150.0), date_time=now, review=0, origin_station=[st2]),
            Report(id=885, magnitude=6.0, depth=10.0, epicenter=(350.0, 400.0), date_time=now, review=1, origin_station=[st1]),
            Report(id=886, magnitude=3.3, depth=12.0, epicenter=(150.0, 200.0), date_time=now, review=1, origin_station=[st1]),
        ]

        for r in demo_reports:
            self.observatory.report_queue.enqueue(r)

        self._log("[RÁFAGA] 6 reportes de prueba cargados en la cola FIFO.", ACCENT_CYAN)
        self.refresh()

    # =========================================================================
    # ACCIONES DE ARCHIVO DE SUBÁRBOLES
    # =========================================================================

    def _on_t_change(self, value):
        self.archive_threshold_hours = int(value)
        self.lbl_t_val.configure(text=f"{self.archive_threshold_hours} h")
        # Modo previsualizador: NO modificamos el valor global self.observatory.max_tree_age aquí
        self._check_eligible_badge()
        self._handle_analyze_archive()

    def _handle_analyze_archive(self):
        """Ejecuta la vista previa de búsqueda de ramas elegibles usando el umbral del slider."""
        if not self.observatory:
            return

        try:
            res = self.observatory.archive_subtree(execute=False, max_age_hours=self.archive_threshold_hours)
            if res:
                root_id = res["best_root_id"]
                count = res["count"]
                affected = res["affected_ids"]
                self.lbl_elig_root.configure(text=f"Raíz candidata: EV-{root_id}")
                self.lbl_elig_detail.configure(text=f"{count} nodos · IDs {affected[:6]}... · todos > {self.archive_threshold_hours}h")
                self.btn_exec_archive.configure(text=f"Ejecutar Archivo · {count} nodos", state="normal")
                # self._log(f"[ARCHIVO] Rama elegible identificada: raíz EV-{root_id} ({count} nodos)", WARNING)
            else:
                self.lbl_elig_root.configure(text="Sin ramas elegibles")
                self.lbl_elig_detail.configure(text=f"No existe ninguna rama con todos sus nodos de Prioridad 1 y edad > {self.archive_threshold_hours}h.")
                self.btn_exec_archive.configure(text="Sin ramas para archivar", state="disabled")
        except Exception:
            self.lbl_elig_root.configure(text="Sin ramas elegibles")
            self.lbl_elig_detail.configure(text=f"No existe ninguna rama con todos sus nodos de Prioridad 1 y edad > {self.archive_threshold_hours}h.")
            self.btn_exec_archive.configure(text="Sin ramas para archivar", state="disabled")

        self._check_eligible_badge()

    def _handle_execute_archive(self):
        """Ejecuta el archivo masivo de la rama elegible seleccionada y fija el nuevo valor global de T."""
        if not self.observatory:
            return

        # El usuario confirmó la acción: ahora sí fijamos el nuevo valor global de T en el observatorio
        self.observatory.max_tree_age = self.archive_threshold_hours
        try:
            res = self.observatory.archive_subtree(execute=True)
            if res:
                root_id = res["best_root_id"]
                count = res["count"]
                self._show_msg(f"Rama con raíz {root_id} ({count} eventos) archivada con éxito. T global fijado en {self.archive_threshold_hours}h.", SUCCESS)
                self._log(f"[ARCHIVO MASIVO] {count} eventos trasladados al Histórico (T global = {self.archive_threshold_hours}h).", SUCCESS)
                self.lbl_elig_root.configure(text="Archivo ejecutado con éxito")
                self.btn_exec_archive.configure(text="Ejecutar Archivo de Rama", state="disabled")
                self.refresh()
                if self.app and hasattr(self.app, 'refresh_all'):
                    self.app.refresh_all()
        except Exception as ex:
            self._show_msg(f"Error al archivar: {ex}", DANGER)
