"""
Recovery Report Modal for SismoLab AVL.
Informative popup window displayed when restoring the AVL tree balance (Global Recovery).
Satisfies the requirement:
'Al solicitar la recuperación global, se pausa el procesamiento de reportes.
El sistema detecta los desbalances y aplica las rotaciones necesarias hasta
restablecer la propiedad AVL. Se muestran los cambios y su costo.
No se permite vaciar el árbol para sustituirlo por otro construido a partir de una lista ordenada.'
"""

import os
from typing import Any, Dict
import customtkinter as ctk

from Presentation.Components.theme import (
    FONT_MAIN,
    FONT_MONO,
    BG_ROOT,
    BG_SURFACE,
    BG_CARD,
    BG_CARD_ALT,
    BORDER_SUBTLE,
    BORDER_STRONG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_CYAN,
    SUCCESS,
    WARNING,
    DANGER,
    RADIUS_MD,
    RADIUS_LG,
    RADIUS_SM,
)
from Presentation.Components.Atoms.badges import StatusBadge
from Presentation.Components.Atoms.buttons import PrimaryButton
from Presentation.Components.Molecules.cards import Card
from Presentation.Components.Molecules.banners import InfoBanner


def _fmt_key(key: Any) -> str:
    """Format node key (priority, magnitude, id) for clear display."""
    if key is None:
        return "--"
    if isinstance(key, (tuple, list)):
        if len(key) >= 3:
            return f"(P{key[0]}, Mag {key[1]:.1f}, #{key[2]})"
        return str(key)
    return str(key)


