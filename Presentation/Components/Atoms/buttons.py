"""
Atomic Button Components for SismoLab AVL.
Provides consistent, themed action triggers across all views.
"""

from typing import Callable
import customtkinter as ctk

from Presentation.Components.theme import (
    FONT_MAIN,
    BG_SURFACE, BG_HOVER,
    BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_INVERSE,
    ACCENT_CYAN, ACCENT_CYAN_HOVER,
    DANGER, WARNING,
    RADIUS_SM
)


class PrimaryButton(ctk.CTkButton):
    """
    Primary action button with high-contrast cyan accent.
    Ideal for main triggers: 'Crear Evento', 'Calcular Consulta', 'Avanzar Tick'.
    """
    def __init__(
        self,
        master,
        text: str = "Aceptar",
        command: Callable | None = None,
        width: int = 140,
        height: int = 34,
        corner_radius: int = RADIUS_SM,
        **kwargs
    ):
        super().__init__(
            master=master,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=corner_radius,
            fg_color=ACCENT_CYAN,
            hover_color=ACCENT_CYAN_HOVER,
            text_color=TEXT_INVERSE,
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            **kwargs
        )


class SecondaryButton(ctk.CTkButton):
    """
    Secondary action button with dark surface and subtle border.
    Ideal for neutral triggers: 'Cancelar', 'Limpiar', 'Exportar', 'Ver Detalles'.
    """
    def __init__(
        self,
        master,
        text: str = "Cancelar",
        command: Callable | None = None,
        width: int = 120,
        height: int = 34,
        corner_radius: int = RADIUS_SM,
        **kwargs
    ):
        super().__init__(
            master=master,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=corner_radius,
            fg_color=BG_SURFACE,
            hover_color=BG_HOVER,
            border_color=BORDER_SUBTLE,
            border_width=1,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_MAIN, size=12),
            **kwargs
        )


class DangerButton(ctk.CTkButton):
    """
    Destructive action button with red tone.
    Ideal for irreversible triggers: 'Eliminar Evento', 'Limpiar Catálogo', 'Archivar Subárbol'.
    """
    def __init__(
        self,
        master,
        text: str = "Eliminar",
        command: Callable | None = None,
        width: int = 120,
        height: int = 34,
        corner_radius: int = RADIUS_SM,
        **kwargs
    ):
        super().__init__(
            master=master,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=corner_radius,
            fg_color=DANGER,
            hover_color="#dc2626",
            text_color="#ffffff",
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            **kwargs
        )


class WarningButton(ctk.CTkButton):
    """
    Warning action button with orange tone.
    Ideal for attention-demanding triggers: 'Modo Estrés', 'Forzar Rotación', 'Recuperar AVL'.
    """
    def __init__(
        self,
        master,
        text: str = "Alerta",
        command: Callable | None = None,
        width: int = 120,
        height: int = 34,
        corner_radius: int = RADIUS_SM,
        **kwargs
    ):
        super().__init__(
            master=master,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=corner_radius,
            fg_color=WARNING,
            hover_color="#ea580c",
            text_color="#ffffff",
            font=ctk.CTkFont(family=FONT_MAIN, size=12, weight="bold"),
            **kwargs
        )


class GhostButton(ctk.CTkButton):
    """
    Minimalist button with transparent background.
    Ideal for topbar icons, pagination, tabs, and compact toolbars.
    """
    def __init__(
        self,
        master,
        text: str = "",
        command: Callable | None = None,
        width: int = 36,
        height: int = 30,
        corner_radius: int = RADIUS_SM,
        **kwargs
    ):
        super().__init__(
            master=master,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=corner_radius,
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family=FONT_MAIN, size=12),
            **kwargs
        )
