"""
Presentation / Views / queries_view.py
Vista de Consultas, Auditoría y Métricas.
Implementa fielmente el diseño de Banani en CustomTkinter:
- Encabezado con breadcrumb, título y badge dinámico de eventos costosos P3>L.
- Fila superior (2 Columnas):
  * Columna 1 (Izquierda): Generador de Consultas Avanzadas con 4 pestañas interactivas:
    1. Top-k pendientes en orden descendente de K=(P, M, I) con poda temprana.
    2. Filtros por rango de magnitud, profundidad y fechas con poda matemática.
    3. Búsqueda y trazabilidad de asociaciones y réplicas.
    4. Detección de accesos costosos de alta prioridad (profundidad > L).
  * Columna 2 (Derecha): AssociationExplorer detallado con candidato ganador, candidatos evaluados y réplicas.
- Fila inferior: Centro de Auditoría y Verificación Estructural Global:
  * 4 tarjetas de verificación técnica (Orden BST, Unicidad de IDs, Alturas recalculadas, Factores de balance).
  * 12 tarjetas de métricas acumulativas de negocio y rotaciones AVL (LL, RR, LR, RL, giros).
  * Barra de reporte descargable en JSON.
"""

import json
import math
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox
import customtkinter as ctk

from Models.event import Event
from Business.Rules.queries import Queries
from Presentation.Components.theme import (
    FONT_MAIN, FONT_MONO,
    BG_ROOT, BG_SURFACE, BG_SURFACE_ALT,
    BORDER_SUBTLE, BORDER_STRONG,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_INVERSE,
    ACCENT_CYAN, ACCENT_CYAN_HOVER,
    SUCCESS, WARNING, DANGER,
    RADIUS_SM, RADIUS_MD, RADIUS_LG
)
from Presentation.Components import Card, PrimaryButton, SecondaryButton, GhostButton


