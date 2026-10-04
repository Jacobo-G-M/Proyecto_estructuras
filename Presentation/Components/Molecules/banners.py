"""
Banner Molecule Components for SismoLab AVL.
Provides alert and status notification boxes with semantic color strips.
"""

from typing import Literal
import customtkinter as ctk

from Presentation.Components.theme import (
    BG_SURFACE,
    BORDER_SUBTLE,
    TEXT_PRIMARY,
    SUCCESS, WARNING, DANGER, INFO,
    RADIUS_MD
)
from Presentation.Components.Atoms.typography import StyledLabel


class InfoBanner(ctk.CTkFrame):
    """
    Colored alert or notification banner.
    Variants: 'info', 'success', 'warning', 'danger'.
    """
    THEMES = {
        "info": {"bar": INFO, "bg": BG_SURFACE, "text": TEXT_PRIMARY, "icon": "ℹ️"},
        "success": {"bar": SUCCESS, "bg": BG_SURFACE, "text": TEXT_PRIMARY, "icon": "✅"},
        "warning": {"bar": WARNING, "bg": BG_SURFACE, "text": TEXT_PRIMARY, "icon": "⚠️"},
        "danger": {"bar": DANGER, "bg": BG_SURFACE, "text": TEXT_PRIMARY, "icon": "🚨"},
    }

    def __init__(
        self,
        master,
        title: str,
        message: str,
        variant: Literal["info", "success", "warning", "danger"] = "info",
        **kwargs
    ):
        theme = self.THEMES.get(variant, self.THEMES["info"])
        super().__init__(
            master=master,
            fg_color=theme["bg"],
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=RADIUS_MD,
            height=0,
            **kwargs
        )

        # Colored indicator strip on the left
        self.strip = ctk.CTkFrame(self, width=4, height=0, corner_radius=2, fg_color=theme["bar"])
        self.strip.pack(side="left", fill="y", padx=(0, 10))

        # Content container
        content = ctk.CTkFrame(self, fg_color="transparent", height=0)
        content.pack(side="left", fill="both", expand=True, pady=6, padx=(0, 10))

        header = ctk.CTkFrame(content, fg_color="transparent", height=0)
        header.pack(fill="x")

        ctk.CTkLabel(header, text=theme["icon"], font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))
        StyledLabel(header, text=title, variant="h3").pack(side="left")

        StyledLabel(content, text=message, variant="caption").pack(anchor="w", pady=(1, 0))
