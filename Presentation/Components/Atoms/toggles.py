"""
Atomic Capsule Toggle Switch Component for SismoLab AVL.
Implements a sleek, custom capsule toggle matching the Topbar design.
"""

from typing import Callable
import customtkinter as ctk

from Presentation.Components.theme import (
    ACCENT_CYAN,
    BORDER_SUBTLE
)


class CapsuleToggle(ctk.CTkFrame):
    """
    Compact modern capsule toggle switch.
    Features a perfectly circular thumb (12x12px) inside a sleek capsule track (34x18px).
    Matches the Topbar status indicator styling.
    """
    def __init__(
        self,
        master,
        variable: ctk.BooleanVar | None = None,
        command: Callable | None = None,
        active_color: str = ACCENT_CYAN,
        inactive_color: str = BORDER_SUBTLE,
        width: int = 34,
        height: int = 18,
        **kwargs
    ):
        self.variable = variable if variable is not None else ctk.BooleanVar(value=True)
        self.command = command
        self.active_color = active_color
        self.inactive_color = inactive_color

        initial_color = self.active_color if self.variable.get() else self.inactive_color

        super().__init__(
            master=master,
            width=width,
            height=height,
            corner_radius=height // 2,
            fg_color=initial_color,
            cursor="hand2",
            **kwargs
        )
        self.pack_propagate(False)

        # Sliding white thumb (perfect circular dot)
        dot_size = height - 6
        self.dot = ctk.CTkFrame(
            self,
            width=dot_size,
            height=dot_size,
            corner_radius=dot_size // 2,
            fg_color="#ffffff",
            cursor="hand2"
        )
        initial_relx = 0.72 if self.variable.get() else 0.28
        self.dot.place(relx=initial_relx, rely=0.5, anchor="center")

        # Click event bindings
        self.bind("<Button-1>", self._on_click)
        self.dot.bind("<Button-1>", self._on_click)

        # Hover event bindings (subtle darkening on mouseover)
        self.bind("<Enter>", lambda e: self.dot.configure(fg_color="#cbd5e1"))
        self.bind("<Leave>", lambda e: self.dot.configure(fg_color="#ffffff"))
        self.dot.bind("<Enter>", lambda e: self.dot.configure(fg_color="#cbd5e1"))
        self.dot.bind("<Leave>", lambda e: self.dot.configure(fg_color="#ffffff"))

    def _on_click(self, event=None):
        """Toggle current state and execute callback."""
        new_val = not self.variable.get()
        self.variable.set(new_val)
        self._update_appearance(new_val)
        if self.command:
            self.command()

    def _update_appearance(self, is_active: bool):
        """Update track color and dot position."""
        self.configure(fg_color=self.active_color if is_active else self.inactive_color)
        relx = 0.72 if is_active else 0.28
        self.dot.place(relx=relx, rely=0.5, anchor="center")

    def set(self, is_active: bool):
        """Programmatically set toggle state."""
        self.variable.set(is_active)
        self._update_appearance(is_active)

    def get(self) -> bool:
        """Returns boolean state."""
        return self.variable.get()