class QueriesView(ctk.CTkFrame):
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color=BG_ROOT, corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory

        # Estado de navegación y parámetros de consulta
        self.active_query_tab = "top_k"
        self.last_visited_nodes = 0
        self.selected_assoc_event_id = None
        self.current_query_results = []
        self.audit_status = {
            "bst_order": True,
            "unique_ids": True,
            "heights": True,
            "balance_factors": True,
            "errors": [],
            "last_audit_time": None
        }

        # Construir Interfaz de Usuario
        self._build_ui()
        self.refresh()
        self._handle_execute_query()

    # =========================================================================
    # CONSTRUCCIÓN DE LA INTERFAZ
    # =========================================================================

    def _build_ui(self):
        # Contenedor principal con scroll vertical adaptable a cualquier resolución
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Encabezado de la Vista
        self._build_header(self.scroll_container)

        # 2. Grid Superior: Generador de Consultas (Izq) + Association Explorer (Der)
        top_grid = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        top_grid.pack(fill="x", pady=(0, 15))
        top_grid.grid_columnconfigure(0, weight=6)
        top_grid.grid_columnconfigure(1, weight=4)

        # Componente Izquierdo: Generador de Consultas
        self.card_query_gen = self._build_query_generator(top_grid)
        self.card_query_gen.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Componente Derecho: Association Explorer
        self.card_assoc_exp = self._build_association_explorer(top_grid)
        self.card_assoc_exp.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # 3. Componente Inferior: Centro de Auditoría y Verificación Estructural
        self.card_audit_center = self._build_audit_center(self.scroll_container)
        self.card_audit_center.pack(fill="x", pady=(0, 15))

        # 4. Pie de Página Técnico
        self._build_footer(self.scroll_container)

    # -------------------------------------------------------------------------
    # 1. Encabezado
    # -------------------------------------------------------------------------
    def _build_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        left_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_box.pack(side="left", fill="y")

        lbl_breadcrumb = ctk.CTkLabel(
            left_box,
            text="PRESENTATION / VIEWS / QUERIES_VIEW.PY · EXPANDIDO",
            font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
            text_color=ACCENT_CYAN
        )
        lbl_breadcrumb.pack(anchor="w")

        lbl_title = ctk.CTkLabel(
            left_box,
            text="Consultas, Auditoría y Métricas",
            font=ctk.CTkFont(family=FONT_MAIN, size=24, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        lbl_title.pack(anchor="w", pady=(2, 0))

        lbl_subtitle = ctk.CTkLabel(
            left_box,
            text="Generador de 4 tabs con nodos visitados obligatorios + verificación estructural global.",
            font=ctk.CTkFont(family=FONT_MAIN, size=12),
            text_color=TEXT_MUTED
        )
        lbl_subtitle.pack(anchor="w", pady=(2, 0))

        # Badges a la derecha
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right", anchor="s")

        self.chip_tabs_info = ctk.CTkLabel(
            right_box,
            text="tabs: Top-k · Rangos · Asociaciones · Costoso",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_MUTED,
            fg_color="#0e1620",
            corner_radius=6,
            padx=10,
            pady=6
        )
        self.chip_tabs_info.pack(side="left", padx=(0, 6))

        self.chip_costly_count = ctk.CTkLabel(
            right_box,
            text="0 costosos P3·depth>L",
            font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
            text_color="#ffb020",
            fg_color="#0e1620",
            corner_radius=6,
            padx=10,
            pady=6
        )
        self.chip_costly_count.pack(side="left")

    # -------------------------------------------------------------------------
    # 2. Generador de Consultas Avanzadas (Columna Izquierda Superior)
    # -------------------------------------------------------------------------
    def _build_query_generator(self, parent):
        card = Card(parent, fg_color="#0e1620", border_color="#1e2d3d", corner_radius=12)

        # Header de la tarjeta
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))

        lbl_title = ctk.CTkLabel(
            header,
            text="Generador de Consultas Avanzadas",
            font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        lbl_title.pack(side="left")

        self.badge_visited_nodes = ctk.CTkLabel(
            header,
            text="◉ visitados AVL: 0 nodos",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color="#ffb020",
            fg_color="#20180a",
            corner_radius=4,
            padx=8,
            pady=4
        )
        self.badge_visited_nodes.pack(side="right")

        # Pestañas de tipo de consulta (4 Tabs)
        tabs_bar = ctk.CTkFrame(card, fg_color="transparent")
        tabs_bar.pack(fill="x", padx=16, pady=(4, 8))

        self.btn_tab_top_k = ctk.CTkButton(
            tabs_bar,
            text="Top-k pendientes ↓K",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            fg_color=ACCENT_CYAN,
            text_color=TEXT_INVERSE,
            height=30,
            corner_radius=6,
            command=lambda: self._switch_query_tab("top_k")
        )
        self.btn_tab_top_k.pack(side="left", padx=(0, 4))

        self.btn_tab_range = ctk.CTkButton(
            tabs_bar,
            text="Rango M + H + fechas",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#101922",
            border_color="#1e2d3d",
            border_width=1,
            text_color=TEXT_MUTED,
            height=30,
            corner_radius=6,
            command=lambda: self._switch_query_tab("range")
        )
        self.btn_tab_range.pack(side="left", padx=4)

        self.btn_tab_by_id = ctk.CTkButton(
            tabs_bar,
            text="Buscar por ID (Sec. 6)",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#101922",
            border_color="#1e2d3d",
            border_width=1,
            text_color=TEXT_MUTED,
            height=30,
            corner_radius=6,
            command=lambda: self._switch_query_tab("by_id")
        )
        self.btn_tab_by_id.pack(side="left", padx=4)

        self.btn_tab_assoc = ctk.CTkButton(
            tabs_bar,
            text="Asociaciones / ref",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#101922",
            border_color="#1e2d3d",
            border_width=1,
            text_color=TEXT_MUTED,
            height=30,
            corner_radius=6,
            command=lambda: self._switch_query_tab("assoc")
        )
        self.btn_tab_assoc.pack(side="left", padx=4)

        self.btn_tab_costly = ctk.CTkButton(
            tabs_bar,
            text="Acceso costoso P3>L",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#101922",
            border_color="#1e2d3d",
            border_width=1,
            text_color=TEXT_MUTED,
            height=30,
            corner_radius=6,
            command=lambda: self._switch_query_tab("costly")
        )
        self.btn_tab_costly.pack(side="left", padx=4)

        # Barra dinámica de parámetros de la consulta seleccionada
        self.frame_params = ctk.CTkFrame(card, fg_color="transparent")
        self.frame_params.pack(fill="x", padx=16, pady=4)
        self._render_param_controls()

        # Tabla de Resultados
        self.frame_table_container = ctk.CTkFrame(card, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, corner_radius=8)
        self.frame_table_container.pack(fill="both", expand=True, padx=16, pady=(8, 14))

        # Encabezado de la tabla (6 Columnas)
        tbl_hdr = ctk.CTkFrame(self.frame_table_container, fg_color="#070c12", corner_radius=0, height=30)
        tbl_hdr.pack(fill="x")
        tbl_hdr.grid_columnconfigure(0, weight=1)  # #
        tbl_hdr.grid_columnconfigure(1, weight=2)  # ID
        tbl_hdr.grid_columnconfigure(2, weight=3)  # K=(P,M,I)
        tbl_hdr.grid_columnconfigure(3, weight=3)  # Detalle
        tbl_hdr.grid_columnconfigure(4, weight=2)  # Estado
        tbl_hdr.grid_columnconfigure(5, weight=2)  # Visitados

        headers = ["#", "ID", "K=(P,M,I)", "Detalle", "Estado", "Visitados"]
        for col_idx, h_text in enumerate(headers):
            lbl = ctk.CTkLabel(
                tbl_hdr,
                text=h_text,
                font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                text_color=TEXT_MUTED,
                anchor="e" if h_text == "Visitados" else "w"
            )
            lbl.grid(row=0, column=col_idx, sticky="ew", padx=8, pady=4)

        # Filas de la tabla (Scrollable)
        self.scroll_table_rows = ctk.CTkScrollableFrame(self.frame_table_container, fg_color="transparent", height=180)
        self.scroll_table_rows.pack(fill="both", expand=True)

        return card

    # -------------------------------------------------------------------------
    # Renderizado Dinámico de Parámetros según Pestaña
    # -------------------------------------------------------------------------
    def _render_param_controls(self):
        for widget in self.frame_params.winfo_children():
            widget.destroy()

        tab = self.active_query_tab

        if tab == "top_k":
            # Param k
            f_k = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_k.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(f_k, text="k =", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED).pack(side="left", padx=(8, 4))
            self.entry_top_k = ctk.CTkEntry(f_k, width=45, height=26, fg_color="transparent", border_width=0, font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=TEXT_PRIMARY)
            self.entry_top_k.insert(0, "5")
            self.entry_top_k.pack(side="left", padx=(0, 6))

            # Chip preview
            f_info = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_info.pack(side="left", padx=4)
            ctk.CTkLabel(f_info, text="Pendientes (P3 > P2 > P1) · In-order inverso", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(padx=8, pady=4)

        elif tab == "range":
            # Rango Magnitud
            f_m = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_m.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(f_m, text="M ∈", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED).pack(side="left", padx=(6, 2))
            self.entry_min_m = ctk.CTkEntry(f_m, width=38, height=26, fg_color="transparent", border_width=0, font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_PRIMARY)
            self.entry_min_m.insert(0, "4.0")
            self.entry_min_m.pack(side="left")
            ctk.CTkLabel(f_m, text="→", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED).pack(side="left", padx=2)
            self.entry_max_m = ctk.CTkEntry(f_m, width=38, height=26, fg_color="transparent", border_width=0, font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_PRIMARY)
            self.entry_max_m.insert(0, "7.0")
            self.entry_max_m.pack(side="left", padx=(0, 6))

            # Profundidad H
            f_h = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_h.pack(side="left", padx=4)
            ctk.CTkLabel(f_h, text="H ≤", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED).pack(side="left", padx=(6, 2))
            self.entry_max_h = ctk.CTkEntry(f_h, width=40, height=26, fg_color="transparent", border_width=0, font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_PRIMARY)
            self.entry_max_h.insert(0, "70")
            self.entry_max_h.pack(side="left")
            ctk.CTkLabel(f_h, text="km", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(side="left", padx=(0, 6))

            # Días rango
            f_days = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_days.pack(side="left", padx=4)
            ctk.CTkLabel(f_days, text="Últimos", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(side="left", padx=(6, 2))
            self.entry_days = ctk.CTkEntry(f_days, width=35, height=26, fg_color="transparent", border_width=0, font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_PRIMARY)
            self.entry_days.insert(0, "30")
            self.entry_days.pack(side="left")
            ctk.CTkLabel(f_days, text="días", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(side="left", padx=(0, 6))

        elif tab == "by_id":
            # Búsqueda por ID según Sección 6
            f_id = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_id.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(f_id, text="ID =", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED).pack(side="left", padx=(8, 4))
            self.entry_search_id = ctk.CTkEntry(f_id, width=60, height=26, fg_color="transparent", border_width=0, font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=TEXT_PRIMARY)
            init_id = "42"
            if self.observatory and self.observatory.events_dict:
                init_id = str(next(iter(self.observatory.events_dict.keys())))
            self.entry_search_id.insert(0, init_id)
            self.entry_search_id.pack(side="left", padx=(0, 6))

            f_info = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_info.pack(side="left", padx=4)
            ctk.CTkLabel(f_info, text="Sección 6: Localización O(1) · métricas de nodo AVL (prof, h, FB) · asociaciones", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(padx=8, pady=4)

        elif tab == "assoc":
            # Evento objetivo ID
            f_id = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_id.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(f_id, text="ID =", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED).pack(side="left", padx=(8, 4))
            self.entry_target_id = ctk.CTkEntry(f_id, width=55, height=26, fg_color="transparent", border_width=0, font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=TEXT_PRIMARY)
            init_id = "42"
            if self.observatory and self.observatory.events_dict:
                init_id = str(next(iter(self.observatory.events_dict.keys())))
            self.entry_target_id.insert(0, init_id)
            self.entry_target_id.pack(side="left", padx=(0, 6))

            # Reglas fijas
            f_rules = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_rules.pack(side="left", padx=4)
            ctk.CTkLabel(f_rules, text="W ≤ 48h · R ≤ 40km · MA > MB", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(padx=8, pady=4)

        elif tab == "costly":
            # Límite L
            f_l = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_l.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(f_l, text="L =", font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED).pack(side="left", padx=(8, 4))
            self.entry_limit_l = ctk.CTkEntry(f_l, width=45, height=26, fg_color="transparent", border_width=0, font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=TEXT_PRIMARY)
            current_l = str(self.observatory.limit) if (self.observatory and hasattr(self.observatory, 'limit')) else "3"
            self.entry_limit_l.insert(0, current_l)
            self.entry_limit_l.pack(side="left", padx=(0, 6))

            f_info = ctk.CTkFrame(self.frame_params, fg_color="#0b131c", border_color=BORDER_SUBTLE, border_width=1, corner_radius=6)
            f_info.pack(side="left", padx=4)
            ctk.CTkLabel(f_info, text="Condición: Prioridad P=3 y profundidad en AVL > L", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(padx=8, pady=4)

        # Botones de Acción: Ejecutar y Exportar
        btn_exec = ctk.CTkButton(
            self.frame_params,
            text="Ejecutar",
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            fg_color=ACCENT_CYAN,
            text_color=TEXT_INVERSE,
            hover_color=ACCENT_CYAN_HOVER,
            height=28,
            corner_radius=6,
            command=self._handle_execute_query
        )
        btn_exec.pack(side="right", padx=(4, 0))

        btn_export = ctk.CTkButton(
            self.frame_params,
            text="Exportar",
            font=ctk.CTkFont(family=FONT_MAIN, size=11),
            fg_color="transparent",
            border_color="#1e2d3d",
            border_width=1,
            text_color=TEXT_SECONDARY,
            hover_color="#13202e",
            height=28,
            corner_radius=6,
            command=self._handle_export_query
        )
        btn_export.pack(side="right", padx=4)

    # -------------------------------------------------------------------------
    # 3. Explorador de Asociaciones (Columna Derecha Superior)
    # -------------------------------------------------------------------------
    def _build_association_explorer(self, parent):
        card = Card(parent, fg_color="#0e1620", border_color="#1e2d3d", corner_radius=12)

        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header, text="SISMOLAB · CONSULTAS Y REPORTES",
            font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#22d3ee"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header, text="Consultas y Métricas · Top-k",
            font=ctk.CTkFont(family=FONT_MAIN, size=22, weight="bold"), text_color="#e8eef3"
        ).pack(anchor="w", pady=(2, 0))
        
        ctk.CTkLabel(
            header, text="Consultas especializadas con poda de subárboles: Top-k pendientes, rango de magnitudes y réplicas.",
            font=ctk.CTkFont(family=FONT_MAIN, size=11), text_color="#8a9bb0"
        ).pack(anchor="w", pady=(2, 0))

        self.lbl_assoc_title = ctk.CTkLabel(
            header,
            text="Asociaciones · EV-...",
            font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.lbl_assoc_title.pack(side="left")

        self.badge_assoc_visited = ctk.CTkLabel(
            header,
            text="visitados: 0",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color="#ffb020",
            fg_color="#20180a",
            corner_radius=4,
            padx=8,
            pady=4
        )
        self.badge_assoc_visited.pack(side="right")

        # Selector de ID + Regla
        selector_bar = ctk.CTkFrame(card, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, corner_radius=6)
        selector_bar.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(selector_bar, text="Selector ID", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(side="left", padx=(8, 4), pady=4)

        self.combo_assoc_ids = ctk.CTkComboBox(
            selector_bar,
            values=["42"],
            width=90,
            height=26,
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            dropdown_font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="#101922",
            border_color="#1e2d3d",
            command=self._on_assoc_id_selected
        )
        self.combo_assoc_ids.pack(side="left", padx=4, pady=4)

        lbl_formula = ctk.CTkLabel(selector_bar, text="MA>MB · Δt≤W · d≤R", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED)
        lbl_formula.pack(side="right", padx=8, pady=4)

        # Sección 1: Candidatos Evaluados
        lbl_cand_title = ctk.CTkLabel(card, text="CANDIDATOS EVALUADOS", font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"), text_color=TEXT_MUTED)
        lbl_cand_title.pack(anchor="w", padx=16, pady=(10, 4))

        self.frame_candidates_list = ctk.CTkFrame(card, fg_color="transparent")
        self.frame_candidates_list.pack(fill="x", padx=16)

        # Sección 2: Lo toman como referencia
        lbl_ref_title = ctk.CTkLabel(card, text="LO TOMAN COMO REFERENCIA", font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"), text_color=TEXT_MUTED)
        lbl_ref_title.pack(anchor="w", padx=16, pady=(10, 4))

        self.frame_replicas_list = ctk.CTkFrame(card, fg_color="transparent")
        self.frame_replicas_list.pack(fill="x", padx=16)

        # Pie de tarjeta: Criterio de Desempate del PDF
        footer_tiebreak = ctk.CTkFrame(card, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, corner_radius=6)
        footer_tiebreak.pack(fill="x", padx=16, pady=(12, 14))

        lbl_tb = ctk.CTkLabel(
            footer_tiebreak,
            text="desempate: menor d → mayor MA → ID menor",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_MUTED
        )
        lbl_tb.pack(anchor="w", padx=8, pady=6)

        return card

    # -------------------------------------------------------------------------
    # 4. Centro de Auditoría y Verificación Estructural (Inferior)
    # -------------------------------------------------------------------------
    def _build_audit_center(self, parent):
        card = Card(parent, fg_color="#0e1620", border_color="#1e2d3d", corner_radius=12)

        # Header con Botón de Verificación
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 8))

        lbl_title = ctk.CTkLabel(
            header,
            text="Centro de Auditoría y Verificación",
            font=ctk.CTkFont(family=FONT_MAIN, size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        lbl_title.pack(side="left")

        btn_verify = ctk.CTkButton(
            header,
            text="Verificar Estructura",
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            fg_color=ACCENT_CYAN,
            text_color=TEXT_INVERSE,
            hover_color=ACCENT_CYAN_HOVER,
            height=30,
            corner_radius=6,
            command=self._handle_verify_structure
        )
        btn_verify.pack(side="right")

        # 4 Tarjetas de Verificación Técnica (1x4)
        cards_grid = ctk.CTkFrame(card, fg_color="transparent")
        cards_grid.pack(fill="x", padx=16, pady=4)
        cards_grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="audit_cards")

        # 1. Orden BST
        self.card_v_bst = self._create_audit_pill(cards_grid, 0, "✓ Orden BST global", "OK · inorden creciente K", SUCCESS)
        # 2. Unicidad de IDs
        self.card_v_uniq = self._create_audit_pill(cards_grid, 1, "✓ Unicidad de IDs", "OK · 0 duplicados", SUCCESS)
        # 3. Alturas recalculadas
        self.card_v_heights = self._create_audit_pill(cards_grid, 2, "✓ Alturas recalculadas", "OK · coinciden", SUCCESS)
        # 4. Factores de balance
        self.card_v_bf = self._create_audit_pill(cards_grid, 3, "✓ Factores balance", "OK · BF ∈ [-1,1]", SUCCESS)

        # Grid de 12 Tarjetas de Estadísticas (2 Filas de 6)
        stats_grid = ctk.CTkFrame(card, fg_color="transparent")
        stats_grid.pack(fill="x", padx=16, pady=(10, 8))
        for col_idx in range(6):
            stats_grid.grid_columnconfigure(col_idx, weight=1, uniform="stat_cards")

        # Fila 1: Métricas de Negocio
        self.lbl_stat_active = self._create_stat_cell(stats_grid, 0, 0, "0", "Activos", TEXT_PRIMARY)
        self.lbl_stat_archived = self._create_stat_cell(stats_grid, 0, 1, "0", "Archivados", TEXT_MUTED)
        self.lbl_stat_deleted = self._create_stat_cell(stats_grid, 0, 2, "0", "Eliminados (IDs)", TEXT_MUTED)
        self.lbl_stat_corrections = self._create_stat_cell(stats_grid, 0, 3, "0", "Correcciones", ACCENT_CYAN)
        self.lbl_stat_conflicts = self._create_stat_cell(stats_grid, 0, 4, "0", "Conflictos", "#ffb020")
        self.lbl_stat_discarded = self._create_stat_cell(stats_grid, 0, 5, "0", "Descartados", DANGER)

        # Fila 2: Balanceos y Giros AVL
        self.lbl_stat_ll = self._create_stat_cell(stats_grid, 1, 0, "0", "Balanceos LL", ACCENT_CYAN)
        self.lbl_stat_rr = self._create_stat_cell(stats_grid, 1, 1, "0", "Balanceos RR", ACCENT_CYAN)
        self.lbl_stat_lr = self._create_stat_cell(stats_grid, 1, 2, "0", "Balanceos LR", "#ff7a1a")
        self.lbl_stat_rl = self._create_stat_cell(stats_grid, 1, 3, "0", "Balanceos RL", "#ff7a1a")
        self.lbl_stat_left_turns = self._create_stat_cell(stats_grid, 1, 4, "0", "Giros izquierda", TEXT_PRIMARY)
        self.lbl_stat_right_turns = self._create_stat_cell(stats_grid, 1, 5, "0", "Giros derecha", TEXT_PRIMARY)

        # Barra de Resumen de Auditoría y Botón de Descarga
        report_bar = ctk.CTkFrame(card, fg_color="transparent")
        report_bar.pack(fill="x", padx=16, pady=(4, 14))

        self.lbl_audit_summary = ctk.CTkLabel(
            report_bar,
            text="reporte: auditoría pendiente · haga clic en 'Verificar Estructura'",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_MUTED,
            fg_color="#070c12",
            corner_radius=4,
            padx=10,
            pady=6
        )
        self.lbl_audit_summary.pack(side="left")

        btn_download_report = ctk.CTkButton(
            report_bar,
            text="Descargar reporte",
            font=ctk.CTkFont(family=FONT_MAIN, size=10),
            fg_color="transparent",
            border_color="#1e2d3d",
            border_width=1,
            text_color=TEXT_MUTED,
            hover_color="#13202e",
            height=26,
            corner_radius=4,
            command=self._handle_download_audit_report
        )
        btn_download_report.pack(side="right")

        return card

    def _create_audit_pill(self, parent, col: int, title: str, subtitle: str, color: str):
        frame = ctk.CTkFrame(parent, fg_color="#0c281a", border_color=color, border_width=1, corner_radius=8)
        frame.grid(row=0, column=col, sticky="ew", padx=3, pady=2)

        lbl_t = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=color)
        lbl_t.pack(anchor="w", padx=10, pady=(6, 1))

        lbl_s = ctk.CTkLabel(frame, text=subtitle, font=ctk.CTkFont(family=FONT_MONO, size=9), text_color=TEXT_MUTED)
        lbl_s.pack(anchor="w", padx=10, pady=(0, 6))
        return {"frame": frame, "title": lbl_t, "subtitle": lbl_s}

    def _create_stat_cell(self, parent, row: int, col: int, value: str, label: str, val_color: str):
        cell = ctk.CTkFrame(parent, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, corner_radius=8)
        cell.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)

        lbl_val = ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(family=FONT_MAIN, size=16, weight="bold"), text_color=val_color)
        lbl_val.pack(anchor="center", pady=(6, 0))

        lbl_desc = ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(family=FONT_MAIN, size=10), text_color=TEXT_MUTED)
        lbl_desc.pack(anchor="center", pady=(0, 6))
        return lbl_val

    # -------------------------------------------------------------------------
    # 5. Footer Técnico
    # -------------------------------------------------------------------------
    def _build_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(0, 5))

        lbl_l = ctk.CTkLabel(
            footer_frame,
            text="queries_view.py consume Observatory.top_k() · range_query() · associations(id) · costly_access(L) · verify_structure()",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_MUTED
        )
        lbl_l.pack(side="left")

        lbl_r = ctk.CTkLabel(
            footer_frame,
            text="toda consulta reporta nodos visitados AVL",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_MUTED
        )
        lbl_r.pack(side="right")

    # =========================================================================
    # LÓGICA DE ACTUALIZACIÓN Y SINCRONIZACIÓN DE LA VISTA
    # =========================================================================

    def refresh(self):
        """Refresca todos los datos visuales, listas de IDs y contadores acumulados."""
        if not self.observatory:
            return

        # 1. Actualizar lista de IDs en el combo de asociaciones
        event_ids = []
        if hasattr(self.observatory, 'events_dict') and self.observatory.events_dict:
            event_ids.extend([str(eid) for eid in sorted(self.observatory.events_dict.keys())])
        if self.observatory.historic and hasattr(self.observatory.historic, 'archived') and self.observatory.historic.archived:
            event_ids.extend([str(eid) for eid in sorted(self.observatory.historic.archived.keys())])

        if event_ids:
            self.combo_assoc_ids.configure(values=event_ids)
            if not self.selected_assoc_event_id or str(self.selected_assoc_event_id) not in event_ids:
                self.selected_assoc_event_id = int(event_ids[0])
                self.combo_assoc_ids.set(event_ids[0])
        else:
            self.combo_assoc_ids.configure(values=["-"])
            self.combo_assoc_ids.set("-")

        # 2. Actualizar contador dinámico de eventos costosos P3 > L en el encabezado
        costly_count = 0
        try:
            costly_events, _ = self.observatory.query_costly_high_priority_events()
            costly_count = len(costly_events)
        except Exception:
            costly_count = 0
        self.chip_costly_count.configure(text=f"{costly_count} costosos P3·depth>L")

        # 3. Actualizar contadores en la cuadrícula de auditoría
        metrics = getattr(self.observatory, 'metrics', None)
        n_act = len(self.observatory.events_dict) if hasattr(self.observatory, 'events_dict') else 0
        n_arc = len(self.observatory.historic.archived) if (self.observatory.historic and hasattr(self.observatory.historic, 'archived')) else 0
        n_del = len(self.observatory.historic.deleted) if (self.observatory.historic and hasattr(self.observatory.historic, 'deleted')) else 0

        self.lbl_stat_active.configure(text=str(n_act))
        self.lbl_stat_archived.configure(text=str(n_arc))
        self.lbl_stat_deleted.configure(text=str(n_del))

        if metrics:
            self.lbl_stat_corrections.configure(text=str(metrics.corrections_accepted))
            self.lbl_stat_conflicts.configure(text=str(metrics.conflicts))
            self.lbl_stat_discarded.configure(text=str(metrics.discarded_reports))
            self.lbl_stat_ll.configure(text=str(metrics.cases.get("LL", 0)))
            self.lbl_stat_rr.configure(text=str(metrics.cases.get("RR", 0)))
            self.lbl_stat_lr.configure(text=str(metrics.cases.get("LR", 0)))
            self.lbl_stat_rl.configure(text=str(metrics.cases.get("RL", 0)))
            self.lbl_stat_left_turns.configure(text=str(metrics.turns.get("left", 0)))
            self.lbl_stat_right_turns.configure(text=str(metrics.turns.get("right", 0)))

        # 4. Refrescar el explorador de asociaciones para el ID seleccionado
        if self.selected_assoc_event_id:
            self._render_association_details(self.selected_assoc_event_id)

    # -------------------------------------------------------------------------
    # Manejo de Pestañas del Generador de Consultas
    # -------------------------------------------------------------------------
    def _switch_query_tab(self, tab: str):
        self.active_query_tab = tab

        # Configurar colores de pestañas
        tabs = [
            ("top_k", self.btn_tab_top_k),
            ("range", self.btn_tab_range),
            ("by_id", self.btn_tab_by_id),
            ("assoc", self.btn_tab_assoc),
            ("costly", self.btn_tab_costly)
        ]
        for key, btn in tabs:
            if key == tab:
                btn.configure(fg_color=ACCENT_CYAN, text_color=TEXT_INVERSE, font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"))
            else:
                btn.configure(fg_color="#101922", text_color=TEXT_MUTED, font=ctk.CTkFont(family=FONT_MONO, size=11))

        self._render_param_controls()
        self._handle_execute_query()

    # =========================================================================
    # EJECUCIÓN DE CONSULTAS Y RENDERIZADO DE TABLA
    # =========================================================================

    def _handle_execute_query(self):
        """Ejecuta la consulta correspondiente según la pestaña activa y actualiza la tabla."""
        if not self.observatory:
            return

        tab = self.active_query_tab
        results = []
        visited = 0

        try:
            if tab == "top_k":
                k_val = int(self.entry_top_k.get().strip())
                events, visited = self.observatory.query_top_k_pending(k_val)
                results = [{"event": ev, "visited": visited, "detail": f"M{ev.magnitude} · {ev.depth}km"} for ev in events]

            elif tab == "range":
                min_m = float(self.entry_min_m.get().strip())
                max_m = float(self.entry_max_m.get().strip())
                max_h = float(self.entry_max_h.get().strip())
                days = int(self.entry_days.get().strip())

                now = self.observatory.clock_simulation
                start_dt = now - timedelta(days=days)

                # Consulta combinada aplicando podas del árbol
                events_m, visited_m = self.observatory.query_by_magnitude_range(min_m, max_m)
                visited = visited_m

                # Filtrar en memoria por profundidad y rango de fechas
                filtered_events = [ev for ev in events_m if ev.depth <= max_h and start_dt <= ev.date_time <= now]
                results = [{"event": ev, "visited": visited, "detail": f"M{ev.magnitude} · {ev.depth}km · {ev.date_time.strftime('%m-%d')}"} for ev in filtered_events]

            elif tab == "by_id":
                eid = int(self.entry_search_id.get().strip())
                self.selected_assoc_event_id = eid
                info = self.observatory.query_event(eid)
                if info:
                    visited = 1
                    status_ev = info.get("status", "Active")
                    cd = info.get("current_data", {})
                    nm = info.get("node_metrics", {})
                    d = info.get("node_depth", nm.get("depth", 0))
                    h = info.get("height", nm.get("height", 0))
                    bf = info.get("balance_factor", nm.get("balance_factor", 0))
                    if status_ev == "Active":
                        detail_str = f"M{cd.get('magnitude')} · {cd.get('depth')}km · prof={d} · h={h} · FB={bf}"
                        ev_dummy = self.observatory.events_dict.get(eid)
                    else:
                        detail_str = f"M{cd.get('magnitude')} · {cd.get('depth')}km · [{status_ev}]"
                        ev_dummy = info.get("event_data")

                    if ev_dummy:
                        results = [{"event": ev_dummy, "visited": visited, "detail": detail_str}]
                    self._render_association_details(eid)
                else:
                    messagebox.showinfo("No encontrado", f"El identificador {eid} no existe en ningún catálogo (Activo, Archivados o Eliminados).")

            elif tab == "assoc":
                eid = int(self.entry_target_id.get().strip())
                self.selected_assoc_event_id = eid
                report, visited = self.observatory.query_event_associations(eid)
                target_ev = report.get("event")
                if target_ev:
                    role_str = "Referencia" if report.get("referenced_by") else "Réplica" if report.get("chosen_reference") else "Independiente"
                    results = [{"event": target_ev, "visited": visited, "detail": f"Rol: {role_str} · cand: {len(report.get('candidates', []))}"}]
                self._render_association_details(eid)

            elif tab == "costly":
                l_val = int(self.entry_limit_l.get().strip())
                if hasattr(self.observatory, 'limit'):
                    self.observatory.limit = l_val
                costly_items, visited = self.observatory.query_costly_high_priority_events()
                self.chip_costly_count.configure(text=f"{len(costly_items)} costosos P3·depth>L")
                results = [
                    {
                        "event": item["event"],
                        "visited": item["visited_nodes"],
                        "detail": f"prof={item['depth']} > L={item['limit']}"
                    }
                    for item in costly_items
                ]

            self.last_visited_nodes = visited
            self.current_query_results = results
            self.badge_visited_nodes.configure(text=f"◉ visitados AVL: {visited} nodos")
            self._render_table_rows(results)

        except Exception as ex:
            messagebox.showerror("Error en Consulta", f"No se pudo completar la consulta:\n{ex}")

    def _render_table_rows(self, results: list[dict]):
        """Dibuja las filas de resultados en la tabla."""
        for widget in self.scroll_table_rows.winfo_children():
            widget.destroy()

        if not results:
            empty_lbl = ctk.CTkLabel(
                self.scroll_table_rows,
                text="No se encontraron eventos coincidentes para los criterios seleccionados.",
                font=ctk.CTkFont(family=FONT_MAIN, size=11),
                text_color=TEXT_MUTED
            )
            empty_lbl.pack(pady=20)
            return

        for idx, item in enumerate(results, start=1):
            ev: Event = item["event"]
            detail = item.get("detail", f"M{ev.magnitude} · {ev.depth}km")
            visited_cnt = item.get("visited", "-")

            row_frame = ctk.CTkFrame(self.scroll_table_rows, fg_color="#081018" if idx % 2 == 0 else "transparent", corner_radius=4)
            row_frame.pack(fill="x", pady=1)

            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=3)
            row_frame.grid_columnconfigure(3, weight=3)
            row_frame.grid_columnconfigure(4, weight=2)
            row_frame.grid_columnconfigure(5, weight=2)

            # Clic en fila para explorar asociaciones inmediatamente
            row_frame.bind("<Button-1>", lambda e, eid=ev.id: self._on_row_clicked(eid))

            # Columna 0: Índice #
            lbl_idx = ctk.CTkLabel(row_frame, text=str(idx), font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=TEXT_MUTED)
            lbl_idx.grid(row=0, column=0, sticky="w", padx=8, pady=4)
            lbl_idx.bind("<Button-1>", lambda e, eid=ev.id: self._on_row_clicked(eid))

            # Columna 1: ID
            lbl_id = ctk.CTkLabel(row_frame, text=f"EV-{ev.id}", font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color=TEXT_PRIMARY)
            lbl_id.grid(row=0, column=1, sticky="w", padx=8, pady=4)
            lbl_id.bind("<Button-1>", lambda e, eid=ev.id: self._on_row_clicked(eid))

            # Columna 2: Clave K=(P, M, I)
            k_tuple = ev.get_key() if hasattr(ev, 'get_key') else (ev.priority, ev.magnitude, ev.id)
            lbl_k = ctk.CTkLabel(row_frame, text=str(k_tuple), font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=ACCENT_CYAN)
            lbl_k.grid(row=0, column=2, sticky="w", padx=8, pady=4)
            lbl_k.bind("<Button-1>", lambda e, eid=ev.id: self._on_row_clicked(eid))

            # Columna 3: Detalle
            lbl_det = ctk.CTkLabel(row_frame, text=detail, font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED)
            lbl_det.grid(row=0, column=3, sticky="w", padx=8, pady=4)
            lbl_det.bind("<Button-1>", lambda e, eid=ev.id: self._on_row_clicked(eid))

            # Columna 4: Estado
            st_text = str(ev.attention_state)[:4].upper() if hasattr(ev, 'attention_state') else "PEND"
            st_color = "#ffb020" if "PEND" in st_text else SUCCESS if "REV" in st_text else TEXT_MUTED
            lbl_st = ctk.CTkLabel(row_frame, text=st_text, font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"), text_color=st_color)
            lbl_st.grid(row=0, column=4, sticky="w", padx=8, pady=4)
            lbl_st.bind("<Button-1>", lambda e, eid=ev.id: self._on_row_clicked(eid))

            # Columna 5: Nodos Visitados
            lbl_vis = ctk.CTkLabel(row_frame, text=str(visited_cnt), font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"), text_color="#ffb020", anchor="e")
            lbl_vis.grid(row=0, column=5, sticky="ew", padx=8, pady=4)
            lbl_vis.bind("<Button-1>", lambda e, eid=ev.id: self._on_row_clicked(eid))

    def _on_row_clicked(self, eid: int):
        self.selected_assoc_event_id = eid
        self.combo_assoc_ids.set(str(eid))
        self._render_association_details(eid)

    # -------------------------------------------------------------------------
    # Renderizado de Asociación en AssociationExplorer
    # -------------------------------------------------------------------------
    def _on_assoc_id_selected(self, choice: str):
        try:
            eid = int(choice)
            self.selected_assoc_event_id = eid
            self._render_association_details(eid)
        except ValueError:
            pass

    def _render_association_details(self, event_id: int):
        """Consulta y renderiza los candidatos y réplicas del evento seleccionado."""
        if not self.observatory:
            return

        for w in self.frame_candidates_list.winfo_children():
            w.destroy()
        for w in self.frame_replicas_list.winfo_children():
            w.destroy()

        self.lbl_assoc_title.configure(text=f"Asociaciones · EV-{event_id}")

        report, visited = self.observatory.query_event_associations(event_id)
        self.badge_assoc_visited.configure(text=f"visitados: {visited}")

        target_event = report.get("event")
        if not target_event:
            ctk.CTkLabel(
                self.frame_candidates_list,
                text=f"El evento EV-{event_id} no fue encontrado.",
                font=ctk.CTkFont(family=FONT_MAIN, size=10),
                text_color=TEXT_MUTED
            ).pack(anchor="w", pady=4)
            return

        chosen = report.get("chosen_reference")
        candidates = report.get("candidates", [])
        replicas = report.get("referenced_by", [])

        # 1. Renderizar Candidatos Evaluados
        if not candidates and not chosen:
            ctk.CTkLabel(
                self.frame_candidates_list,
                text="Sin sismos candidatos (MA > MB, Δt ≤ 48h, d ≤ 40km).",
                font=ctk.CTkFont(family=FONT_MONO, size=10),
                text_color=TEXT_MUTED
            ).pack(anchor="w", pady=4)
        else:
            # Ganadora si existe
            if chosen and chosen.get("event"):
                c_ev = chosen["event"]
                c_st = chosen.get("status", "Activo").lower()
                dist = math.sqrt((c_ev.epicenter[0] - target_event.epicenter[0])**2 + (c_ev.epicenter[1] - target_event.epicenter[1])**2)
                dt_h = abs((target_event.date_time - c_ev.date_time).total_seconds()) / 3600.0

                f_win = ctk.CTkFrame(self.frame_candidates_list, fg_color="#0c281a", border_color=SUCCESS, border_width=1, corner_radius=6)
                f_win.pack(fill="x", pady=2)
                ctk.CTkLabel(f_win, text=f"✓ EV-{c_ev.id} · GANADORA", font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"), text_color=SUCCESS).pack(side="left", padx=8, pady=4)
                ctk.CTkLabel(f_win, text=f"{round(dist, 1)}km · {round(dt_h, 1)}h · {c_st}", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(side="right", padx=8, pady=4)

            # Otros candidatos evaluados
            for cand in candidates[:3]:
                c_ev = cand["event"]
                if chosen and chosen.get("event") and chosen["event"].id == c_ev.id:
                    continue  # Ya mostrado como ganador
                c_st = cand.get("status", "Activo").lower()
                dist = math.sqrt((c_ev.epicenter[0] - target_event.epicenter[0])**2 + (c_ev.epicenter[1] - target_event.epicenter[1])**2)
                dt_h = abs((target_event.date_time - c_ev.date_time).total_seconds()) / 3600.0

                f_cand = ctk.CTkFrame(self.frame_candidates_list, fg_color="#0b131c", border_color="#1e2d3d", border_width=1, corner_radius=6)
                f_cand.pack(fill="x", pady=2)
                ctk.CTkLabel(f_cand, text=f"EV-{c_ev.id} · M{c_ev.magnitude} > M{target_event.magnitude} ✓", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_PRIMARY).pack(side="left", padx=8, pady=4)
                ctk.CTkLabel(f_cand, text=f"{round(dist, 1)}km · {round(dt_h, 1)}h · {c_st}", font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=TEXT_MUTED).pack(side="right", padx=8, pady=4)

        # 2. Renderizar Réplicas que lo toman como referencia
        if not replicas:
            ctk.CTkLabel(
                self.frame_replicas_list,
                text="Ningún sismo posterior lo tiene como referencia.",
                font=ctk.CTkFont(family=FONT_MONO, size=10),
                text_color=TEXT_MUTED
            ).pack(anchor="w", pady=4)
        else:
            rep_bar = ctk.CTkFrame(self.frame_replicas_list, fg_color="transparent")
            rep_bar.pack(fill="x", pady=2)

            for r_item in replicas[:4]:
                r_ev = r_item["event"]
                r_st = "act" if "act" in r_item.get("status", "Activo").lower() else "arch"
                chip = ctk.CTkLabel(
                    rep_bar,
                    text=f"EV-{r_ev.id} · {r_st}",
                    font=ctk.CTkFont(family=FONT_MONO, size=9),
                    text_color=TEXT_PRIMARY,
                    fg_color="#101922",
                    corner_radius=4,
                    padx=6,
                    pady=2
                )
                chip.pack(side="left", padx=(0, 4))

            if len(replicas) > 4:
                ctk.CTkLabel(
                    rep_bar,
                    text=f"+{len(replicas) - 4} más",
                    font=ctk.CTkFont(family=FONT_MONO, size=9),
                    text_color=ACCENT_CYAN,
                    fg_color="#101922",
                    corner_radius=4,
                    padx=6,
                    pady=2
                ).pack(side="left")

    # =========================================================================
    # ACCIONES DE AUDITORÍA Y VERIFICACIÓN
    # =========================================================================

    def _handle_verify_structure(self):
        """Ejecuta la verificación estructural completa en el árbol y actualiza indicadores."""
        if not self.observatory:
            return

        report = self.observatory.verify_structure()
        has_errors = any("Error" in line for line in report)
        errors_list = [line for line in report if "Error" in line]

        now_str = datetime.now().strftime("%Y-%m-%dT%H:%MZ")
        node_count = len(self.observatory.events_dict) if hasattr(self.observatory, 'events_dict') else 0
        rot_count = sum(self.observatory.metrics.cases.values()) if (self.observatory.metrics and hasattr(self.observatory.metrics, 'cases')) else 0

        # Actualizar las 4 tarjetas técnicas
        bst_ok = not any("Orden" in line for line in errors_list)
        uniq_ok = not any("Identificador duplicado" in line for line in errors_list)
        h_ok = not any("Metadatos" in line or "Altura" in line for line in errors_list)
        bf_ok = not any("Balance" in line for line in errors_list)

        self._update_audit_pill(self.card_v_bst, "Orden BST global", "OK · inorden creciente K" if bst_ok else "✕ Error en orden", bst_ok)
        self._update_audit_pill(self.card_v_uniq, "Unicidad de IDs", "OK · 0 duplicados" if uniq_ok else "✕ IDs duplicados", uniq_ok)
        self._update_audit_pill(self.card_v_heights, "Alturas recalculadas", f"OK · {node_count}/{node_count} coinciden" if h_ok else "✕ Desfase de alturas", h_ok)
        self._update_audit_pill(self.card_v_bf, "Factores balance", "OK · BF ∈ [-1,1]" if bf_ok else "✕ Desbalance fuera de rango", bf_ok)

        # Actualizar barra de estado
        summary_text = f"reporte: auditoría {now_str} · {node_count} nodos · {len(errors_list)} errores · {rot_count} rotaciones totales"
        self.lbl_audit_summary.configure(text=summary_text, text_color=SUCCESS if not has_errors else DANGER)

        self.audit_status["errors"] = report
        self.audit_status["last_audit_time"] = now_str

        # Sincronizar contadores globales de la app
        self.refresh()
        if self.app and hasattr(self.app, 'refresh_all'):
            self.app.refresh_all()

        if has_errors:
            messagebox.showwarning("Inconsistencias Detectadas", "\n".join(errors_list[:5]))
        else:
            messagebox.showinfo("Auditoría Exitosa", "La estructura del árbol AVL cumple con todas las propiedades matemáticas de balance, alturas y orden lexicográfico K=(P, M, I).")

    def _update_audit_pill(self, pill_dict: dict, title: str, subtitle: str, is_ok: bool):
        color = SUCCESS if is_ok else DANGER
        prefix = "✓ " if is_ok else "✕ "
        bg_col = "#0c281a" if is_ok else "#2a1215"

        pill_dict["frame"].configure(fg_color=bg_col, border_color=color)
        pill_dict["title"].configure(text=f"{prefix}{title}", text_color=color)
        pill_dict["subtitle"].configure(text=subtitle)

    def _handle_download_audit_report(self):
        """Descarga el reporte de auditoría en formato estructurado JSON."""
        if not self.observatory:
            return

        metrics = getattr(self.observatory, 'metrics', None)
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "active_events_count": len(self.observatory.events_dict) if hasattr(self.observatory, 'events_dict') else 0,
            "archived_events_count": len(self.observatory.historic.archived) if (self.observatory.historic and hasattr(self.observatory.historic, 'archived')) else 0,
            "deleted_events_count": len(self.observatory.historic.deleted) if (self.observatory.historic and hasattr(self.observatory.historic, 'deleted')) else 0,
            "verification_log": self.audit_status["errors"] or self.observatory.verify_structure(),
            "cumulative_metrics": {
                "corrections": metrics.corrections_accepted if metrics else 0,
                "conflicts": metrics.conflicts if metrics else 0,
                "discarded": metrics.discarded_reports if metrics else 0,
                "rotation_cases": metrics.cases if metrics else {},
                "rotation_turns": metrics.turns if metrics else {}
            }
        }

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Guardar Reporte de Auditoría"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as fp:
                    json.dump(report_data, fp, indent=2, ensure_ascii=False)
                messagebox.showinfo("Exportación Exitosa", f"Reporte de auditoría guardado en:\n{path}")
            except Exception as ex:
                messagebox.showerror("Error al Exportar", f"No se pudo guardar el archivo:\n{ex}")

    def _handle_export_query(self):
        """Exporta los resultados de la consulta actual a un archivo JSON."""
        if not self.current_query_results:
            messagebox.showwarning("Sin Resultados", "No hay resultados de consulta disponibles para exportar.")
            return

        export_data = []
        for item in self.current_query_results:
            ev: Event = item["event"]
            export_data.append({
                "id": ev.id,
                "key": ev.get_key() if hasattr(ev, 'get_key') else (ev.priority, ev.magnitude, ev.id),
                "magnitude": ev.magnitude,
                "depth": ev.depth,
                "epicenter": ev.epicenter,
                "date_time": ev.date_time.isoformat() if hasattr(ev, 'date_time') else str(ev),
                "attention_state": getattr(ev, 'attention_state', 'Pending'),
                "visited_nodes": item.get("visited", 0)
            })

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title=f"Exportar Resultados ({self.active_query_tab})"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as fp:
                    json.dump(export_data, fp, indent=2, ensure_ascii=False)
                messagebox.showinfo("Exportación Exitosa", f"{len(export_data)} eventos exportados a:\n{path}")
            except Exception as ex:
                messagebox.showerror("Error al Exportar", f"No se pudo guardar el archivo:\n{ex}")
