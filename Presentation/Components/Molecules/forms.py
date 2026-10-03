"""
Form Molecule Components for SismoLab AVL.
Provides composite input elements with labels, placeholders, and helpers.
"""

import customtkinter as ctk

from Presentation.Components.Atoms.inputs import StyledEntry
from Presentation.Components.Atoms.typography import StyledLabel


class LabeledInput(ctk.CTkFrame):
    """
    Form molecule pairing an input field with an informative title label,
    placeholder text, and optional helper hint.
    """
    def __init__(
        self,
        master,
        label: str,
        placeholder_text: str = "",
        initial_value: str = "",
        helper_text: str = "",
        input_width: int = 220,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Top label
        self.lbl_title = StyledLabel(self, text=label, variant="h3")
        self.lbl_title.pack(anchor="w", pady=(0, 4))

        # Input field atom
        self.entry = StyledEntry(self, placeholder_text=placeholder_text, width=input_width)
        if initial_value:
            self.entry.insert(0, str(initial_value))
        self.entry.pack(anchor="w", fill="x")

        # Optional helper caption below input
        if helper_text:
            self.lbl_helper = StyledLabel(self, text=helper_text, variant="caption")
            self.lbl_helper.pack(anchor="w", pady=(2, 0))
        else:
            self.lbl_helper = None

    def get_value(self) -> str:
        """Returns the current string entered by the user."""
        return self.entry.get().strip()

    def set_value(self, text: str):
        """Programmatically updates input content."""
        self.entry.delete(0, "end")
        self.entry.insert(0, str(text))

    def clear(self):
        """Clears the entry text."""
        self.entry.delete(0, "end")
