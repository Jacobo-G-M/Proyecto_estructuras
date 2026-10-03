"""
State and Inspection Molecule Components for SismoLab AVL.
Encapsulates two-column key-value summary rows and empty-state feedback screens.
"""

from typing import Callable
import customtkinter as ctk

from Presentation.Components.theme import (
    FONT_MONO,
    TEXT_PRIMARY,
    ACCENT_CYAN
)
from Presentation.Components.Atoms.buttons import PrimaryButton
from Presentation.Components.Atoms.typography import StyledLabel
from Presentation.Components.Molecules.cards import Card


class KeyValueRow(ctk.CTkFrame):
    """
    Two-column row for entity inspection sheets (Key on left, Value on right).
    Example: 'Magnitud:' -> '7.2 Mw', 'Profundidad:' -> '15.0 km'.
    """
    def __init__(
        self,
        master,
        key: str,
        value: str,
        is_highlighted: bool = False,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.lbl_key = StyledLabel(self, text=key, variant="body")
        self.lbl_key.pack(side="left")

        val_color = ACCENT_CYAN if is_highlighted else TEXT_PRIMARY
        self.lbl_val = ctk.CTkLabel(
            self,
            text=str(value),
            text_color=val_color,
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold")
        )
        self.lbl_val.pack(side="right")

    def set_value(self, new_value: str):
        """Update value string dynamically."""
        self.lbl_val.configure(text=str(new_value))


class EmptyState(Card):
    """
    Placeholder displayed when a list, table, or query has no items.
    Features a centered graphic icon, headline, helpful description, and optional action.
    """
    def __init__(
        self,
        master,
        icon: str = "🔍",
        title: str = "No se encontraron resultados",
        description: str = "Intenta ajustar los filtros o cargar un nuevo escenario sísmico.",
        action_text: str | None = None,
        action_command: Callable | None = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        center_box = ctk.CTkFrame(self, fg_color="transparent")
        center_box.pack(expand=True, pady=30, padx=20)

        ctk.CTkLabel(center_box, text=icon, font=ctk.CTkFont(size=36)).pack(pady=(0, 8))
        StyledLabel(center_box, text=title, variant="h2").pack(pady=(0, 4))
        StyledLabel(center_box, text=description, variant="body").pack(pady=(0, 14))

        if action_text and action_command:
            PrimaryButton(center_box, text=action_text, command=action_command).pack()
