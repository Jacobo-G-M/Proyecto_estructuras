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

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=15)
        self.main_container.grid_rowconfigure(2, weight=1)
        self.main_container.grid_columnconfigure(0, weight=3) # Área de Árboles
        self.main_container.grid_columnconfigure(1, weight=1) # Inspector

        self._build_header()
        self._build_metrics()
        self._build_canvases()
        self._build_inspector()

        # Seleccionar el primer nodo por defecto si existe
        self._select_default_node()
        self.refresh()

    def _select_default_node(self):
        if self.observatory and self.observatory.tree and self.observatory.tree.root:
            self.selected_event_id = self.observatory.tree.root.id

    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Títulos
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="PRESENTATION / VIEWS / TREE_VIEW.PY - OPERATIVO", font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"), text_color="#22d3ee").pack(anchor="w")
        ctk.CTkLabel(title_box, text="Árboles · Inspección Profunda", font=ctk.CTkFont(family=FONT_MAIN, size=20, weight="bold"), text_color="#e8eef3").pack(anchor="w")
        ctk.CTkLabel(title_box, text="Visualizador activo AVL vs BST conectado al Observatorio en tiempo real.", font=ctk.CTkFont(family=FONT_MAIN, size=11), text_color="#8a9bb0").pack(anchor="w")

        # Toggles Solo AVL / AVL vs BST
        toggle_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        toggle_box.pack(side="right", anchor="s", pady=5)
        
        self.btn_solo_avl = ctk.CTkButton(
            toggle_box, text="Solo AVL", width=90, height=28,
            fg_color="#111c28", text_color="#8a9bb0", hover_color="#1e2d3d",
            command=self._on_toggle_solo_avl
        )
        self.btn_solo_avl.pack(side="left", padx=2)
        
        self.btn_side_by_side = ctk.CTkButton(
            toggle_box, text="AVL vs BST lado a lado", width=150, height=28,
            fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(weight="bold"),
            command=self._on_toggle_side_by_side
        )
        self.btn_side_by_side.pack(side="left", padx=2)

    def _build_metrics(self):
        self.metrics_container = ctk.CTkFrame(self.main_container, fg_color="#0e1620", border_color="#1e2d3d", border_width=1, corner_radius=10)
        self.metrics_container.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Fila 1: Números grandes
        self.metrics_top = ctk.CTkFrame(self.metrics_container, fg_color="transparent")
        self.metrics_top.pack(fill="x", pady=10, padx=15)
        self.metrics_top.grid_columnconfigure(list(range(5)), weight=1)
        
        self.metric_labels = {}
        metric_defs = [
            ("height", "Altura AVL", "#22d3ee"),
            ("nodes", "Nodos", "#e8eef3"),
            ("leaves", "Hojas", "#e8eef3"),
            ("max_depth", "Prof. máx", "#e8eef3"),
            ("costly", "Costosos P3>L", "#ff7a1a")
        ]
        
        for i, (key, title, color) in enumerate(metric_defs):
            f = ctk.CTkFrame(self.metrics_top, fg_color="transparent")
            f.grid(row=0, column=i, sticky="w")
            lbl_val = ctk.CTkLabel(f, text="--", font=ctk.CTkFont(family=FONT_MAIN, size=22, weight="bold"), text_color=color)
            lbl_val.pack(anchor="w")
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(family=FONT_MAIN, size=10), text_color="#8a9bb0").pack(anchor="w")
            self.metric_labels[key] = lbl_val

        # Fila 2: Recorridos
        self.metrics_bot = ctk.CTkFrame(self.metrics_container, fg_color="transparent")
        self.metrics_bot.pack(fill="x", pady=(0, 10), padx=15)
        self.metrics_bot.grid_columnconfigure(list(range(4)), weight=1)
        
        self.trav_labels = {}
        for i, trav in enumerate(["INORDEN", "PREORDEN", "POSTORDEN", "POR NIVELES"]):
            box = ctk.CTkFrame(self.metrics_bot, fg_color="#070c12", border_color="#1e2d3d", border_width=1, corner_radius=6)
            box.grid(row=0, column=i, sticky="ew", padx=5)
            ctk.CTkLabel(box, text=trav, font=ctk.CTkFont(family=FONT_MAIN, size=9, weight="bold"), text_color="#22d3ee").pack(side="left", padx=8, pady=4)
            lbl_text = ctk.CTkLabel(box, text="--", font=ctk.CTkFont(family=FONT_MONO, size=9), text_color="#8a9bb0")
            lbl_text.pack(side="left", padx=(0, 8))
            self.trav_labels[trav] = lbl_text

    def _build_canvases(self):
        self.canvas_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.canvas_container.grid(row=2, column=0, sticky="nsew", padx=(0, 15))
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(1, weight=1)

        # AVL Frame
        self.avl_frame = ctk.CTkFrame(self.canvas_container, fg_color="#0e1620", border_color="#1e2d3d", border_width=1, corner_radius=10)
        self.avl_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._add_canvas_header(self.avl_frame, "AVL · balanceado", "BF∈[-1,1] ✓", "#2ecc71")
        self.avl_canvas = tk.Canvas(self.avl_frame, bg="#0e1620", highlightthickness=0)
        self.avl_canvas.pack(fill="both", expand=True)
        self.avl_canvas.bind("<Configure>", lambda e: self._redraw_trees())

        # BST Frame
        self.bst_frame = ctk.CTkFrame(self.canvas_container, fg_color="#0e1620", border_color="#1e2d3d", border_width=1, corner_radius=10)
        self.bst_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self._add_canvas_header(self.bst_frame, "BST · sin balanceo", "degradado ⚠", "#ff3b5c")
        self.bst_canvas = tk.Canvas(self.bst_frame, bg="#0e1620", highlightthickness=0)
        self.bst_canvas.pack(fill="both", expand=True)
        self.bst_canvas.bind("<Configure>", lambda e: self._redraw_trees())

    def _add_canvas_header(self, parent, title, badge, badge_color):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"), text_color="#e8eef3").pack(side="left")
        badge_f = ctk.CTkFrame(f, fg_color="transparent", border_color=badge_color, border_width=1, corner_radius=4)
        badge_f.pack(side="left", padx=8)
        ctk.CTkLabel(badge_f, text=badge, font=ctk.CTkFont(size=10, weight="bold"), text_color=badge_color).pack(padx=4, pady=1)

    def _build_inspector(self):
        self.inspector_frame = ctk.CTkFrame(self.main_container, fg_color="#0e1620", border_color="#1e2d3d", border_width=1, corner_radius=10)
        self.inspector_frame.grid(row=2, column=1, sticky="nsew")
        
        # Header del inspector
        h = ctk.CTkFrame(self.inspector_frame, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=12)
        ctk.CTkFrame(h, width=8, height=8, corner_radius=4, fg_color="#ff3b5c").pack(side="left", padx=5)
        ctk.CTkLabel(h, text="Inspector de Nodo", font=ctk.CTkFont(family=FONT_MAIN, size=13, weight="bold"), text_color="#e8eef3").pack(side="left")
        
        # Badge Naranja / Cyan dinámico
        self.badge_frame = ctk.CTkFrame(self.inspector_frame, fg_color="#1a1311", border_color="#ff7a1a", border_width=1, corner_radius=10)
        self.badge_frame.pack(padx=15, fill="x", pady=5)
        self.lbl_badge_title = ctk.CTkLabel(self.badge_frame, text="--", font=ctk.CTkFont(family=FONT_MONO, size=16, weight="bold"), text_color="#ff7a1a")
        self.lbl_badge_title.pack(pady=(10, 0))
        self.lbl_badge_sub = ctk.CTkLabel(self.badge_frame, text="--", font=ctk.CTkFont(size=9, weight="bold"), text_color="#ff7a1a")
        self.lbl_badge_sub.pack(pady=(0, 10))

        # Tabla de propiedades
        self.prop_labels = {}
        prop_keys = [
            ("key_K", "K=(P, M, I)", "#22d3ee"),
            ("event_id", "ID Evento", "#e8eef3"),
            ("magnitude", "Magnitud", "#e8eef3"),
            ("depth", "Prof. física H", "#e8eef3"),
            ("coords", "Coords X / Y", "#e8eef3"),
            ("datetime", "Fecha / Hora", "#e8eef3"),
            ("review", "Revisión vigente", "#e8eef3"),
            ("status", "Estado", "#ff7a1a"),
            ("stations", "Estaciones", "#e8eef3"),
            ("height", "Altura nodo", "#e8eef3"),
            ("balance", "Factor Balance", "#2ecc71"),
            ("node_depth", "Profundidad", "#ff3b5c")
        ]
        
        table_f = ctk.CTkFrame(self.inspector_frame, fg_color="transparent")
        table_f.pack(fill="both", expand=True, padx=20, pady=5)
        
        for key, title, def_color in prop_keys:
            row_f = ctk.CTkFrame(table_f, fg_color="transparent")
            row_f.pack(fill="x", pady=2)
            ctk.CTkLabel(row_f, text=title, text_color="#8a9bb0", font=ctk.CTkFont(family=FONT_MAIN, size=10)).pack(side="left")
            val_lbl = ctk.CTkLabel(row_f, text="--", text_color=def_color, font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"))
            val_lbl.pack(side="right")
            self.prop_labels[key] = val_lbl

        # Botones de Acción
        btns_f = ctk.CTkFrame(self.inspector_frame, fg_color="transparent")
        btns_f.pack(fill="x", padx=15, pady=15)
        self.btn_confirm = ctk.CTkButton(
            btns_f, text="✓ Revisado", height=32, corner_radius=6,
            fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(weight="bold"),
            command=self._on_mark_reviewed
        )
        self.btn_confirm.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.btn_delete = ctk.CTkButton(
            btns_f, text="Eliminar", height=32, corner_radius=6,
            fg_color="#111c28", border_color="#ff3b5c", border_width=1, text_color="#ff3b5c",
            command=self._on_delete_event
        )
        self.btn_delete.pack(side="right", expand=True, fill="x", padx=(5, 0))

    def on_node_click(self, event_id: int):
        """Callback al hacer clic en un nodo de cualquier árbol."""
        self.selected_event_id = event_id
        self._redraw_trees()
        self._refresh_inspector()

    def refresh(self):
        """Refresca métricas, árboles e inspector con el estado real del Observatorio."""
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

        # Recorrido por niveles (BFS)
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

        # AVL Canvas
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
                is_bst_degenerate=False
            )

        # BST Canvas (Construir árbol BST con los mismos eventos para comparativa)
        if self.show_side_by_side:
            w_bst = self.bst_canvas.winfo_width()
            h_bst = self.bst_canvas.winfo_height()
            if w_bst > 10 and h_bst > 10:
                self.bst_canvas.delete("all")
                TreeRenderer.draw_grid(self.bst_canvas, w_bst, h_bst)

                # Construir sombra BST
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
                    is_bst_degenerate=True
                )

    def _refresh_inspector(self):
        if not self.observatory:
            return

        # Si no hay evento seleccionado, intentar seleccionar el primero
        if self.selected_event_id is None or self.selected_event_id not in self.observatory.events_dict:
            if self.observatory.tree and self.observatory.tree.root:
                self.selected_event_id = self.observatory.tree.root.id
            else:
                self.selected_event_id = None

        if self.selected_event_id is None:
            self.lbl_badge_title.configure(text="Sin Selección")
            self.lbl_badge_sub.configure(text="Selecciona un nodo en el árbol")
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

        # Badge
        badge_text = f"({p}, {m:.1f}, {ev_id})"
        if is_costly:
            self.badge_frame.configure(fg_color="#1a1311", border_color="#ff7a1a")
            self.lbl_badge_title.configure(text=badge_text, text_color="#ff7a1a")
            self.lbl_badge_sub.configure(
                text=f"⚠ ACCESO COSTOSO · P3 depth {node_depth} > L{self.observatory.limit}",
                text_color="#ff7a1a"
            )
        else:
            self.badge_frame.configure(fg_color="#0b171f", border_color="#22d3ee")
            self.lbl_badge_title.configure(text=badge_text, text_color="#22d3ee")
            self.lbl_badge_sub.configure(
                text=f"ESTADO REGULAR · Profundidad {node_depth}",
                text_color="#22d3ee"
            )

        # Propiedades
        self.prop_labels["key_K"].configure(text=f"({p}, {m:.1f}, {ev_id})")
        self.prop_labels["event_id"].configure(text=f"EV-{ev_id}")
        self.prop_labels["magnitude"].configure(text=f"M {m:.1f}")
        self.prop_labels["depth"].configure(text=f"{depth_phys:.1f} km")
        self.prop_labels["coords"].configure(text=f"{x:.1f} · {y:.1f} km")
        self.prop_labels["datetime"].configure(text=dt.strftime("%Y-%m-%d T%H:%MZ"))
        self.prop_labels["review"].configure(text=f"{rev} revisiones")

        state_color = "#ff7a1a" if att_state.lower() == "pending" else "#2ecc71"
        self.prop_labels["status"].configure(text=att_state.upper(), text_color=state_color)

        st_names = [getattr(s, "name", str(s)) for s in stations] if stations else ["S-N1 ✓"]
        self.prop_labels["stations"].configure(text=" · ".join(st_names[:2]))

        self.prop_labels["height"].configure(text=str(h))
        bf_sign = "+" if bf > 0 else ""
        bf_str = f"{bf_sign}{bf} · {'equilibrado' if abs(bf) <= 1 else 'desbalance'}"
        bf_color = "#2ecc71" if abs(bf) <= 1 else "#ff3b5c"
        self.prop_labels["balance"].configure(text=bf_str, text_color=bf_color)

        depth_str = f"{node_depth} · límite L={self.observatory.limit}"
        depth_color = "#ff3b5c" if is_costly else "#e8eef3"
        self.prop_labels["node_depth"].configure(text=depth_str, text_color=depth_color)

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
        self.btn_side_by_side.configure(fg_color="#111c28", text_color="#8a9bb0", font=ctk.CTkFont(weight="normal"))
        self._redraw_trees()

    def _on_toggle_side_by_side(self):
        self.show_side_by_side = True
        self.bst_frame.grid()
        self.btn_side_by_side.configure(fg_color="#22d3ee", text_color="#06202a", font=ctk.CTkFont(weight="bold"))
        self.btn_solo_avl.configure(fg_color="#111c28", text_color="#8a9bb0", font=ctk.CTkFont(weight="normal"))
        self._redraw_trees()
