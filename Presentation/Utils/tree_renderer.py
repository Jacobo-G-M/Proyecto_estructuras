import tkinter as tk
from typing import Callable, Any

class TreeRenderer:
    """
    Renderizador dinámico de árboles binarios (AVL y BST) en Canvas de Tkinter/CustomTkinter.
    Calcula posiciones colisión-cero basadas en orden simétrico (inorden) y profundidad,
    centrando el árbol automáticamente según el ancho del Canvas.
    """

    @staticmethod
    def draw_grid(canvas: tk.Canvas, width: int, height: int, step: int = 25, dot_color: str = "#1e2d3d"):
        """Dibuja una cuadrícula de puntos en el canvas."""
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
        is_bst_degenerate: bool = False
    ):
        """
        Dibuja el árbol completo en el canvas.
        root_node: Instancia de Models.node.Node
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

        # 1. Obtener la secuencia inorden para determinar la coordenada X sin colisiones
        inorder_nodes = []
        def get_inorder(curr):
            if curr is None:
                return
            get_inorder(curr.left_son)
            inorder_nodes.append(curr)
            get_inorder(curr.right_son)

        get_inorder(root_node)
        total_nodes = len(inorder_nodes)

        # 2. Asignar profundidades
        node_depths = {}
        def get_depths(curr, d=0):
            if curr is None:
                return
            node_depths[curr] = d
            get_depths(curr.left_son, d + 1)
            get_depths(curr.right_son, d + 1)

        get_depths(root_node, 0)
        max_d = max(node_depths.values()) if node_depths else 0

        # 3. Calcular espaciados
        margin_x = 50
        margin_y = 50
        avail_width = max(width - 2 * margin_x, 200)
        step_x = avail_width / max(total_nodes - 1, 1) if total_nodes > 1 else avail_width / 2

        # Altura vertical entre niveles
        level_height = 80 if max_d <= 4 else max(40, (height - 120) / max(max_d, 1))

        # 4. Calcular coordenadas (x, y) de cada nodo
        coords = {}
        for idx, node in enumerate(inorder_nodes):
            nx = margin_x + idx * step_x if total_nodes > 1 else width / 2
            ny = margin_y + node_depths[node] * level_height
            coords[node] = (nx, ny)

        # 5. Dibujar aristas (líneas)
        def draw_edges(curr):
            if curr is None:
                return
            curr_x, curr_y = coords[curr]
            for child in (curr.left_son, curr.right_son):
                if child is not None:
                    ch_x, ch_y = coords[child]
                    line_color = "#ff3b5c" if is_bst_degenerate else "#24384e"
                    dash_pattern = (2, 2) if is_bst_degenerate else ()
                    canvas.create_line(
                        curr_x, curr_y, ch_x, ch_y,
                        fill=line_color,
                        width=2,
                        dash=dash_pattern
                    )
                    draw_edges(child)

        draw_edges(root_node)

        # 6. Dibujar cada nodo (círculos y textos)
        r = 28  # radio del nodo
        for node in inorder_nodes:
            nx, ny = coords[node]
            ev = getattr(node, "event", None)
            event_id = getattr(ev, "id", node.id)
            priority = getattr(ev, "priority", 1)
            magnitude = getattr(ev, "magnitude", 0.0)
            height_val = node.height() if hasattr(node, "height") else 0
            bf_val = node.balance_factor() if hasattr(node, "balance_factor") else 0

            # Color del nodo según prioridad (PDF: P3=Rojo, P2=Naranja, P1=Verde)
            if is_bst_degenerate:
                fill_color = "#111c28"
                outline_color = "#8a9bb0"
            else:
                if priority == 3:
                    fill_color = "#ff3b5c"
                elif priority == 2:
                    fill_color = "#ff7a1a"
                else:
                    fill_color = "#2ecc71"
                outline_color = "#e8eef3"

            # Tag para interactividad al hacer click
            tag_name = f"node_{event_id}"

            # Halo de acceso costoso (P3 con depth > L)
            if event_id in costly_ids and not is_bst_degenerate:
                canvas.create_rectangle(
                    nx - r - 8, ny - r - 6, nx + r + 8, ny + r + 6,
                    outline="#ff7a1a",
                    width=2,
                    dash=(4, 4)
                )

            # Halo de nodo seleccionado
            if selected_event_id is not None and event_id == selected_event_id:
                canvas.create_rectangle(
                    nx - r - 12, ny - r - 10, nx + r + 12, ny + r + 10,
                    outline="#22d3ee",
                    width=2,
                    dash=(4, 4)
                )

            # Círculo del nodo
            circle_id = canvas.create_oval(
                nx - r, ny - r, nx + r, ny + r,
                fill=fill_color,
                outline=outline_color,
                width=2 if selected_event_id == event_id else 1,
                tags=tag_name
            )

            # Texto del nodo
            if is_bst_degenerate:
                canvas.create_text(
                    nx, ny,
                    text=f"{event_id}",
                    fill="#e8eef3",
                    font=("Segoe UI", 9, "bold"),
                    tags=tag_name
                )
            else:
                # Tupla (P, M, ID) arriba
                text_top = f"({priority}, {magnitude:.1f}, {event_id})"
                # H:x · BF:x abajo
                sign = "+" if bf_val > 0 else ""
                text_bot = f"H:{height_val} · BF:{sign}{bf_val}"

                canvas.create_text(
                    nx, ny - 6,
                    text=text_top,
                    fill="#e8eef3",
                    font=("Segoe UI", 8, "bold"),
                    tags=tag_name
                )
                canvas.create_text(
                    nx, ny + 8,
                    text=text_bot,
                    fill="#e8eef3",
                    font=("Segoe UI", 7),
                    tags=tag_name
                )

            # Enlazar evento de clic
            if on_node_click is not None:
                canvas.tag_bind(tag_name, "<Button-1>", lambda e, eid=event_id: on_node_click(eid))
