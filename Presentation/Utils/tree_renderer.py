import tkinter as tk
from typing import Callable, Any

class TreeRenderer:
    """
    Renderizador dinámico de alta fidelidad para árboles AVL y BST.
    Replica exactamente los estilos visuales de Banani:
    - Nodos con relleno saturado en AVL (P3 rojo, P2 naranja, P1 verde).
    - Nodos compactos oscuros en BST mostrando claramente su topología sin balancear y sin solapamiento.
    - Círculos de nodos con número de ID tanto en AVL como en BST para una visualización limpia y legible.
    - Selección activa con cuadrado redondeado sólido cian.
    - Halos de nodos costosos con cuadrado redondeado punteado ámbar/naranja.
    - Cuadrícula sutil de puntos de fondo.
    """

    @staticmethod
    def _draw_round_rectangle(
        canvas: tk.Canvas,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float = 8.0,
        **kwargs
    ):
        """Dibuja un cuadrado/rectángulo con esquinas redondeadas suaves en el canvas."""
        r = max(1.0, min(radius, abs(x2 - x1) / 2.0, abs(y2 - y1) / 2.0))
        points = [
            x1 + r, y1,
            x1 + r, y1,
            x2 - r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1 + r,
            x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    @staticmethod
    def draw_grid(
        canvas: tk.Canvas,
        width: int,
        height: int,
        step: int = 24,
        dot_color: str = "#121d28",
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ):
        """Dibuja la cuadrícula sutil de puntos oscuros con desplazamiento dinámico."""
        start_x = int(offset_x) % step
        start_y = int(offset_y) % step
        for x in range(start_x, width, step):
            for y in range(start_y, height, step):
                canvas.create_oval(x, y, x + 2, y + 2, fill=dot_color, outline="")

    @classmethod
    def render_tree(
        cls,
        canvas: tk.Canvas,
        root_node: Any,
        width: int,
        height: int,
        selected_event_id: int | None = None,
        costly_ids: list[int] | None = None,
        on_node_click: Callable[[int], None] | None = None,
        is_bst_degenerate: bool = False,
        p_filter: dict[int, bool] | None = None,
        show_costly_halo: bool = True,
        zoom: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0
    ):
        """
        Dibuja el árbol completo en el canvas de Tkinter con soporte para zoom y desplazamiento (pan/drag).
        """
        if root_node is None:
            canvas.create_text(
                width / 2, height / 2,
                text="Árbol vacío · Sin eventos activos",
                fill="#8a9bb0",
                font=("Segoe UI", 12, "italic")
            )
            return

        costly_ids = costly_ids or []
        p_filter = p_filter or {1: True, 2: True, 3: True}

        # 1. Obtener todos los nodos del árbol
        all_nodes = []
        def collect_nodes(curr):
            if curr is None:
                return
            all_nodes.append(curr)
            collect_nodes(curr.left_son)
            collect_nodes(curr.right_son)

        collect_nodes(root_node)

        # 2. Profundidades de cada nodo
        node_depths = {}
        def get_depths(curr, d=0):
            if curr is None:
                return
            node_depths[id(curr)] = d
            get_depths(curr.left_son, d + 1)
            get_depths(curr.right_son, d + 1)

        get_depths(root_node, 0)

        coords = {}

        if is_bst_degenerate:
            # --- LAYOUT PARA BST (Árbol binario sin balanceo con separación garantizada) ---
            node_radius = 26
            margin_y = 55
            min_node_step = 85
            level_height = 85
        else:
            # --- LAYOUT PARA AVL (Árbol balanceado) ---
            node_radius = 30
            margin_y = 60
            # Distancia horizontal mínima garantizada para evitar colisiones:
            # Con 95 px y r=30 (diámetro 60 px), hay más de 35 px de espacio libre entre círculos
            min_node_step = 95
            level_height = 95

        inorder_nodes = []
        def get_inorder(curr):
            if curr is None:
                return
            get_inorder(curr.left_son)
            inorder_nodes.append(curr)
            get_inorder(curr.right_son)

        get_inorder(root_node)
        total_inorder = len(inorder_nodes)

        step_x = min_node_step
        root_idx = inorder_nodes.index(root_node) if (root_node and root_node in inorder_nodes) else (total_inorder // 2)

        for idx, node in enumerate(inorder_nodes):
            lx = (idx - root_idx) * step_x if total_inorder > 1 else 0
            ly = node_depths[id(node)] * level_height

            nx = (width / 2) + offset_x + lx * zoom
            ny = margin_y + offset_y + ly * zoom
            coords[id(node)] = (nx, ny)

        # 3. Dibujar aristas / líneas conectoras
        line_w = max(1, min(4, int(2 * zoom)))
        def draw_edges(curr):
            if curr is None:
                return
            curr_x, curr_y = coords[id(curr)]
            for child in (curr.left_son, curr.right_son):
                if child is not None:
                    ch_x, ch_y = coords[id(child)]
                    if is_bst_degenerate:
                        line_color = "#422830"
                        dash_pattern = (3, 3) if child == curr.right_son else ()
                    else:
                        line_color = "#1c2e42"
                        dash_pattern = ()

                    canvas.create_line(
                        curr_x, curr_y, ch_x, ch_y,
                        fill=line_color,
                        width=line_w,
                        dash=dash_pattern
                    )
                    draw_edges(child)

        draw_edges(root_node)

        # 4. Dibujar nodos escalados
        r = max(20, min(44, int(node_radius * zoom)))
        pad_costly = max(9, int(14 * zoom))
        pad_sel = max(5, int(8 * zoom))
        corner_radius_costly = max(6, min(14, int(9 * zoom)))
        corner_radius_sel = max(5, min(12, int(7 * zoom)))
        font_sz_id = max(9, min(16, int(12 * zoom)))

        for node in all_nodes:
            nx, ny = coords[id(node)]
            ev = getattr(node, "event", None)
            event_id = getattr(ev, "id", node.id)
            priority = getattr(ev, "priority", 1)

            is_visible = p_filter.get(priority, True)

            if is_bst_degenerate:
                fill_color = "#14202c"
                outline_color = "#24374a"
                text_color = "#e8eef3"
            else:
                if not is_visible:
                    fill_color = "#0e1822"
                    outline_color = "#172635"
                    text_color = "#35485c"
                else:
                    if priority == 3:
                        fill_color = "#ff3b5c"
                    elif priority == 2:
                        fill_color = "#ff7a1a"
                    else:
                        fill_color = "#2ecc71"
                    outline_color = "#ffffff"
                    text_color = "#ffffff"

            tag_name = f"node_{event_id}"

            # Halo redondeado punteado de acceso costoso
            if show_costly_halo and event_id in costly_ids and not is_bst_degenerate and is_visible:
                cls._draw_round_rectangle(
                    canvas,
                    nx - r - pad_costly, ny - r - pad_costly,
                    nx + r + pad_costly, ny + r + pad_costly,
                    radius=corner_radius_costly,
                    outline="#ffb020",
                    width=2,
                    dash=(5, 4),
                    fill=""
                )

            # Recuadro redondeado sólido cian de selección activa
            if selected_event_id is not None and event_id == selected_event_id:
                cls._draw_round_rectangle(
                    canvas,
                    nx - r - pad_sel, ny - r - pad_sel,
                    nx + r + pad_sel, ny + r + pad_sel,
                    radius=corner_radius_sel,
                    outline="#22d3ee",
                    width=2,
                    fill=""
                )

            # Círculo del nodo
            canvas.create_oval(
                nx - r, ny - r, nx + r, ny + r,
                fill=fill_color,
                outline=outline_color if (selected_event_id == event_id or is_bst_degenerate) else fill_color,
                width=2 if selected_event_id == event_id else 1,
                tags=tag_name
            )

            # Texto dentro del nodo: ID del nodo limpio y legible
            canvas.create_text(
                nx, ny,
                text=f"{event_id}",
                fill=text_color,
                font=("Segoe UI", font_sz_id, "bold"),
                tags=tag_name
            )

            if on_node_click is not None:
                canvas.tag_bind(tag_name, "<Button-1>", lambda e, eid=event_id: on_node_click(eid))
