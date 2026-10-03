"""
Atomic Status Badge and Dot Components for SismoLab AVL.
Provides standardized entity health and category indicators.
"""

from typing import Literal
import customtkinter as ctk

from Presentation.Components.theme import (
    FONT_MAIN,
    BG_SURFACE,
    BORDER_SUBTLE,
    TEXT_SECONDARY, TEXT_MUTED,
    SUCCESS, SUCCESS_BG,
    WARNING, WARNING_BG,
    DANGER, DANGER_BG,
    INFO, INFO_BG,
    RADIUS_FULL
)

BadgeVariant = Literal["success", "warning", "danger", "info", "neutral"]


class StatusDot(ctk.CTkFrame):
    """
    Small colored dot representing live entity status (Active, Online, Critical).
    """
    COLOR_MAP = {
        "success": SUCCESS,
        "warning": WARNING,
        "danger": DANGER,
        "info": INFO,
        "neutral": TEXT_MUTED
    }

    def __init__(
        self,
        master,
        variant: BadgeVariant = "success",
        size: int = 8,
        **kwargs
    ):
        dot_color = kwargs.pop("fg_color", self.COLOR_MAP.get(variant, SUCCESS))
        dot_width = kwargs.pop("width", size)
        dot_height = kwargs.pop("height", size)
        dot_radius = kwargs.pop("corner_radius", size // 2)

        super().__init__(
            master=master,
            width=dot_width,
            height=dot_height,
            corner_radius=dot_radius,
            fg_color=dot_color,
            **kwargs
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

    def set_variant(self, variant: BadgeVariant):
        """Dynamically update indicator color."""
        self.configure(fg_color=self.COLOR_MAP.get(variant, SUCCESS))


class StatusBadge(ctk.CTkFrame):
    """
    Capsule pill badge with semantic background and text.
    Used for statuses: 'Activo', 'Archivado', 'Eliminado', 'AVL Balanceado', 'Prioridad P1'.
    """
    THEMES = {
        "success": {"bg": SUCCESS_BG, "border": SUCCESS, "text": SUCCESS},
        "warning": {"bg": WARNING_BG, "border": WARNING, "text": WARNING},
        "danger": {"bg": DANGER_BG, "border": DANGER, "text": DANGER},
        "info": {"bg": INFO_BG, "border": INFO, "text": INFO},
        "neutral": {"bg": BG_SURFACE, "border": BORDER_SUBTLE, "text": TEXT_SECONDARY},
    }

    def __init__(
        self,
        master,
        text: str,
        variant: BadgeVariant = "neutral",
        show_dot: bool = False,
        **kwargs
    ):
        theme = self.THEMES.get(variant, self.THEMES["neutral"])
        super().__init__(
            master=master,
            fg_color=theme["bg"],
            border_color=theme["border"],
            border_width=1,
            corner_radius=RADIUS_FULL,
            **kwargs
        )

        if show_dot:
            self.dot = StatusDot(self, variant=variant, size=6)
            self.dot.pack(side="left", padx=(8, 4), pady=4)

        self.label = ctk.CTkLabel(
            self,
            text=text,
            text_color=theme["text"],
            font=ctk.CTkFont(family=FONT_MAIN, size=10, weight="bold")
        )
        pad_left = 4 if show_dot else 10
        self.label.pack(side="left", padx=(pad_left, 10), pady=2)

    def update_badge(self, text: str, variant: BadgeVariant):
        """Update text and visual palette dynamically."""
        theme = self.THEMES.get(variant, self.THEMES["neutral"])
        self.configure(fg_color=theme["bg"], border_color=theme["border"])
        self.label.configure(text=text, text_color=theme["text"])
        if hasattr(self, "dot"):
            self.dot.set_variant(variant)
