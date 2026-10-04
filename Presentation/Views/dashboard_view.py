"""
Vista de Panel de Control · Consola Maestra
Demuestra el uso de los componentes atómicos (Card, MetricCard, SectionHeader,
StatusBadge, PrimaryButton, SecondaryButton, etc.) conectados en vivo al Observatorio.
"""

import customtkinter as ctk
from tkinter import messagebox

from Presentation.Components import (
    Card, MetricCard, SectionHeader, InfoBanner, KeyValueRow,
    PrimaryButton, SecondaryButton, WarningButton,
    StatusBadge, StatusDot, StyledLabel
)

FONT_MAIN = "Segoe UI"

class DashboardView(ctk.CTkFrame):
    """
    Vista de Panel de Control / Consola Ejecutiva.
    Muestra métricas clave en vivo usando la librería de componentes atómicos.
    """
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color="#070c12", corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory
        self._build_ui()

    def _build_ui(self):
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_container.pack(fill="both", expand=True, padx=16, pady=12)
        container = self.scroll_container

        # 1. Encabezado Molecular (SectionHeader)
        self.header = SectionHeader(
            container,
            category="SismoLab · Observatorio",
            title="Panel de Control · Consola Maestra",
            description="Métricas operativas del árbol AVL, catálogos históricos y colas en tiempo real."
        )
        self.header.pack(fill="x", pady=(0, 10))

        # Botón de acción en el encabezado
        btn_refresh = SecondaryButton(
            self.header,
            text="🔄 Refrescar",
            width=90,
            height=28,
            command=self.refresh
        )
        self.header.add_action(btn_refresh)

        # 2. Fila de Tarjetas de Métricas (MetricCards)
        metrics_grid = ctk.CTkFrame(container, fg_color="transparent")
        metrics_grid.pack(fill="x", pady=(0, 12))
        metrics_grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="metric_cols")

        # Card 1: Eventos Activos
        self.card_active = MetricCard(
            metrics_grid,
            title="Sismos Activos",
            value="0",
            subtitle="Indexados en Árbol AVL",
            icon="🌳",
            badge_text="Activo",
            badge_variant="success"
        )
        self.card_active.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        # Card 2: Histórico
        self.card_archived = MetricCard(
            metrics_grid,
            title="Archivados",
            value="0",
            subtitle="En Catálogo Histórico",
            icon="📦",
            badge_text="Histórico",
            badge_variant="info"
        )
        self.card_archived.grid(row=0, column=1, padx=3, sticky="ew")

        # Card 3: Cola de Prioridad
        self.card_queue = MetricCard(
            metrics_grid,
            title="Cola Reportes",
            value="0",
            subtitle="Pendientes de procesar",
            icon="⏳",
            badge_text="P1-P3",
            badge_variant="warning"
        )
        self.card_queue.grid(row=0, column=2, padx=3, sticky="ew")

        # Card 4: Estado del Sistema
        self.card_status = MetricCard(
            metrics_grid,
            title="Balance AVL",
            value="Normal",
            subtitle="Modo Estrés Inactivo",
            icon="⚡",
            badge_text="OK",
            badge_variant="success"
        )
        self.card_status.grid(row=0, column=3, padx=(6, 0), sticky="ew")

        # 3. Fila de Paneles Intermedios (Dos Columnas)
        panels_row = ctk.CTkFrame(container, fg_color="transparent")
        panels_row.pack(fill="x", pady=(0, 10))
        panels_row.grid_columnconfigure(0, weight=3, uniform="bottom_cols")
        panels_row.grid_columnconfigure(1, weight=2, uniform="bottom_cols")

        # Panel Izquierdo: Ficha del Observatorio y Estado
        self.left_card = Card(panels_row)
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        StyledLabel(self.left_card, text="ESTADO OPERACIONAL", variant="tag").pack(anchor="w", padx=16, pady=(12, 2))
        StyledLabel(self.left_card, text="Detalles del Sistema Sismológico", variant="h2").pack(anchor="w", padx=16, pady=(0, 8))

        # Filas clave-valor
        self.kv_clock = KeyValueRow(self.left_card, key="Reloj de Simulación (UTC):", value="--", is_highlighted=True)
        self.kv_clock.pack(fill="x", padx=16, pady=2)

        self.kv_deleted = KeyValueRow(self.left_card, key="Eventos Eliminados:", value="0")
        self.kv_deleted.pack(fill="x", padx=16, pady=2)

        self.kv_stations = KeyValueRow(self.left_card, key="Estaciones Sísmicas Activas:", value="0")
        self.kv_stations.pack(fill="x", padx=16, pady=2)

        self.kv_zones = KeyValueRow(self.left_card, key="Zonas Geográficas Configuradas:", value="0")
        self.kv_zones.pack(fill="x", padx=16, pady=2)

        # Banner informativo atómico dentro del panel
        self.banner = InfoBanner(
            self.left_card,
            title="Consistencia Estructural Verificada",
            message="El observatorio mantiene la propiedad AVL balanceada (|FB| <= 1).",
            variant="success"
        )
        self.banner.pack(fill="x", padx=16, pady=(8, 10))

        # Panel Derecho: Accesos Rápidos
        self.right_card = Card(panels_row)
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        StyledLabel(self.right_card, text="ACCIONES RÁPIDAS", variant="tag").pack(anchor="w", padx=16, pady=(12, 2))
        StyledLabel(self.right_card, text="Navegación Modular", variant="h2").pack(anchor="w", padx=16, pady=(0, 8))

        # Botones de navegación usando los botones atómicos
        PrimaryButton(
            self.right_card,
            text="🌳 Ver Árbol AVL",
            height=32,
            command=lambda: self.app.switch_view("arboles") if self.app else None
        ).pack(fill="x", padx=16, pady=3)

        SecondaryButton(
            self.right_card,
            text="🗺️ Ver Mapa Sísmico",
            height=32,
            command=lambda: self.app.switch_view("mapa") if self.app else None
        ).pack(fill="x", padx=16, pady=3)

        SecondaryButton(
            self.right_card,
            text="📋 Administrar Eventos",
            height=32,
            command=lambda: self.app.switch_view("eventos") if self.app else None
        ).pack(fill="x", padx=16, pady=3)

        SecondaryButton(
            self.right_card,
            text="🔎 Ejecutar Consultas",
            height=32,
            command=lambda: self.app.switch_view("consultas") if self.app else None
        ).pack(fill="x", padx=16, pady=3)

        # 4. Sección de Parámetros Operativos Modificables
        self.params_card = Card(container)
        self.params_card.pack(fill="x", pady=(0, 4))

        head_p = ctk.CTkFrame(self.params_card, fg_color="transparent")
        head_p.pack(fill="x", padx=16, pady=(10, 4))
        StyledLabel(head_p, text="PARÁMETROS DEL SISTEMA", variant="tag").pack(anchor="w", pady=(0, 2))
        StyledLabel(head_p, text="Configuración Operativa Modificable", variant="h2").pack(anchor="w", pady=(0, 2))
        StyledLabel(
            head_p,
            text="Modifica los umbrales del observatorio en vivo. Cada cambio se registra en la pila y se puede revertir con '↩ Deshacer'.",
            variant="body",
            text_color="#8a9bb0"
        ).pack(anchor="w")

        params_grid = ctk.CTkFrame(self.params_card, fg_color="transparent")
        params_grid.pack(fill="x", padx=12, pady=(6, 12))
        params_grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="param_cols")

        # 1. Límite L
        self.lbl_val_l, self.entry_l = self._create_param_box(
            params_grid, col=0,
            title="Límite L", code="L",
            desc="Capacidad / Profundidad", unit="niveles",
            accent_color="#22d3ee",
            on_confirm=self._on_set_limit
        )

        # 2. Ventana W
        self.lbl_val_w, self.entry_w = self._create_param_box(
            params_grid, col=1,
            title="Ventana W", code="W",
            desc="Tiempo máx. réplicas", unit="horas",
            accent_color="#f59e0b",
            on_confirm=self._on_set_max_time
        )

        # 3. Radio R
        self.lbl_val_r, self.entry_r = self._create_param_box(
            params_grid, col=2,
            title="Radio R", code="R",
            desc="Distancia réplicas", unit="km",
            accent_color="#a855f7",
            on_confirm=self._on_set_distance_epicenter
        )

        # 4. Antigüedad T
        self.lbl_val_t, self.entry_t = self._create_param_box(
            params_grid, col=3,
            title="Antigüedad T", code="T",
            desc="Edad máx. en árbol", unit="horas",
            accent_color="#2ecc71",
            on_confirm=self._on_set_max_tree_age
        )

        self.refresh()

    def _create_param_box(self, parent, col, title, code, desc, unit, accent_color, on_confirm):
        box = ctk.CTkFrame(parent, fg_color="#080e15", border_color="#1a2736", border_width=1, corner_radius=8)
        box.grid(row=0, column=col, padx=4, sticky="nsew")

        top_bar = ctk.CTkFrame(box, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(8, 1))

        ctk.CTkLabel(
            top_bar, text=f"• {code}",
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            text_color=accent_color
        ).pack(side="left")

        ctk.CTkLabel(
            box, text=title,
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            text_color="#e8eef3"
        ).pack(anchor="w", padx=10, pady=(0, 1))

        ctk.CTkLabel(
            box, text=desc,
            font=ctk.CTkFont(family=FONT_MAIN, size=10),
            text_color="#8a9bb0"
        ).pack(anchor="w", padx=10, pady=(0, 4))

        val_frame = ctk.CTkFrame(box, fg_color="transparent")
        val_frame.pack(fill="x", padx=10, pady=(2, 6))

        lbl_val = ctk.CTkLabel(
            val_frame, text="--",
            font=ctk.CTkFont(family=FONT_MAIN, size=18, weight="bold"),
            text_color="#ffffff"
        )
        lbl_val.pack(side="left")

        ctk.CTkLabel(
            val_frame, text=f" {unit}",
            font=ctk.CTkFont(family=FONT_MAIN, size=11),
            text_color="#8a9bb0"
        ).pack(side="left", pady=(4, 0))

        ctrl_frame = ctk.CTkFrame(box, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=(0, 10))

        entry = ctk.CTkEntry(
            ctrl_frame, height=28,
            placeholder_text="Nuevo valor",
            justify="center",
            fg_color="#101922",
            border_color="#1a2736",
            text_color="#e8eef3",
            font=ctk.CTkFont(family=FONT_MAIN, size=11)
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn = ctk.CTkButton(
            ctrl_frame, text="✓ Set",
            width=48, height=28,
            corner_radius=6,
            fg_color="#142436",
            hover_color="#1e3a5a",
            text_color=accent_color,
            border_width=1,
            border_color=accent_color,
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            command=lambda: on_confirm(entry)
        )
        btn.pack(side="right")
        entry.bind("<Return>", lambda e: on_confirm(entry))

        return lbl_val, entry

    def _on_set_limit(self, entry):
        if not self.observatory:
            return
        text = entry.get().strip()
        try:
            val = int(text)
            if val <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Valor Inválido", "El Límite L debe ser un número entero mayor a 0.")
            return

        old_val = self.observatory.limit
        if old_val == val:
            return
        self.observatory.limit = val
        entry.delete(0, "end")
        if self.app:
            self.app.refresh_all()
        messagebox.showinfo(
            "Parámetro Actualizado",
            f"Límite L modificado de {old_val} a {val}.\n\nPuedes presionar '↩ Deshacer' en la barra superior para revertir este cambio."
        )

    def _on_set_max_time(self, entry):
        if not self.observatory:
            return
        text = entry.get().strip()
        try:
            val = float(text)
            if val <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Valor Inválido", "La Ventana de Tiempo W debe ser un número positivo mayor a 0 horas.")
            return

        old_val = self.observatory.max_time
        if old_val == val:
            return
        self.observatory.max_time = val
        entry.delete(0, "end")
        if self.app:
            self.app.refresh_all()
        messagebox.showinfo(
            "Parámetro Actualizado",
            f"Ventana W modificada de {old_val}h a {val}h.\n\nPuedes presionar '↩ Deshacer' en la barra superior para revertir este cambio."
        )

    def _on_set_distance_epicenter(self, entry):
        if not self.observatory:
            return
        text = entry.get().strip()
        try:
            val = float(text)
            if val <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Valor Inválido", "El Radio de Epicentro R debe ser un número positivo mayor a 0 km.")
            return

        old_val = self.observatory.distance_epicenter
        if old_val == val:
            return
        self.observatory.distance_epicenter = val
        entry.delete(0, "end")
        if self.app:
            self.app.refresh_all()
        messagebox.showinfo(
            "Parámetro Actualizado",
            f"Radio R modificado de {old_val} km a {val} km.\n\nPuedes presionar '↩ Deshacer' en la barra superior para revertir este cambio."
        )

    def _on_set_max_tree_age(self, entry):
        if not self.observatory:
            return
        text = entry.get().strip()
        try:
            val = int(text)
            if val <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Valor Inválido", "La Antigüedad en Árbol T debe ser un número entero mayor a 0 horas.")
            return

        old_val = self.observatory.max_tree_age
        if old_val == val:
            return
        self.observatory.max_tree_age = val
        entry.delete(0, "end")
        if self.app:
            self.app.refresh_all()
        messagebox.showinfo(
            "Parámetro Actualizado",
            f"Antigüedad T modificada de {old_val}h a {val}h.\n\nPuedes presionar '↩ Deshacer' en la barra superior para revertir este cambio."
        )

    def refresh(self):
        """Sincroniza todas las métricas atómicas con el Observatorio en vivo."""
        if not self.observatory:
            return

        # 1. Total sismos activos
        active_count = len(getattr(self.observatory, "events_dict", {}))
        self.card_active.set_value(active_count)

        # 2. Total archivados
        historic = getattr(self.observatory, "historic", None)
        archived_count = len(historic.archived) if historic and hasattr(historic, "archived") else 0
        self.card_archived.set_value(archived_count)

        deleted_count = len(historic.deleted) if historic and hasattr(historic, "deleted") else 0
        self.kv_deleted.set_value(str(deleted_count))

        # 3. Cola de reportes
        queue = getattr(self.observatory, "report_queue", None)
        if hasattr(queue, "current_reports") and isinstance(queue.current_reports, list):
            queue_count = len(queue.current_reports)
        elif isinstance(queue, list):
            queue_count = len(queue)
        else:
            queue_count = 0
        self.card_queue.set_value(queue_count)

        # 4. Modo estrés / Balance AVL
        stress = getattr(self.observatory, "stress_mode", False)
        if stress:
            self.card_status.set_value("Estrés")
            self.card_status.set_subtitle("Modo desbalance activo")
            self.card_status.set_badge("Desbalance", "danger")
        else:
            self.card_status.set_value("Normal")
            self.card_status.set_subtitle("AVL balanceado")
            self.card_status.set_badge("OK", "success")

        # 5. Reloj de simulación
        clock = getattr(self.observatory, "clock_simulation", None)
        clock_str = clock.strftime("%Y-%m-%d %H:%M:%S") if clock else "--"
        self.kv_clock.set_value(clock_str)

        # 6. Estaciones y Zonas
        stations = getattr(self.observatory, "stations", {})
        self.kv_stations.set_value(str(len(stations)))

        geo_map = getattr(self.observatory, "geographical_map", None)
        zones = getattr(geo_map, "zones", []) if geo_map else []
        self.kv_zones.set_value(str(len(zones)))

        # 7. Parámetros Modificables
        if hasattr(self, "lbl_val_l"):
            self.lbl_val_l.configure(text=str(getattr(self.observatory, "limit", 3)))
        if hasattr(self, "lbl_val_w"):
            self.lbl_val_w.configure(text=f"{getattr(self.observatory, 'max_time', 48.0):.1f}")
        if hasattr(self, "lbl_val_r"):
            self.lbl_val_r.configure(text=f"{getattr(self.observatory, 'distance_epicenter', 40.0):.1f}")
        if hasattr(self, "lbl_val_t"):
            self.lbl_val_t.configure(text=str(getattr(self.observatory, "max_tree_age", 72)))
