"""Dev Intelligence dark blue color theme."""

BG_PRIMARY = "#060809"
BG_PANEL = "#090c10"
BG_CARD = "#0c1016"
BORDER = "#0e1c2a"
ACCENT_BLUE = "#378add"
ACCENT_DIM = "#0c2240"
SUCCESS = "#1d9e75"
WARNING = "#ba7517"
CRITICAL = "#e24b4a"
INFO = "#85b7eb"
TEXT = "#b5d4f4"
TEXT_DIM = "#142233"
FONT = "JetBrains Mono, monospace"

CARD_STYLE = {
    "backgroundColor": BG_CARD,
    "border": f"1px solid {BORDER}",
    "borderRadius": "4px",
    "padding": "12px",
    "marginBottom": "12px",
    "fontFamily": FONT,
}

HEADER_STYLE = {
    "backgroundColor": BG_PANEL,
    "color": ACCENT_BLUE,
    "fontFamily": FONT,
    "fontSize": "13px",
    "padding": "8px 16px",
    "borderBottom": f"1px solid {BORDER}",
    "letterSpacing": "2px",
    "textTransform": "uppercase",
}

PLOTLY_THEME = {
    "paper_bgcolor": BG_PANEL,
    "plot_bgcolor": BG_PRIMARY,
    "font": {"color": TEXT, "family": FONT, "size": 11},
    "colorway": [ACCENT_BLUE, SUCCESS, WARNING, CRITICAL, INFO, "#a855f7"],
}
