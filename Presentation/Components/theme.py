"""
Design Tokens and Theme Constants for SismoLab AVL.
Centralizes the color palette, typography scales, spacing, and border radii
used across all Presentation components and views.
"""

# Color Palette: Backgrounds & Surfaces
BG_ROOT = "#070c12"       # Main application window background
BG_SURFACE = "#0b131c"    # Card, panel, and modal container surface
BG_SURFACE_ALT = "#101b26"# Elevated or nested surface
BG_HOVER = "#142130"      # Standard hover state for dark components
BG_ACTIVE = "#1a2a3e"     # Pressed or active state

# Color Palette: Borders
BORDER_SUBTLE = "#1a2736" # Default card and input boundary
BORDER_STRONG = "#25384d" # Highlighted border
BORDER_FOCUS = "#22d3ee"  # Input focus and active selection

# Color Palette: Typography
TEXT_PRIMARY = "#e8eef3"  # Main headings, primary labels, and inputs
TEXT_SECONDARY = "#8a9bb0"# Subtitles, secondary captions, and placeholders
TEXT_MUTED = "#506375"    # Disabled text, footer notes, and subtle indicators
TEXT_INVERSE = "#06202a"  # Text on bright accent buttons

# Color Palette: Accents & Semantics
ACCENT_CYAN = "#22d3ee"   # Primary brand accent
ACCENT_CYAN_HOVER = "#06b6d4"
SUCCESS = "#2ecc71"       # Active state, balanced AVL, successful validations
SUCCESS_BG = "#0c281a"
WARNING = "#ff7a1a"       # Stress mode, alerts, high depth/magnitude warning
WARNING_BG = "#2a1608"
DANGER = "#ef4444"        # Deleted events, severe imbalances, critical errors
DANGER_BG = "#2b1010"
INFO = "#3b82f6"          # Informational status, pending queues
INFO_BG = "#0d1e38"

# Typography Families
FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

# Radii
RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12
RADIUS_FULL = 999
