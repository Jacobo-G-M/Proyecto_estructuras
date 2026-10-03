"""
Atomic Input Components for SismoLab AVL.
Provides styled single-line text entries for forms and filters.
"""

import customtkinter as ctk

from Presentation.Components.theme import (
    FONT_MAIN,
    BG_ROOT,
    BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_MUTED,
    RADIUS_SM
)


class StyledEntry(ctk.CTkEntry):
    """
    Standardized dark input field with cyan focus outline.
    """
    def __init__(
        self,
        master,
        placeholder_text: str = "",
        width: int = 220,
        height: int = 34,
        corner_radius: int = RADIUS_SM,
        **kwargs
    ):
        super().__init__(
            master=master,
            placeholder_text=placeholder_text,
            width=width,
            height=height,
            corner_radius=corner_radius,
            fg_color=BG_ROOT,
            border_color=BORDER_SUBTLE,
            border_width=1,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            font=ctk.CTkFont(family=FONT_MAIN, size=12),
            **kwargs
        )
