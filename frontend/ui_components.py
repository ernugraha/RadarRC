# frontend/ui_components.py

from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal

class TopBar(QWidget):
    # ... (Sama seperti sebelumnya, biarkan saja) ...
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
        self.setFixedSize(320, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel("Most tracked flights")
        header.setObjectName("HeaderText")
        layout.addWidget(header)

        # Gunakan Scroll Area untuk menampung banyak pesawat
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(5)
        self.list_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area)

    def update_data(self, data_dict):
        """Memperbarui daftar pesawat di sidebar (Top 15 berdasarkan ketinggian)."""
        # Hapus semua item lama
        for i in reversed(range(self.list_layout.count())):
            widget_to_remove = self.list_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        # Urutkan berdasarkan ketinggian tertinggi
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1].get("altitude", 0), reverse=True)[:15]

        for i, (callsign, info) in enumerate(sorted_data):
            panel = self.create_flight_panel(callsign, info)
            self.list_layout.addWidget(panel)

    def create_flight_panel(self, callsign, info):
        panel = QFrame()
        panel.setObjectName("FlightPanel")
        p_layout = QVBoxLayout(panel)
        p_layout.setContentsMargins(10, 10, 10, 10)

        row1 = QHBoxLayout()
        lbl_callsign = QLabel(callsign)
        lbl_callsign.setStyleSheet("font-size: 14px; font-weight: bold;")

        alt = info.get("altitude", 0)
        lbl_alt = QLabel(f"FL{int(alt/100):03d}")
        lbl_alt.setObjectName("AccentText")

        row1.addWidget(lbl_callsign)
        row1.addStretch()
        row1.addWidget(lbl_alt)

        ac_type = info.get("aircraftType", "Unknown")
        lbl_type = QLabel(ac_type)
        lbl_type.setObjectName("SubText")

        p_layout.addLayout(row1)
        p_layout.addWidget(lbl_type)
        return panel

class FlightInfoPanel(QFrame):
    closed = Signal() # Sinyal saat tombol close diklik

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar") # Gunakan style yang sama dengan sidebar
        self.setFixedSize(320, 500)
        self.setVisible(False) # Sembunyikan secara default

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header Panel Info
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("FLIGHT INFO")
        self.lbl_title.setObjectName("HeaderText")

        btn_close = QPushButton("X")
        btn_close.setFixedSize(25, 25)
        btn_close.setStyleSheet("background: #333; color: white; border-radius: 12px;")
        btn_close.clicked.connect(self.closed.emit)

        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_close)
        layout.addLayout(header_layout)

        # Konten Info
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(15)
        layout.addLayout(self.content_layout)

        layout.addStretch()

    def set_flight_data(self, callsign, info):
        """Mengisi data penerbangan ke panel."""
        # Hapus data lama
        for i in reversed(range(self.content_layout.count())):
            widget_to_remove = self.content_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        self.lbl_title.setText(f"INFO: {callsign}")

        # Buat baris data
        data_points = [
            ("Aircraft Type", info.get("aircraftType", "Unknown")),
            ("Pilot Name", info.get("playerName", "Unknown")),
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
    # ... (Sama seperti sebelumnya, biarkan saja) ...
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
    # ... (Sama seperti sebelumnya, biarkan saja) ...
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
