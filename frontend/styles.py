# frontend/styles.py

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #131313;
}
QWidget {
    color: #e0e0e0;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
}

/* --- SIDEBAR & PANEL INFO --- */
QFrame#Sidebar {
    background-color: rgba(25, 25, 25, 0.95);
    border-radius: 12px;
    border: 1px solid #333;
}

QFrame#FlightPanel {
    background-color: #2b2b2b;
    border-radius: 8px;
    border: 1px solid #333;
}
QFrame#FlightPanel:hover {
    background-color: #3a3a3a;
    border: 1px solid #f4b400;
}

/* --- SCROLLBAR CUSTOM --- */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #f4b400;
    min-height: 30px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #ffc400;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

/* --- TOP BAR & BOTTOM TOOLBAR --- */
QLineEdit#SearchBar {
    background-color: rgba(255, 255, 255, 0.95);
    color: #121212;
    border-radius: 20px;
    padding: 10px 20px;
    font-size: 14px;
    border: none;
}
QFrame#BottomToolbar {
    background-color: rgba(25, 25, 25, 0.95);
    border-radius: 30px;
    border: 1px solid #444;
}
QPushButton#ToolBtn {
    background: transparent;
    border: none;
    color: #aaa;
    font-size: 13px;
    padding: 10px 15px;
}
QPushButton#ToolBtn:hover {
    color: #ffffff;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
}

/* --- MAP CONTROLS --- */
QPushButton#ZoomBtn {
    background-color: rgba(40, 40, 40, 0.9);
    color: white;
    font-size: 20px;
    font-weight: bold;
    border-radius: 20px;
    border: 1px solid #555;
}
QPushButton#ZoomBtn:hover {
    background-color: rgba(70, 70, 70, 0.9);
}

/* --- TEXT & LABELS --- */
QLabel#AppLogo {
    font-size: 22px;
    font-weight: bold;
    color: white;
}
QLabel#HeaderText {
    font-size: 16px;
    font-weight: bold;
    color: white;
}
QLabel#AccentText {
    color: #f4b400;
    font-weight: bold;
}
QLabel#SubText {
    color: #999;
    font-size: 12px;
}

/* --- INFO PANEL SPECIFIC --- */
QFrame#InfoPanel {
    background-color: #1a1a1a;
    border-radius: 12px;
    border: 1px solid #333;
}
QLabel#InfoCallsign {
    font-size: 24px;
    font-weight: bold;
    color: white;
}
QLabel#InfoAirline {
    font-size: 14px;
    color: #aaa;
}
QLabel#InfoBadge {
    background-color: #333;
    color: #ccc;
    font-size: 11px;
    font-weight: bold;
    border-radius: 4px;
    padding: 3px 8px;
}
QLabel#RouteCode {
    font-size: 26px;
    font-weight: bold;
    color: white;
}
QFrame#TelemetryBox {
    background-color: #222;
    border: 1px solid #333;
    border-radius: 6px;
}
QLabel#DataLabel {
    color: #777;
    font-size: 10px;
    font-weight: bold;
}
QLabel#DataValue {
    color: #f4b400;
    font-size: 16px;
    font-weight: bold;
}
QPushButton#CopyBtn {
    background-color: transparent;
    border: none;
    color: #4ade80;
    font-size: 14px;
    font-weight: bold;
    text-align: left;
}
QPushButton#CopyBtn:hover {
    color: #86efac;
    text-decoration: underline;
}

/* --- POPUP PANEL (FILTERS/SETTINGS/WEATHER) --- */
QFrame#PopupPanel {
    background-color: #1e1e1e;
    border-radius: 12px;
    border: 1px solid #555;
}

/* Checkbox Modern */
QCheckBox {
    color: #e0e0e0;
    font-size: 13px;
    spacing: 10px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #555;
    background: #1e1e1e;
}
QCheckBox::indicator:hover {
    border: 2px solid #f4b400;
}
QCheckBox::indicator:checked {
    background: #f4b400;
    border: 2px solid #f4b400;
}

/* Slider Modern */
QSlider::groove:horizontal {
    height: 6px;
    background: #333;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #f4b400;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #f4b400;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
    border: 2px solid #1e1e1e;
}
QSlider::handle:horizontal:hover {
    background: #ffc400;
}
"""
