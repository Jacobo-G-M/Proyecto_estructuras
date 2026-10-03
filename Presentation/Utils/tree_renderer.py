import tkinter as tk
from typing import Callable, Any

class TreeRenderer:
    """
    Renderizador dinámico de alta fidelidad para árboles AVL y BST.
    Replica exactamente los estilos visuales de Banani:
    - Nodos con relleno saturado (P3 rojo, P2 naranja, P1 verde).
    - Círculos de nodos con doble línea de texto (K=(P,M,I) y H/BF).
    - Selección activa con recuadro sólido cian.
    - Halos de nodos costosos con recuadro punteado ámbar/naranja.
    - Controles de zoom (+, -, drag) sobre el canvas.
    - Cuadrícula sutil de puntos.
    """

    @staticmethod
    def draw_grid(canvas: tk.Canvas, width: int, height: int, step: int = 24, dot_color: str = "#121d28"):
        """Dibuja la cuadrícula sutil de puntos oscuros."""
        for x in range(0, width, step):
            for y in range(0, height, step):
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
        show_costly_halo: bool = True
    ):
        """
        Dibuja el árbol completo en el canvas de Tkinter.
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

        # 1. Obtener secuencia inorden para espaciado horizontal sin colisiones
        inorder_nodes = []
        def get_inorder(curr):
            if curr is None:
                return
            get_inorder(curr.left_son)
            inorder_nodes.append(curr)
            get_inorder(curr.right_son)

        get_inorder(root_node)
        total_nodes = len(inorder_nodes)

        # 2. Profundidades de cada nodo
        node_depths = {}
        def get_depths(curr, d=0):
            if curr is None:
                return
            node_depths[curr] = d
            get_depths(curr.left_son, d + 1)
            get_depths(curr.right_son, d + 1)

        get_depths(root_node, 0)
        max_d = max(node_depths.values()) if node_depths else 0

        # 3. Cálculo de márgenes y escala
        margin_x = 65
        margin_y = 55
        avail_width = max(width - 2 * margin_x, 180)
        step_x = avail_width / max(total_nodes - 1, 1) if total_nodes > 1 else avail_width / 2

        # Altura vertical entre niveles
        level_height = 85 if max_d <= 4 else max(45, (height - 140) / max(max_d, 1))

        # 4. Asignar coordenadas (x, y)
        coords = {}
        if is_bst_degenerate:
            # En BST degenerado, dibujar una línea descendente tipo lista enlazada hacia la derecha
            start_x = width * 0.35
            for idx, node in enumerate(inorder_nodes):
                coords[node] = (start_x + idx * 32, margin_y + idx * 48)
        else:
            for idx, node in enumerate(inorder_nodes):
                nx = margin_x + idx * step_x if total_nodes > 1 else width / 2
                ny = margin_y + node_depths[node] * level_height
                coords[node] = (nx, ny)

        # 5. Dibujar aristas / líneas
        def draw_edges(curr):
            if curr is None:
                return
            curr_x, curr_y = coords[curr]
            for child in (curr.left_son, curr.right_son):
                if child is not None:
                    ch_x, ch_y = coords[child]
                    line_color = "#3a2028" if is_bst_degenerate else "#1c2e42"
                    dash_pattern = (3, 3) if is_bst_degenerate and child == curr.right_son and curr_x > width * 0.4 else ()
                    canvas.create_line(
                        curr_x, curr_y, ch_x, ch_y,
                        fill=line_color,
                        width=2,
                        dash=dash_pattern
                    )
                    draw_edges(child)

        draw_edges(root_node)

        # 6. Dibujar nodos
        r = 30  # radio del nodo circular
        for node in inorder_nodes:
            nx, ny = coords[node]
            ev = getattr(node, "event", None)
            event_id = getattr(ev, "id", node.id)
            priority = getattr(ev, "priority", 1)
            magnitude = getattr(ev, "magnitude", 0.0)
            height_val = node.height() if hasattr(node, "height") else 0
            bf_val = node.balance_factor() if hasattr(node, "balance_factor") else 0

            # Verificar filtro de resaltado
            is_visible = p_filter.get(priority, True)

            # Estilos según el árbol y prioridad
            if is_bst_degenerate:
                fill_color = "#16202c"
                outline_color = "#24364a"
                text_color = "#e8eef3"
            else:
                if not is_visible:
                    # Modo atenuado / semi-transparente
                    fill_color = "#0e1822"
                    outline_color = "#172635"
                    text_color = "#35485c"
                else:
                    if priority == 3:
                        fill_color = "#ff3b5c"    # Rosa / Rojo vibrante
                    elif priority == 2:
                        fill_color = "#ff7a1a"    # Naranja vibrante
                    else:
                        fill_color = "#2ecc71"    # Verde esmeralda
                    outline_color = "#ffffff"
                    text_color = "#ffffff"

            tag_name = f"node_{event_id}"

            # Halo de acceso costoso (recuadro ámbar punteado con esquinas redondeadas)
            if show_costly_halo and event_id in costly_ids and not is_bst_degenerate and is_visible:
                pad = 12
                canvas.create_rectangle(
                    nx - r - pad, ny - r - pad + 4, nx + r + pad, ny + r + pad - 4,
                    outline="#ffb020",
                    width=2,
                    dash=(5, 4)
                )

            # Recuadro sólido cian de selección activa
            if selected_event_id is not None and event_id == selected_event_id:
                pad = 8
                canvas.create_rectangle(
                    nx - r - pad, ny - r - pad + 2, nx + r + pad, ny + r + pad - 2,
                    outline="#22d3ee",
                    width=2
                )

            # Círculo del nodo
            canvas.create_oval(
                nx - r, ny - r, nx + r, ny + r,
                fill=fill_color,
                outline=outline_color if (selected_event_id == event_id or is_bst_degenerate) else fill_color,
                width=2 if selected_event_id == event_id else 1,
                tags=tag_name
            )

            # Textos dentro del nodo
            if is_bst_degenerate:
                canvas.create_text(
                    nx, ny,
                    text=f"{event_id}",
                    fill=text_color,
                    font=("Segoe UI", 9, "bold"),
                    tags=tag_name
                )
            else:
                # Línea superior: (P, M, ID)
                text_top = f"({priority}, {magnitude:.1f}, {event_id})"
                # Línea inferior: H3 · BF 0
                sign = "+" if bf_val > 0 else ""
                text_bot = f"H{height_val} · BF {sign}{bf_val}"

                canvas.create_text(
                    nx, ny - 6,
                    text=text_top,
                    fill=text_color,
                    font=("Segoe UI", 8, "bold"),
                    tags=tag_name
                )
                canvas.create_text(
                    nx, ny + 8,
                    text=text_bot,
                    fill=text_color,
                    font=("Segoe UI", 7),
                    tags=tag_name
                )

            # Enlace interactivo con click
            if on_node_click is not None:
                canvas.tag_bind(tag_name, "<Button-1>", lambda e, eid=event_id: on_node_click(eid))
