"""
Header Molecule Components for SismoLab AVL.
Provides standardized view banners with breadcrumbs, titles, and actions.
"""

import customtkinter as ctk

from Presentation.Components.Atoms.typography import StyledLabel


class SectionHeader(ctk.CTkFrame):
    """
    Standardized header for views and major panels.
    Contains category tag, main title, description, and an actions slot.
    """
    def __init__(
        self,
        master,
        category: str,
        title: str,
        description: str = "",
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Left column (Texts)
        text_col = ctk.CTkFrame(self, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)

        self.lbl_category = StyledLabel(text_col, text=category.upper(), variant="tag")
        self.lbl_category.pack(anchor="w")

        self.lbl_title = StyledLabel(text_col, text=title, variant="h1")
        self.lbl_title.pack(anchor="w", pady=(2, 0))

        if description:
            self.lbl_desc = StyledLabel(text_col, text=description, variant="body")
            self.lbl_desc.pack(anchor="w", pady=(2, 0))

        # Right column for buttons / actions
        self.actions_box = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_box.pack(side="right", padx=(10, 0))

    def add_action(self, button: ctk.CTkButton):
        """Adds a button or widget into the header's right action slot."""
        button.pack(in_=self.actions_box, side="left", padx=4)
