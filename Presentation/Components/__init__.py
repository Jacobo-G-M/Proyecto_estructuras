"""
Atomic Components Package for SismoLab AVL.
Exposes standardized Atoms, Molecules, and Design Tokens for all views.
"""

from Presentation.Components.theme import (
    FONT_MAIN, FONT_MONO,
    BG_ROOT, BG_SURFACE, BG_CARD, BG_CARD_ALT, BG_SURFACE_ALT, BG_INPUT, BG_MUTED, BG_HOVER, BG_ACTIVE,
    BORDER_SUBTLE, BORDER_STRONG, BORDER_LINE, BORDER_FOCUS,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_INVERSE,
    ACCENT_CYAN, ACCENT_CYAN_HOVER,
    SUCCESS, SUCCESS_BG,
    WARNING, WARNING_BG,
    ACCENT_AMBER, INFORMATION,
    DANGER, DANGER_BG,
    INFO, INFO_BG,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL, RADIUS_FULL
)

from Presentation.Components.Atoms import (
    PrimaryButton,
    SecondaryButton,
    DangerButton,
    WarningButton,
    GhostButton,
    StatusBadge,
    StatusDot,
    StyledEntry,
    StyledLabel,
    Divider,
    BadgeVariant,
    CapsuleToggle
)

from Presentation.Components.Molecules import (
    Card,
    MetricCard,
    LabeledInput,
    SectionHeader,
    InfoBanner,
    KeyValueRow,
    EmptyState
)

__all__ = [
    # Theme tokens
    "FONT_MAIN", "FONT_MONO",
    "BG_ROOT", "BG_SURFACE", "BG_CARD", "BG_CARD_ALT", "BG_SURFACE_ALT", "BG_INPUT", "BG_MUTED", "BG_HOVER", "BG_ACTIVE",
    "BORDER_SUBTLE", "BORDER_STRONG", "BORDER_LINE", "BORDER_FOCUS",
    "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED", "TEXT_INVERSE",
    "ACCENT_CYAN", "ACCENT_CYAN_HOVER",
    "SUCCESS", "SUCCESS_BG", "WARNING", "WARNING_BG",
    "ACCENT_AMBER", "INFORMATION",
    "DANGER", "DANGER_BG", "INFO", "INFO_BG",
    "RADIUS_SM", "RADIUS_MD", "RADIUS_LG", "RADIUS_XL", "RADIUS_FULL",

    # Atoms
    "PrimaryButton",
    "SecondaryButton",
    "DangerButton",
    "WarningButton",
    "GhostButton",
    "StatusBadge",
    "StatusDot",
    "StyledEntry",
    "StyledLabel",
    "Divider",
    "BadgeVariant",
    "CapsuleToggle",

    # Molecules
    "Card",
    "MetricCard",
    "LabeledInput",
    "SectionHeader",
    "InfoBanner",
    "KeyValueRow",
    "EmptyState"
]
