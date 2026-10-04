"""
Vista de Panel de Control · Consola Maestra
Demuestra el uso de los componentes atómicos (Card, MetricCard, SectionHeader,
StatusBadge, PrimaryButton, SecondaryButton, etc.) conectados en vivo al Observatorio.
"""

import customtkinter as ctk

from Presentation.Components import (
    Card, MetricCard, SectionHeader, InfoBanner, KeyValueRow,
    PrimaryButton, SecondaryButton, WarningButton,
    StatusBadge, StatusDot, StyledLabel
)

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
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=12)

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

        # 3. Fila de Paneles Inferiores (Dos Columnas)
        panels_row = ctk.CTkFrame(container, fg_color="transparent")
        panels_row.pack(fill="both", expand=True)
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

        self.refresh()

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
