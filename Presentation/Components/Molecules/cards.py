"""
Card Molecule Components for SismoLab AVL.
Encapsulates surface containers and dashboard KPI metric cards.
"""

import customtkinter as ctk

from Presentation.Components.theme import (
    FONT_MONO,
    BG_SURFACE,
    BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_MUTED,
    ACCENT_CYAN,
    RADIUS_LG
)
from Presentation.Components.Atoms.typography import StyledLabel
from Presentation.Components.Atoms.badges import StatusBadge, BadgeVariant


class Card(ctk.CTkFrame):
    """
    Standard surface container for grouping related content and actions.
    Features subtle border, dark background, and rounded corners.
    """
    def __init__(
        self,
        master,
        corner_radius: int = RADIUS_LG,
        border_width: int = 1,
        fg_color: str = BG_SURFACE,
        border_color: str = BORDER_SUBTLE,
        **kwargs
    ):
        kwargs.setdefault("height", 0)
        super().__init__(
            master=master,
            corner_radius=corner_radius,
            border_width=border_width,
            fg_color=fg_color,
            border_color=border_color,
            **kwargs
        )


class MetricCard(Card):
    """
    Dashboard metric card displaying a KPI value, title, subtitle, and status.
    Ideal for: 'Sismos Activos', 'Profundidad Media', 'Balance AVL', 'Cola de Reportes'.
    """
    def __init__(
        self,
        master,
        title: str,
        value: str | int | float = "--",
        subtitle: str = "",
        icon: str = "📊",
        accent_color: str = ACCENT_CYAN,
        badge_text: str | None = None,
        badge_variant: BadgeVariant = "info",
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.accent_color = accent_color

        # Header row: Icon & Title + Optional Badge
        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(10, 4))
        header_row.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header_row, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        self.lbl_icon = ctk.CTkLabel(title_box, text=icon, font=ctk.CTkFont(size=13))
        self.lbl_icon.pack(side="left", padx=(0, 4))

        self.lbl_title = StyledLabel(title_box, text=title.upper(), variant="tag")
        self.lbl_title.configure(text_color=TEXT_MUTED)
        self.lbl_title.pack(side="left")

        if badge_text:
            self.badge = StatusBadge(header_row, text=badge_text, variant=badge_variant)
            self.badge.grid(row=0, column=1, sticky="e", padx=(4, 0))
        else:
            self.badge = None

        # Value Row: Big display number
        self.lbl_value = ctk.CTkLabel(
            self,
            text=str(value),
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_MONO, size=22, weight="bold")
        )
        self.lbl_value.pack(anchor="w", padx=12, pady=(2, 2))

        # Subtitle / description note
        self.lbl_sub = StyledLabel(self, text=subtitle, variant="caption")
        self.lbl_sub.pack(anchor="w", padx=12, pady=(0, 10))

    def set_value(self, new_value: str | int | float):
        """Dynamically update the main KPI value."""
        self.lbl_value.configure(text=str(new_value))

    def set_subtitle(self, new_subtitle: str):
        """Dynamically update the subtitle description."""
        self.lbl_sub.configure(text=new_subtitle)

    def set_badge(self, text: str, variant: BadgeVariant = "info"):
        """Update or toggle the badge state."""
        if self.badge:
            self.badge.update_badge(text, variant)
