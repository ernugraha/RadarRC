# frontend/ui_components.py

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal

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
        self.setFixedSize(340, 600) # Sedikit lebih lebar agar muat teks

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel("Most tracked flights")
        header.setObjectName("HeaderText")
        layout.addWidget(header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area)

    def update_data(self, data_dict):
        # PERBAIKAN CRASH: Gunakan deleteLater(), jangan setParent(None)
        for i in reversed(range(self.list_layout.count())):
            widget_to_remove = self.list_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.deleteLater()

        # Top 20 berdasarkan ketinggian
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1].get("altitude", 0), reverse=True)[:20]

        for i, (callsign, info) in enumerate(sorted_data):
            panel = self.create_flight_panel(callsign, info)
            self.list_layout.addWidget(panel)

    def create_flight_panel(self, callsign, info):
        panel = QFrame()
        panel.setObjectName("FlightPanel")
        panel.setFixedHeight(65)
        p_layout = QVBoxLayout(panel)
        p_layout.setContentsMargins(10, 8, 10, 8)
        p_layout.setSpacing(4)

        # --- BARIS 1: Callsign, Badge, Altitude ---
        row1 = QHBoxLayout()
        lbl_callsign = QLabel(callsign.split("-")[0] if "-" in callsign else callsign)
        lbl_callsign.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")

        ac_type = info.get("aircraftType", "Unknown")
        # Ambil 4 huruf pertama tipe pesawat sebagai badge
        badge_text = ac_type[:4].upper() if ac_type else "UNKN"
        lbl_badge = QLabel(badge_text)
        lbl_badge.setObjectName("BadgeBlue")

        alt = info.get("altitude", 0)
        lbl_alt = QLabel(f"{int(alt):,}")
        lbl_alt.setObjectName("AccentText")

        row1.addWidget(lbl_callsign)
        row1.addWidget(lbl_badge)
        row1.addStretch()
        row1.addWidget(lbl_alt)

        # --- BARIS 2: Rute ---
        row2 = QHBoxLayout()
        dep = info.get("plan_departing", "N/A")
        arr = info.get("plan_arriving", "N/A")

        lbl_route = QLabel(f"{dep} - {arr}")
        lbl_route.setObjectName("SubText")

        row2.addWidget(lbl_route)
        row2.addStretch()

        p_layout.addLayout(row1)
        p_layout.addLayout(row2)
        return panel

class FlightInfoPanel(QFrame):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedSize(340, 600)
        self.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("FLIGHT INFO")
        self.lbl_title.setObjectName("HeaderText")

        btn_close = QPushButton("X")
        btn_close.setFixedSize(25, 25)
        btn_close.setStyleSheet("background: #333; color: white; border-radius: 12px; font-weight: bold;")
        btn_close.clicked.connect(self.closed.emit)

        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_close)
        layout.addLayout(header_layout)

        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(10)
        layout.addLayout(self.content_layout)
        layout.addStretch()

    def set_flight_data(self, callsign, info):
        for i in reversed(range(self.content_layout.count())):
            widget_to_remove = self.content_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.deleteLater()

        self.lbl_title.setText(f"INFO: {callsign}")

        data_points = [
            ("Aircraft", info.get("aircraftType", "Unknown")),
            ("Pilot", info.get("playerName", "Unknown")),
            ("Altitude", f"{int(info.get('altitude', 0))} ft"),
            ("Speed", f"{int(info.get('speed', 0))} kts"),
            ("Heading", f"{int(info.get('heading', 0))}°"),
            ("Departure", info.get("plan_departing", "N/A")),
            ("Arrival", info.get("plan_arriving", "N/A")),
        ]

        for label, value in data_points:
            row = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #888; font-size: 11px;")
            val = QLabel(str(value))
            val.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
            row.addWidget(lbl)
            row.addWidget(val)
            self.content_layout.addLayout(row)

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