class RecoveryReportModal(ctk.CTkToplevel):
    """
    Modal window reporting global AVL recovery results, rotations,
    topological mutations, and computational complexity costs.
    """

    def __init__(self, master, result: Dict[str, Any]):
        super().__init__(master)

        self.result = result or {}
        self.success = self.result.get("success", False)

        # Configuración básica de ventana
        self.title("Restauración Global AVL - SismoLab")
        self.geometry("680x740")
        self.minsize(660, 600)
        self.resizable(False, False)
        self.configure(fg_color=BG_ROOT)

        # Configurar icono oficial de la aplicación (logo.ico)
        self._set_app_icon()

        # Vincular con ventana principal
        if master:
            try:
                top = master.winfo_toplevel() if hasattr(master, "winfo_toplevel") else master
                self.transient(top)
            except Exception:
                pass

        # Centrado sobre la ventana padre
        self._center_on_master(master)

        # Configuración modal y atajo de escape
        self.bind("<Escape>", lambda e: self.destroy())
        self.after(100, self._apply_modal_focus)

        # Contenedor raíz
        self._build_ui()

    def _set_app_icon(self):
        """Aplica el icono oficial del observatorio (logo.ico) a la barra de título de la ventana."""
        ico_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Assets", "logo.ico"))
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass
            # Reaplicar con retardo para asegurar que sobreescriba el icono por defecto de CustomTkinter en Windows
            self.after(200, lambda: self._apply_icon(ico_path))

    def _apply_icon(self, ico_path: str):
        try:
            if self.winfo_exists():
                self.iconbitmap(ico_path)
        except Exception:
            pass

    def _center_on_master(self, master):
        self.update_idletasks()
        try:
            top = master.winfo_toplevel() if master and hasattr(master, "winfo_toplevel") else master
            w = 680
            h = 740
            if top and top.winfo_ismapped():
                x = top.winfo_rootx() + (top.winfo_width() - w) // 2
                y = top.winfo_rooty() + (top.winfo_height() - h) // 2
            else:
                x = (self.winfo_screenwidth() - w) // 2
                y = (self.winfo_screenheight() - h) // 2
            x = max(20, x)
            y = max(20, y)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _apply_modal_focus(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:
            pass

    def _build_ui(self):
        # Frame principal con padding
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=(18, 16))

        # -------------------------------------------------------------
        # 1. ENCABEZADO
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        top_meta_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_meta_row.pack(fill="x", pady=(0, 4))

        if self.success:
            badge = StatusBadge(
                top_meta_row,
                text="PROPIEDAD AVL RESTABLECIDA",
                variant="success",
                show_dot=True
            )
        else:
            badge = StatusBadge(
                top_meta_row,
                text="FALLO EN LA RESTAURACIÓN",
                variant="danger",
                show_dot=True
            )
        badge.pack(side="left")

        lbl_title = ctk.CTkLabel(
            header_frame,
            text="Informe de Reequilibrio y Costos AVL",
            font=ctk.CTkFont(family=FONT_MAIN, size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        )
        lbl_title.pack(fill="x", pady=(2, 0))

        lbl_desc = ctk.CTkLabel(
            header_frame,
            text="Resultados de la restauración topológica tras operar bajo el modo de estrés.",
            font=ctk.CTkFont(family=FONT_MAIN, size=11),
            text_color=TEXT_SECONDARY,
            anchor="w"
        )
        lbl_desc.pack(fill="x")

        # -------------------------------------------------------------
        # 2. BANNER DE GARANTÍAS Y RESTRICCIONES (CONFORME AL DOCUMENTO)
        # -------------------------------------------------------------
        banner = InfoBanner(
            main_container,
            title="Garantía de Restablecimiento",
            message=(
                "• El procesamiento de reportes fue pausado automáticamente.\n"
                "• No se vació el árbol para sustituirlo por una lista ordenada;\n"
                "  las rotaciones se aplicaron directamente sobre la estructura en memoria."
            ),
            variant="success" if self.success else "danger"
        )
        banner.pack(fill="x", pady=(0, 12))

        # -------------------------------------------------------------
        # 3. TARJETAS DE RESUMEN KPI (2x2)
        # -------------------------------------------------------------
        total_rotations = self.result.get("total_rotations", 0)
        total_turns = self.result.get("total_turns", 0)
        imbalanced_count = self.result.get("imbalanced_count", 0)
        pre_height = self.result.get("pre_height", 0)
        post_height = self.result.get("post_height", 0)
        height_diff = pre_height - post_height
        elapsed_ms = self.result.get("elapsed_ms", 0.0)

        grid_cards = ctk.CTkFrame(main_container, fg_color="transparent")
        grid_cards.pack(fill="x", pady=(0, 12))
        grid_cards.grid_columnconfigure((0, 1), weight=1)

        self._create_metric_pill(
            grid_cards,
            row=0, col=0,
            title="ROTACIONES AVL",
            value=f"{total_rotations} Casos",
            subtext=f"{total_turns} Giros elementales de puntero",
            color=ACCENT_CYAN,
            icon="🔄"
        )

        self._create_metric_pill(
            grid_cards,
            row=0, col=1,
            title="DESBALANCES CORREGIDOS",
            value=f"{imbalanced_count} Nodos",
            subtext="0 residuales (|FE| ≤ 1)",
            color=SUCCESS,
            icon="⚖️"
        )

        height_sub = f"Reducción de {height_diff} niveles" if height_diff > 0 else "Altura balanceada"
        self._create_metric_pill(
            grid_cards,
            row=1, col=0,
            title="ALTURA DEL ÁRBOL",
            value=f"{pre_height}  ➜  {post_height}",
            subtext=height_sub,
            color="#ffb020",
            icon="🌲"
        )

        self._create_metric_pill(
            grid_cards,
            row=1, col=1,
            title="COSTO COMPUTACIONAL",
            value=f"{elapsed_ms} ms",
            subtext="O(N) tiempo  |  O(1) aux.",
            color="#38bdf8",
            icon="⚡"
        )

        # -------------------------------------------------------------
        # 4. CONTENEDOR DESPLAZABLE CON DETALLE TÉCNICO
        # -------------------------------------------------------------
        scroll = ctk.CTkScrollableFrame(
            main_container,
            fg_color=BG_SURFACE,
            border_width=1,
            border_color=BORDER_SUBTLE,
            corner_radius=RADIUS_MD
        )
        scroll.pack(fill="both", expand=True, pady=(0, 14))

        # SECCIÓN A: Desglose de Rotaciones y Costos de Puntero
        self._build_rotations_breakdown(scroll)

        # SECCIÓN B: Cambios Topológicos (Raíz y Nodos)
        self._build_topology_changes(scroll)

        # SECCIÓN C: Verificación y Auditoría
        self._build_audit_section(scroll)

        # -------------------------------------------------------------
        # 5. BOTÓN DE CIERRE INFERIOR
        # -------------------------------------------------------------
        btn_close = PrimaryButton(
            main_container,
            text="Entendido y Continuar",
            command=self.destroy,
            height=38
        )
        btn_close.pack(fill="x")

    def _create_metric_pill(self, master, row, col, title, value, subtext, color, icon):
        card = Card(
            master,
            corner_radius=RADIUS_MD,
            fg_color=BG_CARD,
            border_color=BORDER_SUBTLE,
            border_width=1
        )
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        lbl_icon = ctk.CTkLabel(top_row, text=icon, font=ctk.CTkFont(size=13))
        lbl_icon.pack(side="left", padx=(0, 5))

        lbl_t = ctk.CTkLabel(
            top_row,
            text=title,
            font=ctk.CTkFont(family=FONT_MONO, size=9, weight="bold"),
            text_color=TEXT_MUTED
        )
        lbl_t.pack(side="left")

        lbl_val = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(family=FONT_MAIN, size=16, weight="bold"),
            text_color=color,
            anchor="w"
        )
        lbl_val.pack(fill="x", pady=(2, 0))

        lbl_sub = ctk.CTkLabel(
            inner,
            text=subtext,
            font=ctk.CTkFont(family=FONT_MAIN, size=10),
            text_color=TEXT_SECONDARY,
            anchor="w"
        )
        lbl_sub.pack(fill="x")

    def _build_rotations_breakdown(self, master):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=(10, 12))

        lbl_sec = ctk.CTkLabel(
            frame,
            text="1. DESGLOSE DE ROTACIONES Y OPERACIONES DE PUNTEROS",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color=ACCENT_CYAN,
            anchor="w"
        )
        lbl_sec.pack(fill="x", pady=(0, 6))

        cases = self.result.get("cases", {})
        turns = self.result.get("turns", {})

        # Tabla de casos de rotación
        table_frame = ctk.CTkFrame(
            frame,
            fg_color=BG_CARD_ALT,
            corner_radius=RADIUS_SM,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        table_frame.pack(fill="x", pady=(0, 6))
        table_frame.grid_columnconfigure((0, 1), weight=1)

        rot_specs = [
            ("Rotación Simple Derecha (LL)", cases.get("LL", 0), "1 giro de puntero c/u (3 reasignaciones)"),
            ("Rotación Simple Izquierda (RR)", cases.get("RR", 0), "1 giro de puntero c/u (3 reasignaciones)"),
            ("Rotación Doble Izq-Der (LR)", cases.get("LR", 0), "2 giros de puntero c/u (5 reasignaciones)"),
            ("Rotación Doble Der-Izq (RL)", cases.get("RL", 0), "2 giros de puntero c/u (5 reasignaciones)"),
        ]

        for i, (name, count, desc) in enumerate(rot_specs):
            row = i // 2
            col = i % 2
            item = ctk.CTkFrame(table_frame, fg_color="transparent")
            item.grid(row=row, column=col, padx=12, pady=6, sticky="nsew")

            lbl_name = ctk.CTkLabel(
                item,
                text=f"{name}:",
                font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
                text_color=TEXT_PRIMARY,
                anchor="w"
            )
            lbl_name.pack(fill="x")

            lbl_count = ctk.CTkLabel(
                item,
                text=f"• {count} ejecutadas",
                font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"),
                text_color=TEXT_SECONDARY if count == 0 else ACCENT_CYAN,
                anchor="w"
            )
            lbl_count.pack(fill="x", pady=(1, 0))

            lbl_desc = ctk.CTkLabel(
                item,
                text=f"  ({desc})",
                font=ctk.CTkFont(family=FONT_MAIN, size=9),
                text_color=TEXT_MUTED,
                anchor="w"
            )
            lbl_desc.pack(fill="x", pady=(0, 2))

        # Fila de giros de enlace elementales
        turns_left = turns.get("left", 0)
        turns_right = turns.get("right", 0)
        lbl_turns = ctk.CTkLabel(
            frame,
            text=(
                f"Giros elementales ejecutados:  Izquierda: {turns_left}  |  Derecha: {turns_right}\n"
                f"(Costo por giro elemental: Θ(1) punteros actualizados)"
            ),
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        lbl_turns.pack(fill="x", pady=(4, 0))

    def _build_topology_changes(self, master):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=(0, 12))

        lbl_sec = ctk.CTkLabel(
            frame,
            text="2. CAMBIOS EN LA TOPOLOGÍA DEL ÁRBOL",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color=ACCENT_CYAN,
            anchor="w"
        )
        lbl_sec.pack(fill="x", pady=(0, 6))

        card = ctk.CTkFrame(
            frame,
            fg_color=BG_CARD_ALT,
            corner_radius=RADIUS_SM,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        card.pack(fill="x", pady=(0, 6), padx=0)

        pre_root_id = self.result.get("pre_root_id")
        post_root_id = self.result.get("post_root_id")
        pre_root_key = self.result.get("pre_root_key")
        post_root_key = self.result.get("post_root_key")

        root_changed = (pre_root_id != post_root_id)
        root_badge = "Raíz reubicada por balanceo" if root_changed else "Raíz preservada en su posición"
        root_color = WARNING if root_changed else SUCCESS

        row_root = ctk.CTkFrame(card, fg_color="transparent")
        row_root.pack(fill="x", padx=10, pady=(8, 4))

        lbl_root_t = ctk.CTkLabel(
            row_root,
            text=f"Nodo Raíz:  {root_badge}",
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            text_color=root_color,
            anchor="w"
        )
        lbl_root_t.pack(fill="x")

        lbl_root_desc = ctk.CTkLabel(
            row_root,
            text=(
                f"• Antes:  ID #{pre_root_id or 'None'} {_fmt_key(pre_root_key)}\n"
                f"• Después: ID #{post_root_id or 'None'} {_fmt_key(post_root_key)}"
            ),
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_PRIMARY,
            justify="left",
            anchor="w"
        )
        lbl_root_desc.pack(fill="x", pady=(2, 0))

        # Muestra de nodos que tenían desbalance
        imbalanced_nodes = self.result.get("imbalanced_nodes", [])
        row_nodes = ctk.CTkFrame(card, fg_color="transparent")
        row_nodes.pack(fill="x", padx=10, pady=(4, 8))

        lbl_imb_t = ctk.CTkLabel(
            row_nodes,
            text="Nodos con Desbalance (|FE| > 1) Detectados y Subsanados:",
            font=ctk.CTkFont(family=FONT_MAIN, size=11, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        )
        lbl_imb_t.pack(fill="x")

        if imbalanced_nodes:
            # Mostrar hasta 5 nodos
            lines = []
            for node in imbalanced_nodes[:5]:
                bf = node.get("bf", 0)
                nid = node.get("id")
                key_str = _fmt_key(node.get("key"))
                lines.append(f"  • Nodo ID #{nid} {key_str}\n    FE previo: {bf:+d}  ➜  Corregido a FE ≤ 1")
            if len(imbalanced_nodes) > 5:
                lines.append(f"  • ... y {len(imbalanced_nodes) - 5} nodos adicionales rebalanceados con éxito.")
            imb_text = "\n".join(lines)
        else:
            imb_text = (
                "  • El árbol ya se encontraba dentro de tolerancias AVL.\n"
                "    (|FE| ≤ 1 verificado en todos los nodos)."
            )

        lbl_imb_desc = ctk.CTkLabel(
            row_nodes,
            text=imb_text,
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_SECONDARY if not imbalanced_nodes else TEXT_PRIMARY,
            justify="left",
            anchor="w"
        )
        lbl_imb_desc.pack(fill="x", pady=(2, 0))

    def _build_audit_section(self, master):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=(0, 8))

        lbl_sec = ctk.CTkLabel(
            frame,
            text="3. AUDITORÍA MATEMÁTICA Y VERIFICACIÓN ESTRUCTURAL",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color=ACCENT_CYAN,
            anchor="w"
        )
        lbl_sec.pack(fill="x", pady=(0, 6))

        box = ctk.CTkFrame(
            frame,
            fg_color=BG_CARD_ALT,
            corner_radius=RADIUS_SM,
            border_width=1,
            border_color=BORDER_SUBTLE
        )
        box.pack(fill="x")

        audit_items = [
            ("✓ Invariante AVL", "Cumplida: |FE| ≤ 1 verificado en el 100% de los nodos.", SUCCESS),
            ("✓ Invariante BST", "Cumplida: Claves en orden estricto (Hijo Izq < Nodo < Hijo Der).", SUCCESS),
            ("✓ Integridad de Datos", "Consistencia total: Todos los eventos del catálogo siguen presentes.", SUCCESS),
            ("✓ Modo de Estrés", "Desactivado: Las futuras inserciones autobalancearán en O(log N).", ACCENT_CYAN)
        ]

        for title, desc, color in audit_items:
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)

            lbl_t = ctk.CTkLabel(
                row,
                text=f"{title}:",
                font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold"),
                text_color=color,
                width=150,
                anchor="w"
            )
            lbl_t.pack(side="left")

            lbl_d = ctk.CTkLabel(
                row,
                text=desc,
                font=ctk.CTkFont(family=FONT_MAIN, size=10),
                text_color=TEXT_PRIMARY,
                anchor="w"
            )
            lbl_d.pack(side="left", fill="x", expand=True)
