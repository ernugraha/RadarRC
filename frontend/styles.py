# frontend/styles.py

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #131313;
}
QWidget {
    color: #e0e0e0;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
}

/* --- OVERLAY CONTAINER --- */
QWidget#OverlayContainer {
    background: transparent;
}

/* --- SIDEBAR (KIRI) --- */
QFrame#Sidebar {
    background-color: rgba(25, 25, 25, 0.95);
    border-radius: 12px;
    border: 1px solid #333;
}
QFrame#FlightPanel {
    background-color: rgba(40, 40, 40, 0.9);
    border-radius: 8px;
    margin-bottom: 8px;
}
QFrame#FlightPanel:hover {
    background-color: rgba(55, 55, 55, 0.9);
}

/* --- TOP BAR --- */
QLineEdit#SearchBar {
    background-color: rgba(255, 255, 255, 0.95);
    color: #121212;
    border-radius: 20px;
    padding: 10px 20px;
    font-size: 14px;
    border: none;
}
QPushButton#ViewMapBtn {
    background-color: rgba(30, 30, 30, 0.85);
    color: white;
    border-radius: 20px;
    padding: 10px 20px;
    font-weight: bold;
    border: 1px solid #444;
}
QPushButton#ViewMapBtn:hover {
    background-color: rgba(50, 50, 50, 0.85);
}

/* --- BOTTOM TOOLBAR --- */
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

/* --- MAP CONTROLS (ZOOM) --- */
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

QPushButton#EditBtn {
    background-color: rgba(40, 40, 40, 0.9);
    color: white;
    font-size: 12px;
    font-weight: bold;
    border-radius: 25px;
    border: 1px solid #555;
}
QPushButton#EditBtn:hover {
    background-color: rgba(70, 70, 70, 0.9);
}

/* --- TEKS & LABEL --- */
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
    font-size: 13px;
}
"""
