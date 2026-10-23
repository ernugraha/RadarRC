# frontend/ui_components.py

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QWidget)
from PySide6.QtCore import Qt

class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 0)

        logo = QLabel("RadarRC")
        logo.setObjectName("AppLogo")

        search_bar = QLineEdit()
        search_bar.setObjectName("SearchBar")
        search_bar.setPlaceholderText("Find flights, airports and more...")
        search_bar.setFixedWidth(450)

        view_btn = QPushButton("VIEW Map v")
        view_btn.setObjectName("ViewMapBtn")

        layout.addWidget(logo)
        layout.addStretch()
        layout.addWidget(search_bar)
        layout.addStretch()
        layout.addWidget(view_btn)

class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel("Most tracked flights")
        header.setObjectName("HeaderText")
        layout.addWidget(header)

        panel1 = self.create_flight_panel("1. N/A B744", "1,834", "N/A - N/A")
        layout.addWidget(panel1)

        panel2 = self.create_flight_panel("2. AFR49HG A321", "1,325", "Paris CDG - Nantes NTE")
        layout.addWidget(panel2)

        layout.addStretch()

    def create_flight_panel(self, callsign, tracked, route):
        panel = QFrame()
        panel.setObjectName("FlightPanel")
        p_layout = QVBoxLayout(panel)
        p_layout.setContentsMargins(10, 10, 10, 10)

        row1 = QHBoxLayout()
        lbl_callsign = QLabel(callsign)
        lbl_callsign.setStyleSheet("font-size: 15px; font-weight: bold;")

        lbl_tracked = QLabel(f"{tracked} users")
        lbl_tracked.setObjectName("AccentText")

        row1.addWidget(lbl_callsign)
        row1.addStretch()
        row1.addWidget(lbl_tracked)

        lbl_route = QLabel(route)
        lbl_route.setObjectName("SubText")

        p_layout.addLayout(row1)
        p_layout.addWidget(lbl_route)
        return panel

class BottomToolbar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomToolbar")
        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(10)

        buttons = ["Settings", "Weather", "Filters", "Widgets", "Playback"]
        for text in buttons:
            btn = QPushButton(text)
            btn.setObjectName("ToolBtn")
            layout.addWidget(btn)

class MapControls(QWidget):
    def __init__(self, map_view, parent=None):
        super().__init__(parent)
        self.map_view = map_view

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        btn_in = QPushButton("+")
        btn_in.setFixedSize(40, 40)
        btn_in.setObjectName("ZoomBtn")
        btn_in.clicked.connect(self.map_view.zoom_in)

        btn_out = QPushButton("-")
        btn_out.setFixedSize(40, 40)
        btn_out.setObjectName("ZoomBtn")
        btn_out.clicked.connect(self.map_view.zoom_out)

        layout.addWidget(btn_in)
        layout.addWidget(btn_out)
