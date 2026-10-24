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

class FlightPanel(QFrame):
    # Sinyal yang membawa data callsign asli saat di-klik
    clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FlightPanel")
        self.setFixedHeight(65)
        self.setCursor(Qt.PointingHandCursor) # Ubah kursor jadi tangan saat hover

        self.original_callsign = "" # Simpan callsign asli dari server

        p_layout = QVBoxLayout(self)
        p_layout.setContentsMargins(10, 8, 10, 8)
        p_layout.setSpacing(2)

        # Baris 1: Callsign, Tipe, Kecepatan
        row1 = QHBoxLayout()
        self.lbl_callsign = QLabel("CALLSIGN")
        self.lbl_callsign.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")

        self.lbl_type = QLabel("TYPE")
        self.lbl_type.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold; margin-left: 5px;")

        self.lbl_speed = QLabel("0 kts")
        self.lbl_speed.setObjectName("AccentText")

        row1.addWidget(self.lbl_callsign)
        row1.addWidget(self.lbl_type)
        row1.addStretch()
        row1.addWidget(self.lbl_speed)

        # Baris 2: Rute
        self.lbl_route = QLabel("N/A - N/A")
        self.lbl_route.setObjectName("SubText")

        p_layout.addLayout(row1)
        p_layout.addWidget(self.lbl_route)

    def set_data(self, callsign, info):
        self.original_callsign = callsign # Simpan untuk dikirim saat diklik

        clean_callsign = callsign.split("-")[0] if "-" in callsign else callsign
        self.lbl_callsign.setText(clean_callsign)

        ac_type = info.get("aircraftType", "Unknown")
        self.lbl_type.setText(ac_type.upper())

        # Ubah kecepatan menjadi string, bulatkan angkanya
        speed = int(info.get("speed", 0))
        self.lbl_speed.setText(f"{speed} kts")

        dep = info.get("plan_departing", "N/A")
        arr = info.get("plan_arriving", "N/A")
        self.lbl_route.setText(f"{dep} - {arr}")

    def mousePressEvent(self, event):
        """Deteksi klik pada panel ini."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.original_callsign)
        super().mousePressEvent(event)

class Sidebar(QFrame):
    # Sinyal yang diteruskan ke MainWindow
    flight_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Ganti Judul
        header = QLabel("Current Flights")
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

        self.panels = []
        for _ in range(30):
            p = FlightPanel()
            # Hubungkan sinyal klik panel ke sinyal sidebar
            p.clicked.connect(self.flight_clicked.emit)
            self.panels.append(p)
            self.list_layout.addWidget(p)
            p.hide()

        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area)

    def update_data(self, data_dict):
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1].get("altitude", 0), reverse=True)

        for i, panel in enumerate(self.panels):
            if i < len(sorted_data):
                callsign, info = sorted_data[i]
                panel.set_data(callsign, info)
                panel.show()
            else:
                panel.hide()

class FlightInfoPanel(QFrame):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
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
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    subitem = item.layout().takeAt(0)
                    if subitem.widget():
                        subitem.widget().deleteLater()
                item.layout().deleteLater()

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
