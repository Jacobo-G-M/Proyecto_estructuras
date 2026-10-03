import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from collections import deque

from Presentation.Utils.tree_renderer import TreeRenderer
from Business.Structures.bst import BST
from Models.node import Node

FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

class TreeView(ctk.CTkFrame):
    def __init__(self, master, app=None, observatory=None, **kwargs):
        super().__init__(master, fg_color="#070c12", corner_radius=0, **kwargs)
        self.app = app
        self.observatory = observatory

        self.selected_event_id: int | None = None
        self.show_side_by_side: bool = True
        self.show_costly_halo: bool = True
        self.p_filter = {1: True, 2: True, 3: True}

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Contenedor principal con márgenes limpios
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=25, pady=15)
        self.main_container.grid_rowconfigure(2, weight=1)
        self.main_container.grid_columnconfigure(0, weight=3) # Árboles
        self.main_container.grid_columnconfigure(1, weight=1) # Inspector

        self._build_header()
        self._build_metrics_bar()
        self._build_canvases_area()
        self._build_inspector()
        self._build_footer()

        self._select_default_node()
        self.refresh()

    def _select_default_node(self):
        if self.observatory and self.observatory.tree and self.observatory.tree.root:
            self.selected_event_id = self.observatory.tree.root.id

    # -------------------------------------------------------------------------
    # 1. CABECERA CON BREADCRUMB Y TOGGLES
    # -------------------------------------------------------------------------
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Títulos
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left")
        
        ctk.CTkLabel(
            title_box, text="PRESENTATION / VIEWS / TREE_VIEW.PY · EXPANDIDO",
            font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#22d3ee"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_box, text="Árboles · Inspección Profunda",
            font=ctk.CTkFont(family=FONT_MAIN, size=22, weight="bold"), text_color="#e8eef3"
        ).pack(anchor="w", pady=(2, 0))
        
        ctk.CTkLabel(
            title_box, text="Canvas con pan & zoom, comparativa AVL vs BST y inspector lateral. Render: tree_renderer.py.",
            font=ctk.CTkFont(family=FONT_MAIN, size=11), text_color="#8a9bb0"
        ).pack(anchor="w", pady=(2, 0))

        # Toggles a la derecha
        toggle_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        toggle_box.pack(side="right", anchor="s", pady=5)
        
        self.btn_solo_avl = ctk.CTkButton(
            toggle_box, text="Solo AVL", width=80, height=28, corner_radius=6,
            fg_color="#101922", text_color="#8a9bb0", hover_color="#182736",
            font=ctk.CTkFont(family=FONT_MAIN, size=11),
            command=self._on_toggle_solo_avl
        )
        self.btn_solo_avl.pack(side="left", padx=3)
        
        self.btn_side_by_side = ctk.CTkButton(
            toggle_box, text="AVL vs BST lado a lado", width=145, height=28, corner_radius=6,
            fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            command=self._on_toggle_side_by_side
        )
        self.btn_side_by_side.pack(side="left", padx=3)

    # -------------------------------------------------------------------------
    # 2. BARRA DE MÉTRICAS (Exacta a la Imagen 4)
    # -------------------------------------------------------------------------
    def _build_metrics_bar(self):
        self.metrics_container = ctk.CTkFrame(
            self.main_container, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=12
        )
        self.metrics_container.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Fila 1: 5 Columnas divididas por líneas verticales
        self.metrics_top = ctk.CTkFrame(self.metrics_container, fg_color="transparent")
        self.metrics_top.pack(fill="x", padx=10, pady=12)
        self.metrics_top.grid_columnconfigure((0, 2, 4, 6, 8), weight=1)

        metric_defs = [
            ("height", "Altura AVL", "#22d3ee"),
            ("nodes", "Nodos", "#e8eef3"),
            ("leaves", "Hojas", "#e8eef3"),
            ("max_depth", "Prof. máx", "#e8eef3"),
            ("costly", "Costosos P3>L", "#ff7a1a")
        ]
        
        self.metric_labels = {}
        for idx, (key, title, color) in enumerate(metric_defs):
            col = idx * 2
            cell = ctk.CTkFrame(self.metrics_top, fg_color="transparent")
            cell.grid(row=0, column=col, sticky="w", padx=15)
            
            lbl_val = ctk.CTkLabel(
                cell, text="--", font=ctk.CTkFont(family=FONT_MAIN, size=24, weight="bold"), text_color=color
            )
            lbl_val.pack(anchor="w")
            
            ctk.CTkLabel(
                cell, text=title, font=ctk.CTkFont(family=FONT_MAIN, size=10), text_color="#8a9bb0"
            ).pack(anchor="w", pady=(2, 0))
            
            self.metric_labels[key] = lbl_val

            # Separador vertical fino
            if idx < len(metric_defs) - 1:
                sep = ctk.CTkFrame(self.metrics_top, width=1, height=45, fg_color="#1a2736")
                sep.grid(row=0, column=col + 1, sticky="ns", pady=2)

        # Línea divisoria horizontal
        h_line = ctk.CTkFrame(self.metrics_container, height=1, fg_color="#1a2736")
        h_line.pack(fill="x")

        # Fila 2: 4 Recorridos con pill cian y botón de copiar
        self.metrics_bot = ctk.CTkFrame(self.metrics_container, fg_color="transparent")
        self.metrics_bot.pack(fill="x", padx=10, pady=10)
        self.metrics_bot.grid_columnconfigure((0, 2, 4, 6), weight=1)

        self.trav_labels = {}
        for idx, trav in enumerate(["INORDEN", "PREORDEN", "POSTORDEN", "POR NIVELES"]):
            col = idx * 2
            box = ctk.CTkFrame(self.metrics_bot, fg_color="transparent")
            box.grid(row=0, column=col, sticky="ew", padx=8)

            # Badge cian
            badge = ctk.CTkFrame(box, fg_color="#101f2b", border_color="#1b4556", border_width=1, corner_radius=4)
            badge.pack(side="left", padx=(0, 8), pady=2)
            ctk.CTkLabel(
                badge, text=trav, font=ctk.CTkFont(family=FONT_MAIN, size=9, weight="bold"), text_color="#22d3ee"
            ).pack(padx=6, pady=2)

            # Texto de secuencia
            lbl_text = ctk.CTkLabel(
                box, text="--", font=ctk.CTkFont(family=FONT_MONO, size=9), text_color="#8a9bb0"
            )
            lbl_text.pack(side="left", fill="x", expand=True)
            self.trav_labels[trav] = lbl_text

            # Botón icono copiar ⧉
            btn_copy = ctk.CTkButton(
                box, text="⧉", width=20, height=20, fg_color="transparent",
                text_color="#8a9bb0", hover_color="#162432", font=ctk.CTkFont(size=11),
                command=lambda t=trav: self._copy_traversal_to_clipboard(t)
            )
            btn_copy.pack(side="right", padx=(5, 0))

            if idx < 3:
                sep2 = ctk.CTkFrame(self.metrics_bot, width=1, height=26, fg_color="#1a2736")
                sep2.grid(row=0, column=col + 1, sticky="ns")

    # -------------------------------------------------------------------------
    # 3. ZONA DE LIENZOS / ÁRBOLES (Exacta a la Imagen 3)
    # -------------------------------------------------------------------------
    def _build_canvases_area(self):
        self.canvas_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.canvas_container.grid(row=2, column=0, sticky="nsew", padx=(0, 15))
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(1, weight=1)

        # --- AVL Card (Izquierda) ---
        self.avl_frame = ctk.CTkFrame(
            self.canvas_container, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=12
        )
        self.avl_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # Header de la tarjeta AVL
        avl_head = ctk.CTkFrame(self.avl_frame, fg_color="transparent")
        avl_head.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            avl_head, text="AVL · balanceado · h=9",
            font=ctk.CTkFont(family=FONT_MAIN, size=13, weight="bold"), text_color="#e8eef3"
        ).pack(side="left")
        
        # Pill verde BF in [-1, 1]
        bf_pill = ctk.CTkFrame(avl_head, fg_color="#0d241d", border_color="#1b523e", border_width=1, corner_radius=4)
        bf_pill.pack(side="left", padx=8)
        self.lbl_avl_bf_badge = ctk.CTkLabel(
            bf_pill, text="BF ∈ [-1, 1] ✓", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#2ecc71"
        )
        self.lbl_avl_bf_badge.pack(padx=6, pady=2)

        # Botones 100% y recentrar a la derecha
        ctk.CTkButton(
            avl_head, text="↻ recentrar", width=70, height=24, corner_radius=4,
            fg_color="#101922", border_color="#1a2736", border_width=1,
            text_color="#8a9bb0", hover_color="#182736", font=ctk.CTkFont(family=FONT_MAIN, size=10),
            command=self._redraw_trees
        ).pack(side="right", padx=2)

        ctk.CTkButton(
            avl_head, text="⤢ 100%", width=60, height=24, corner_radius=4,
            fg_color="#101922", border_color="#1a2736", border_width=1,
            text_color="#8a9bb0", hover_color="#182736", font=ctk.CTkFont(family=FONT_MAIN, size=10)
        ).pack(side="right", padx=2)

        # Contenedor del Canvas AVL con controles flotantes
        avl_canvas_wrap = ctk.CTkFrame(self.avl_frame, fg_color="transparent")
        avl_canvas_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.avl_canvas = tk.Canvas(avl_canvas_wrap, bg="#081018", highlightthickness=0)
        self.avl_canvas.pack(fill="both", expand=True)
        self.avl_canvas.bind("<Configure>", lambda e: self._redraw_trees())

        # Controles flotantes en la esquina superior izquierda del Canvas AVL
        self.zoom_ctrl_frame = ctk.CTkFrame(
            self.avl_canvas, fg_color="#0e1722", border_color="#1a2736", border_width=1, corner_radius=6
        )
        self.zoom_ctrl_frame.place(x=12, y=12)
        
        ctk.CTkButton(self.zoom_ctrl_frame, text="+", width=28, height=24, corner_radius=3, fg_color="transparent", text_color="#e8eef3").pack(pady=1)
        ctk.CTkButton(self.zoom_ctrl_frame, text="−", width=28, height=24, corner_radius=3, fg_color="transparent", text_color="#e8eef3").pack(pady=1)
        ctk.CTkButton(self.zoom_ctrl_frame, text="✥ drag", width=42, height=22, corner_radius=3, fg_color="#162332", text_color="#22d3ee", font=ctk.CTkFont(size=9)).pack(padx=2, pady=2)

        # Barra de desplazamiento decorativa cian en la base del canvas
        self.scroll_bar_mock = ctk.CTkFrame(self.avl_frame, height=4, fg_color="#101a24", corner_radius=2)
        self.scroll_bar_mock.pack(fill="x", padx=15, pady=(0, 6))
        self.scroll_thumb_mock = ctk.CTkFrame(self.scroll_bar_mock, width=140, height=4, fg_color="#22d3ee", corner_radius=2)
        self.scroll_thumb_mock.pack(side="left", fill="y")
        self.scroll_bar_mock.pack_propagate(False)

        # Leyenda inferior en la tarjeta AVL
        legend_f = ctk.CTkFrame(self.avl_frame, fg_color="transparent")
        legend_f.pack(fill="x", padx=15, pady=(0, 10))

        # Dots P3, P2, P1
        ctk.CTkLabel(legend_f, text="• P3", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#ff3b5c").pack(side="left", padx=4)
        ctk.CTkLabel(legend_f, text="• P2", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#ff7a1a").pack(side="left", padx=4)
        ctk.CTkLabel(legend_f, text="• P1", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#2ecc71").pack(side="left", padx=4)

        # Icono y texto de costoso
        costly_badge = ctk.CTkFrame(legend_f, fg_color="transparent", border_color="#ffb020", border_width=1, corner_radius=4)
        costly_badge.pack(side="left", padx=10)
        ctk.CTkLabel(
            costly_badge, text="⬚ costoso P3 · depth > L=3",
            font=ctk.CTkFont(family=FONT_MAIN, size=9), text_color="#ffb020"
        ).pack(padx=5, pady=1)

        ctk.CTkLabel(
            legend_f, text="click nodo → inspector lateral",
            font=ctk.CTkFont(family=FONT_MAIN, size=9), text_color="#8a9bb0"
        ).pack(side="right")

        # --- BST Card (Derecha) ---
        self.bst_frame = ctk.CTkFrame(
            self.canvas_container, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=12
        )
        self.bst_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        bst_head = ctk.CTkFrame(self.bst_frame, fg_color="transparent")
        bst_head.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            bst_head, text="BST · sin balanceo",
            font=ctk.CTkFont(family=FONT_MAIN, size=13, weight="bold"), text_color="#e8eef3"
        ).pack(side="left")
        
        ctk.CTkLabel(
            bst_head, text="degradado · h=17 · BF máx +4 ⚠",
            font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#ff3b5c"
        ).pack(side="left", padx=10)

        # Canvas BST
        self.bst_canvas = tk.Canvas(self.bst_frame, bg="#081018", highlightthickness=0)
        self.bst_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.bst_canvas.bind("<Configure>", lambda e: self._redraw_trees())

        # Tarjeta inferior explicativa del BST (Exacta a la imagen)
        bst_info_card = ctk.CTkFrame(
            self.bst_frame, fg_color="#140f13", border_color="#361720", border_width=1, corner_radius=8
        )
        bst_info_card.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            bst_info_card, text="Misma secuencia de inserción",
            font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#ff3b5c"
        ).pack(anchor="w", padx=10, pady=(8, 0))

        ctk.CTkLabel(
            bst_info_card, text="AVL rota (RR×9, LL×12) · BST colapsa a lista → búsquedas O(n)",
            font=ctk.CTkFont(family=FONT_MAIN, size=9), text_color="#8a9bb0"
        ).pack(anchor="w", padx=10, pady=(2, 8))

    # -------------------------------------------------------------------------
    # 4. INSPECTOR DE NODO (Exacto a la Imagen 2)
    # -------------------------------------------------------------------------
    def _build_inspector(self):
        self.inspector_frame = ctk.CTkFrame(
            self.main_container, fg_color="#0b131c", border_color="#1a2736", border_width=1, corner_radius=12
        )
        self.inspector_frame.grid(row=2, column=1, sticky="nsew")
        
        # Header del inspector con punto rojo
        h = ctk.CTkFrame(self.inspector_frame, fg_color="transparent")
        h.pack(fill="x", padx=18, pady=(15, 10))
        
        dot = ctk.CTkFrame(h, width=8, height=8, corner_radius=4, fg_color="#ff3b5c")
        dot.pack(side="left", padx=(0, 6))
        
        ctk.CTkLabel(
            h, text="Inspector de Nodo",
            font=ctk.CTkFont(family=FONT_MAIN, size=13, weight="bold"), text_color="#e8eef3"
        ).pack(side="left")
        
        ctk.CTkLabel(
            h, text="click → fija",
            font=ctk.CTkFont(family=FONT_MAIN, size=10), text_color="#8a9bb0"
        ).pack(side="right")

        # Hero Card de nodo seleccionado
        self.hero_card = ctk.CTkFrame(
            self.inspector_frame, fg_color="#161217", border_color="#361a22", border_width=1, corner_radius=10
        )
        self.hero_card.pack(padx=15, fill="x", pady=6)

        self.lbl_hero_tuple = ctk.CTkLabel(
            self.hero_card, text="(3, 5.2, 10)",
            font=ctk.CTkFont(family=FONT_MAIN, size=18, weight="bold"), text_color="#ffffff"
        )
        self.lbl_hero_tuple.pack(pady=(12, 6))

        # Caja punteada de advertencia
        self.hero_badge_box = ctk.CTkFrame(
            self.hero_card, fg_color="#1e1308", border_color="#ffb020", border_width=1, corner_radius=6
        )
        self.hero_badge_box.pack(padx=15, pady=(0, 12), fill="x")

        self.lbl_hero_badge = ctk.CTkLabel(
            self.hero_badge_box, text="⚠ ACCESO COSTOSO · P3 depth 4 > L3",
            font=ctk.CTkFont(family=FONT_MAIN, size=9, weight="bold"), text_color="#ffb020"
        )
        self.lbl_hero_badge.pack(padx=8, pady=4)

        # Tabla densa de 12 propiedades
        self.prop_labels = {}
        prop_defs = [
            ("key_K", "K = (P, M, I)", "#22d3ee"),
            ("event_id", "ID Evento", "#ffffff"),
            ("magnitude", "Magnitud", "#ffffff"),
            ("depth", "Prof. física H", "#ffffff"),
            ("coords", "Coords X / Y", "#ffffff"),
            ("datetime", "Fecha / Hora", "#ffffff"),
            ("review", "Revisión vigente", "#ffffff"),
            ("status", "Estado", "#ff7a1a"),
            ("stations", "Estaciones", "#ffffff"),
            ("height", "Altura nodo", "#ffffff"),
            ("balance", "Factor Balance", "#2ecc71"),
            ("node_depth", "Profundidad", "#ff3b5c")
        ]

        table_f = ctk.CTkFrame(self.inspector_frame, fg_color="transparent")
        table_f.pack(fill="x", padx=18, pady=4)

        for key, title, def_color in prop_defs:
            row_f = ctk.CTkFrame(table_f, fg_color="transparent")
            row_f.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                row_f, text=title, text_color="#8a9bb0", font=ctk.CTkFont(family=FONT_MAIN, size=10)
            ).pack(side="left")
            
            val_lbl = ctk.CTkLabel(
                row_f, text="--", text_color=def_color, font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold")
            )
            val_lbl.pack(side="right")
            self.prop_labels[key] = val_lbl

        # Sección RESALTADO
        ctk.CTkLabel(
            self.inspector_frame, text="RESALTADO",
            font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#8a9bb0"
        ).pack(anchor="w", padx=18, pady=(10, 4))

        p_buttons_f = ctk.CTkFrame(self.inspector_frame, fg_color="transparent")
        p_buttons_f.pack(fill="x", padx=18, pady=2)

        self.btn_p1 = ctk.CTkButton(
            p_buttons_f, text="P1 on", width=65, height=24, corner_radius=6,
            fg_color="#2ecc71", text_color="#06202a", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"),
            command=lambda: self._toggle_p_filter(1)
        )
        self.btn_p1.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_p2 = ctk.CTkButton(
            p_buttons_f, text="P2 on", width=65, height=24, corner_radius=6,
            fg_color="#ff7a1a", text_color="#ffffff", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"),
            command=lambda: self._toggle_p_filter(2)
        )
        self.btn_p2.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_p3 = ctk.CTkButton(
            p_buttons_f, text="P3 on", width=65, height=24, corner_radius=6,
            fg_color="#ff3b5c", text_color="#ffffff", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"),
            command=lambda: self._toggle_p_filter(3)
        )
        self.btn_p3.pack(side="left", expand=True, fill="x", padx=2)

        # Toggle halo costoso
        halo_toggle_f = ctk.CTkFrame(
            self.inspector_frame, fg_color="#121a22", border_color="#ffb020", border_width=1, corner_radius=6
        )
        halo_toggle_f.pack(fill="x", padx=18, pady=8)

        self.btn_halo_switch = ctk.CTkButton(
            halo_toggle_f, text="●", width=24, height=18, corner_radius=9,
            fg_color="#ffb020", text_color="#121a22", font=ctk.CTkFont(size=10),
            command=self._toggle_costly_halo
        )
        self.btn_halo_switch.pack(side="left", padx=8, pady=4)

        ctk.CTkLabel(
            halo_toggle_f, text="halo costoso visible",
            font=ctk.CTkFont(family=FONT_MAIN, size=10), text_color="#ffb020"
        ).pack(side="left")

        # Botones de Acción inferior
        action_f = ctk.CTkFrame(self.inspector_frame, fg_color="transparent")
        action_f.pack(fill="x", padx=18, pady=(8, 4))

        self.btn_confirm = ctk.CTkButton(
            action_f, text="✓ Revisado", height=34, corner_radius=8,
            fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            command=self._on_mark_reviewed
        )
        self.btn_confirm.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_delete = ctk.CTkButton(
            action_f, text="Eliminar", height=34, corner_radius=8,
            fg_color="#111620", border_color="#ff3b5c", border_width=1,
            text_color="#ff3b5c", hover_color="#261016", font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            command=self._on_delete_event
        )
        self.btn_delete.pack(side="right", expand=True, fill="x", padx=(4, 0))

        ctk.CTkLabel(
            self.inspector_frame, text="via Observatory.mark_reviewed() / delete()",
            font=ctk.CTkFont(family=FONT_MAIN, size=9), text_color="#536477"
        ).pack(pady=(0, 10))

    # -------------------------------------------------------------------------
    # 5. FOOTER INFERIOR
    # -------------------------------------------------------------------------
    def _build_footer(self):
        self.footer_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ctk.CTkLabel(
            self.footer_frame,
            text="tree_view.py consume Observatory.get_tree_snapshot() · on_node_click(id) → inspector · export_traversal(tipo)",
            font=ctk.CTkFont(family=FONT_MONO, size=9), text_color="#536477"
        ).pack(side="left")

        ctk.CTkLabel(
            self.footer_frame,
            text="scrollbars + drag · nodos nunca se comprimen",
            font=ctk.CTkFont(family=FONT_MAIN, size=9), text_color="#536477"
        ).pack(side="right")

    # -------------------------------------------------------------------------
    # LÓGICA DE ACTUALIZACIÓN Y LLAMADAS AL BACKEND
    # -------------------------------------------------------------------------
    def on_node_click(self, event_id: int):
        self.selected_event_id = event_id
        self._redraw_trees()
        self._refresh_inspector()

    def refresh(self):
        self._refresh_metrics()
        self._redraw_trees()
        self._refresh_inspector()

    def _refresh_metrics(self):
        if not self.observatory or not self.observatory.tree:
            return

        inorder = self.observatory.tree.inorder()
        total_nodes = len(inorder)
        height_val = self.observatory.tree.height()
        leaves = sum(1 for n in inorder if n.is_leaf())
        depths = self.observatory.tree.get_all_nodes_with_depth()
        max_depth = max((d for _, d in depths), default=0)
        costly_list = self.observatory.get_costly_access()

        self.metric_labels["height"].configure(text=str(height_val))
        self.metric_labels["nodes"].configure(text=str(total_nodes))
        self.metric_labels["leaves"].configure(text=str(leaves))
        self.metric_labels["max_depth"].configure(text=str(max_depth))
        self.metric_labels["costly"].configure(text=str(len(costly_list)))

        # Actualizar recorridos
        def fmt_seq(nodes_list):
            if not nodes_list:
                return "--"
            items = []
            for n in nodes_list[:4]:
                ev = n.event
                items.append(f"({ev.priority},{ev.magnitude:.1f},{ev.id})")
            res = " -> ".join(items)
            return res + ("..." if len(nodes_list) > 4 else "")

        preorder = self.observatory.tree.preorder()
        postorder = self.observatory.tree.postorder()

        self.trav_labels["INORDEN"].configure(text=fmt_seq(inorder))
        self.trav_labels["PREORDEN"].configure(text=fmt_seq(preorder))
        self.trav_labels["POSTORDEN"].configure(text=fmt_seq(postorder))

        # BFS por niveles
        bfs_nodes = []
        if self.observatory.tree.root:
            q = deque([self.observatory.tree.root])
            while q:
                cur = q.popleft()
                bfs_nodes.append(cur)
                if cur.left_son:
                    q.append(cur.left_son)
                if cur.right_son:
                    q.append(cur.right_son)
        self.trav_labels["POR NIVELES"].configure(text=fmt_seq(bfs_nodes))

    def _redraw_trees(self):
        if not self.observatory:
            return

        costly_ids = self.observatory.get_costly_access()

        # Canvas AVL
        w_avl = self.avl_canvas.winfo_width()
        h_avl = self.avl_canvas.winfo_height()
        if w_avl > 10 and h_avl > 10:
            self.avl_canvas.delete("all")
            TreeRenderer.draw_grid(self.avl_canvas, w_avl, h_avl)
            root_avl = self.observatory.tree.root if self.observatory.tree else None
            TreeRenderer.render_tree(
                canvas=self.avl_canvas,
                root_node=root_avl,
                width=w_avl,
                height=h_avl,
                selected_event_id=self.selected_event_id,
                costly_ids=costly_ids,
                on_node_click=self.on_node_click,
                is_bst_degenerate=False,
                p_filter=self.p_filter,
                show_costly_halo=self.show_costly_halo
            )

        # Canvas BST
        if self.show_side_by_side:
            w_bst = self.bst_canvas.winfo_width()
            h_bst = self.bst_canvas.winfo_height()
            if w_bst > 10 and h_bst > 10:
                self.bst_canvas.delete("all")
                TreeRenderer.draw_grid(self.bst_canvas, w_bst, h_bst)

                shadow_bst = BST(id=99)
                for ev in self.observatory.events_dict.values():
                    shadow_bst.insert(Node(id=ev.id, event=ev))

                TreeRenderer.render_tree(
                    canvas=self.bst_canvas,
                    root_node=shadow_bst.root,
                    width=w_bst,
                    height=h_bst,
                    selected_event_id=self.selected_event_id,
                    costly_ids=costly_ids,
                    on_node_click=self.on_node_click,
                    is_bst_degenerate=True,
                    p_filter=self.p_filter,
                    show_costly_halo=self.show_costly_halo
                )

    def _refresh_inspector(self):
        if not self.observatory:
            return

        if self.selected_event_id is None or self.selected_event_id not in self.observatory.events_dict:
            if self.observatory.tree and self.observatory.tree.root:
                self.selected_event_id = self.observatory.tree.root.id
            else:
                self.selected_event_id = None

        if self.selected_event_id is None:
            self.lbl_hero_tuple.configure(text="Sin Selección")
            self.lbl_hero_badge.configure(text="Selecciona un nodo en el árbol")
            for lbl in self.prop_labels.values():
                lbl.configure(text="--")
            return

        data = self.observatory.query_event(self.selected_event_id)
        if not data:
            return

        costly_ids = self.observatory.get_costly_access()
        is_costly = self.selected_event_id in costly_ids

        ev_id = data["id"]
        p = data.get("priority", 1)
        m = data["current_data"]["magnitude"]
        depth_phys = data["current_data"]["depth"]
        x, y = data["current_data"]["epicenter"]
        dt = data["current_data"]["date_time"]
        rev = data.get("review", 1)
        att_state = data.get("attention_state", "Pending")
        stations = data.get("stations", [])
        h = data.get("height", 0)
        bf = data.get("balance_factor", 0)
        node_depth = data.get("node_depth", 0)

        # Hero Card
        self.lbl_hero_tuple.configure(text=f"({p}, {m:.1f}, {ev_id})")
        if is_costly:
            self.hero_card.configure(fg_color="#161217", border_color="#361a22")
            self.hero_badge_box.configure(fg_color="#1e1308", border_color="#ffb020")
            self.lbl_hero_badge.configure(
                text=f"⚠ ACCESO COSTOSO · P3 depth {node_depth} > L{self.observatory.limit}",
                text_color="#ffb020"
            )
        else:
            self.hero_card.configure(fg_color="#0d1720", border_color="#1b3644")
            self.hero_badge_box.configure(fg_color="#0e1f2b", border_color="#22d3ee")
            self.lbl_hero_badge.configure(
                text=f"ESTADO REGULAR · Profundidad {node_depth}",
                text_color="#22d3ee"
            )

        # Propiedades exactas
        self.prop_labels["key_K"].configure(text=f"({p}, {m:.1f}, {ev_id})")
        self.prop_labels["event_id"].configure(text=f"EV-{ev_id}")
        self.prop_labels["magnitude"].configure(text=f"M {m:.1f}")
        self.prop_labels["depth"].configure(text=f"{depth_phys:.1f} km")
        self.prop_labels["coords"].configure(text=f"{x:.1f} · {y:.1f} km")
        self.prop_labels["datetime"].configure(text=dt.strftime("%Y-%m-%d T%H:%MZ"))
        self.prop_labels["review"].configure(text=f"v{rev} · {rev}/3 estaciones")

        state_color = "#ff7a1a" if att_state.lower() == "pending" else "#2ecc71"
        self.prop_labels["status"].configure(text=att_state.upper(), text_color=state_color)

        st_names = [getattr(s, "name", str(s)) for s in stations] if stations else ["S-N1 ✓", "S-N2 ✓"]
        self.prop_labels["stations"].configure(text=" · ".join(st_names[:2]))

        self.prop_labels["height"].configure(text=str(h))
        bf_sign = "+" if bf > 0 else ""
        bf_str = f"{bf_sign}{bf} · {'equilibrado' if abs(bf) <= 1 else 'desbalanceado'}"
        bf_color = "#2ecc71" if abs(bf) <= 1 else "#ff3b5c"
        self.prop_labels["balance"].configure(text=bf_str, text_color=bf_color)

        depth_str = f"{node_depth} · límite L={self.observatory.limit}"
        depth_color = "#ff3b5c" if is_costly else "#ffffff"
        self.prop_labels["node_depth"].configure(text=depth_str, text_color=depth_color)

    # -------------------------------------------------------------------------
    # ACCIONES DE BOTONES
    # -------------------------------------------------------------------------
    def _toggle_p_filter(self, p: int):
        self.p_filter[p] = not self.p_filter[p]
        btn = {1: self.btn_p1, 2: self.btn_p2, 3: self.btn_p3}[p]
        active = self.p_filter[p]
        bg = {1: "#2ecc71", 2: "#ff7a1a", 3: "#ff3b5c"}[p] if active else "#1a2530"
        txt = "#06202a" if (p == 1 and active) else "#ffffff"
        btn.configure(fg_color=bg, text_color=txt, text=f"P{p} {'on' if active else 'off'}")
        self._redraw_trees()

    def _toggle_costly_halo(self):
        self.show_costly_halo = not self.show_costly_halo
        self.btn_halo_switch.configure(
            text="●" if self.show_costly_halo else "○",
            fg_color="#ffb020" if self.show_costly_halo else "#1a2530"
        )
        self._redraw_trees()

    def _copy_traversal_to_clipboard(self, trav_name: str):
        text = self.trav_labels[trav_name].cget("text")
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copiado", f"Recorrido {trav_name} copiado al portapapeles:\n\n{text}")

    def _on_mark_reviewed(self):
        if not self.observatory or self.selected_event_id is None:
            return
        success = self.observatory.mark_as_reviewed(self.selected_event_id)
        if success:
            messagebox.showinfo("Inspector", f"Evento EV-{self.selected_event_id} marcado como REVISADO.")
        if self.app:
            self.app.refresh_all()

    def _on_delete_event(self):
        if not self.observatory or self.selected_event_id is None:
            return
        confirm = messagebox.askyesno("Eliminar Evento", f"¿Seguro que deseas eliminar el evento EV-{self.selected_event_id}?")
        if confirm:
            try:
                self.observatory.remove_event(self.selected_event_id)
                self.selected_event_id = None
                if self.app:
                    self.app.refresh_all()
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al eliminar: {e}")

    def _on_toggle_solo_avl(self):
        self.show_side_by_side = False
        self.bst_frame.grid_remove()
        self.btn_solo_avl.configure(fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(weight="bold"))
        self.btn_side_by_side.configure(fg_color="#101922", text_color="#8a9bb0", font=ctk.CTkFont(weight="normal"))
        self._redraw_trees()

    def _on_toggle_side_by_side(self):
        self.show_side_by_side = True
        self.bst_frame.grid()
        self.btn_side_by_side.configure(fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(weight="bold"))
        self.btn_solo_avl.configure(fg_color="#101922", text_color="#8a9bb0", font=ctk.CTkFont(weight="normal"))
        self._redraw_trees()
