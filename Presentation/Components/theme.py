"""
Design Tokens and Theme Constants for SismoLab AVL.
Centralizes the color palette, typography scales, spacing, and border radii
used across all Presentation components and views.
"""

# Color Palette: Backgrounds & Surfaces
BG_ROOT = "#070c12"       # Main application window background (--color-background)
BG_SURFACE = "#0b131c"    # Outer panel and container surface (--color-surface)
BG_CARD = "#0e1620"       # Card container surface (--color-card)
BG_CARD_ALT = "#13202e"   # Elevated or nested card surface (--color-card2)
BG_SURFACE_ALT = "#101b26"# Legacy alias for elevated surfaces
BG_INPUT = "#101922"      # Input fields and textboxes (--color-input)
BG_MUTED = "#111c28"      # Inactive tags and muted pills (--color-muted)
BG_HOVER = "#142130"      # Standard hover state for dark components
BG_ACTIVE = "#1a2a3e"     # Pressed or active state

# Color Palette: Borders
BORDER_SUBTLE = "#1e2d3d" # Default card and input boundary (--color-border)
BORDER_STRONG = "#25384d" # Highlighted border
BORDER_LINE = "#24384e"   # Grid reticle lines and fine dividers (--color-line)
BORDER_FOCUS = "#22d3ee"  # Input focus and active selection

# Color Palette: Typography
TEXT_PRIMARY = "#e8eef3"  # Main headings, primary labels, and inputs (--color-foreground)
TEXT_SECONDARY = "#8a9bb0"# Subtitles, secondary captions, and placeholders (--color-muted-foreground)
TEXT_MUTED = "#506375"    # Disabled text, footer notes, and subtle indicators
TEXT_INVERSE = "#06202a"  # Text on bright accent buttons (--color-primary-foreground)

# Color Palette: Accents & Semantics
ACCENT_CYAN = "#22d3ee"   # Primary brand accent (--color-primary)
ACCENT_CYAN_HOVER = "#06b6d4"
SUCCESS = "#2ecc71"       # Active state, balanced AVL (--color-success)
SUCCESS_BG = "#0c281a"
WARNING = "#ff7a1a"       # Stress mode, alerts (--color-secondary)
WARNING_BG = "#2a1608"
ACCENT_AMBER = "#ffb020"  # Replica vectors, candidate events (--color-accent)
INFORMATION = "#ffb020"   # Compatibility alias pointing to ACCENT_AMBER
DANGER = "#ff3b5c"        # Deleted events, active P3 earthquakes (--color-danger)
DANGER_BG = "#2b1010"
INFO = "#3b82f6"          # Informational status, pending queues
INFO_BG = "#0d1e38"

# Typography Families
FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

# Radii
RADIUS_SM = 4             # --radius-sm: 4px
RADIUS_MD = 8             # --radius-md: 8px
RADIUS_LG = 12            # --radius-lg: 12px
RADIUS_XL = 20            # --radius-xl: 20px
RADIUS_FULL = 999

