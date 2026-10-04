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

        self.enabled = True

        # Click event bindings
        self.bind("<Button-1>", self._on_click)
        self.dot.bind("<Button-1>", self._on_click)

        # Hover event bindings (subtle darkening on mouseover)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.dot.bind("<Enter>", self._on_enter)
        self.dot.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        if self.enabled:
            self.dot.configure(fg_color="#cbd5e1")

    def _on_leave(self, event=None):
        if self.enabled:
            self.dot.configure(fg_color="#ffffff")

    def _on_click(self, event=None):
        """Toggle current state and execute callback if enabled."""
        if not self.enabled:
            return
        new_val = not self.variable.get()
        self.variable.set(new_val)
        self._update_appearance(new_val)
        if self.command:
            self.command()

    def _update_appearance(self, is_active: bool):
        """Update track color and dot position."""
        if not self.enabled:
            self.configure(fg_color=BORDER_SUBTLE)
            self.dot.configure(fg_color="#475569")
        else:
            self.configure(fg_color=self.active_color if is_active else self.inactive_color)
            self.dot.configure(fg_color="#ffffff")
        relx = 0.72 if is_active else 0.28
        self.dot.place(relx=relx, rely=0.5, anchor="center")

    def set_enabled(self, enabled: bool):
        """Enable or disable the toggle switch interactivity and appearance."""
        self.enabled = enabled
        cursor = "hand2" if enabled else "arrow"
        self.configure(cursor=cursor)
        self.dot.configure(cursor=cursor)
        self._update_appearance(self.variable.get())

    def set(self, is_active: bool):
        """Programmatically set toggle state."""
        self.variable.set(is_active)
        self._update_appearance(is_active)

    def get(self) -> bool:
        """Returns boolean state."""
        return self.variable.get()

