# frontend/config.py
# RadarRC - FlightEye-inspired Grey Theme

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 780
WINDOW_TITLE = "RadarRC - ATC24 Radar"

# ==== Canvas (map area) ====
BG_COLOR          = "#050505"
GRID_COLOR        = "#202020"
GRID_LABEL        = "#888888"

# ==== Text ====
TEXT_COLOR        = "#e0e0e0"
TEXT_DIM          = "#a0a0a0"
ACCENT_COLOR      = "#ffd400"

# ==== Panel / sidebar ====
PANEL_BG          = "#1c1c1c"
PANEL_BORDER      = "#383838"
CARD_BG           = "#252525"
HOVER_BG          = "#353535"
SELECTED_BG       = "#414141"

# ==== Section header ====
SECTION_BG        = "#303030"
SECTION_TEXT      = "#f5f5f5"
SUBHEADER_BG      = "#292929"

# ==== Aircraft colors by altitude ====
COLOR_LOW         = "#d4a72c"    # muted yellow < 2000m
COLOR_MID         = "#d9843b"    # muted orange 2000-5000m
COLOR_HIGH        = "#cc5050"    # muted red > 5000m
COLOR_GROUND      = "#528fba"    # muted blue on ground

# ==== Map ====
COAST_COLOR       = "#404040"
BOUNDARY_COLOR    = "#292929"

# ==== Layout ====
SCALE = 0.005
CENTER_X = 0
CENTER_Y = 0
FLIP_Y = True

HEADER_HEIGHT = 44
FOOTER_HEIGHT = 26
SIDEBAR_WIDTH = 260

# ==== Icons ====
ICON_BASE_SIZE = 7.0
ICON_MIN_MULT = 0.9
ICON_MAX_MULT = 1.8
ICON_SELECTED_BOOST = 1.25

TRAIL_LENGTH = 300
ASSETS_DIR = "assets/aircraft"
WS_URL = "ws://localhost:8765"
