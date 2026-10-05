"""
Atomic Typography and Divider Components for SismoLab AVL.
Encapsulates typography hierarchy scales and layout separators.
"""

from typing import Literal
import customtkinter as ctk

from Presentation.Components.theme import (
    FONT_MAIN, FONT_MONO,
    BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_CYAN
)


class StyledLabel(ctk.CTkLabel):
    """
    Typography label with standardized type scale presets.
    Variants:
    - 'h1': Section title (22px bold)
    - 'h2': Card title (16px bold)
    - 'h3': Subsection title (13px bold)
    - 'body': Default readable text (12px)
    - 'caption': Muted descriptions (11px)
    - 'mono': Code, IDs, coordinates, metrics (12px mono bold)
    - 'tag': Category badges in cyan (10px uppercase bold)
    """
    PRESETS = {
        "h1": {"size": 22, "weight": "bold", "color": TEXT_PRIMARY, "family": FONT_MAIN},
        "h2": {"size": 16, "weight": "bold", "color": TEXT_PRIMARY, "family": FONT_MAIN},
        "h3": {"size": 13, "weight": "bold", "color": TEXT_PRIMARY, "family": FONT_MAIN},
        "body": {"size": 12, "weight": "normal", "color": TEXT_SECONDARY, "family": FONT_MAIN},
        "caption": {"size": 11, "weight": "normal", "color": TEXT_MUTED, "family": FONT_MAIN},
        "mono": {"size": 12, "weight": "bold", "color": TEXT_PRIMARY, "family": FONT_MONO},
        "tag": {"size": 10, "weight": "bold", "color": ACCENT_CYAN, "family": FONT_MAIN},
    }

    def __init__(
        self,
        master,
        text: str,
        variant: Literal["h1", "h2", "h3", "body", "caption", "mono", "tag"] = "body",
        **kwargs
    ):
        preset = self.PRESETS.get(variant, self.PRESETS["body"])
        super().__init__(
            master=master,
            text=text,
            text_color=kwargs.pop("text_color", preset["color"]),
            font=ctk.CTkFont(
                family=preset["family"],
                size=preset["size"],
                weight=preset["weight"]
            ),
            **kwargs
        )


class Divider(ctk.CTkFrame):
    """Subtle line divider for separating layout sections."""
    def __init__(self, master, orientation: Literal["horizontal", "vertical"] = "horizontal", **kwargs):
        if orientation == "horizontal":
            super().__init__(master=master, height=1, fg_color=BORDER_SUBTLE, **kwargs)
        else:
            super().__init__(master=master, width=1, fg_color=BORDER_SUBTLE, **kwargs)
