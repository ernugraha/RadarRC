# frontend/ui_components.py

import os
import re
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QWidget, QScrollArea, QGridLayout, QApplication)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from frontend.airlines import get_airline_name, get_airline_keys

def find_aircraft_photo(callsign, aircraft_type, photo_dir="assets/aircraft"):
    if not os.path.exists(photo_dir):
        return None

    at_lower = aircraft_type.lower()
    ac_clean = at_lower.replace(" ", "").replace("-", "")
    nums = ''.join(re.findall(r'\d+', ac_clean))

    model_candidates = set()
    if nums:
        model_candidates.add(nums)
        if "boeing" in at_lower: model_candidates.add(f"b{nums}")
        if "airbus" in at_lower: model_candidates.add(f"a{nums}")
    if ac_clean:
        model_candidates.add(ac_clean)

    airline_keys = get_airline_keys(callsign)
    airline_keys.extend(["generic", "default", callsign.lower()])

    candidates = []
    for model in model_candidates:
        for akey in airline_keys:
            candidates.append(f"{model}_{akey}.png")
            candidates.append(f"{akey}_{model}.png")

    candidates.extend([f"{m}.png" for m in model_candidates])
    candidates.extend([f"{a}.png" for a in airline_keys])

    for name in candidates:
        path = os.path.join(photo_dir, name)
        if os.path.isfile(path):
            return path
    return None

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
    clicked = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FlightPanel")
        self.setFixedHeight(65)
        self.setCursor(Qt.PointingHandCursor)
        self.original_callsign = ""
        p_layout = QVBoxLayout(self)
        p_layout.setContentsMargins(10, 8, 10, 8)
        p_layout.setSpacing(2)
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
        self.lbl_route = QLabel("N/A - N/A")
        self.lbl_route.setObjectName("SubText")
        p_layout.addLayout(row1)
        p_layout.addWidget(self.lbl_route)

    def set_data(self, callsign, info):
        self.original_callsign = callsign
        clean_callsign = callsign.split("-")[0] if "-" in callsign else callsign
        self.lbl_callsign.setText(clean_callsign)
        self.lbl_type.setText(info.get("aircraftType", "Unknown").upper())
        self.lbl_speed.setText(f"{int(info.get('speed', 0))} kts")
        self.lbl_route.setText(f"{info.get('plan_departing', 'N/A')} - {info.get('plan_arriving', 'N/A')}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.original_callsign)
        super().mousePressEvent(event)

class Sidebar(QFrame):
    flight_clicked = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
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
        self.setObjectName("InfoPanel")
        self.setVisible(False)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ================= HEADER =================
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #242424; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)

        row1 = QHBoxLayout()
        self.lbl_callsign = QLabel("CALLSIGN")
        self.lbl_callsign.setObjectName("InfoCallsign")
        self.lbl_badge = QLabel("TYPE")
        self.lbl_badge.setObjectName("InfoBadge")

        btn_close = QPushButton("X")
        btn_close.setFixedSize(25, 25)
        btn_close.setStyleSheet("background: #333; color: white; border-radius: 12px; font-weight: bold;")
        btn_close.clicked.connect(self.closed.emit)

        row1.addWidget(self.lbl_callsign)
        row1.addWidget(self.lbl_badge)
        row1.addStretch()
        row1.addWidget(btn_close)

        self.lbl_airline = QLabel("Airline Name")
        self.lbl_airline.setObjectName("InfoAirline")

        header_layout.addLayout(row1)
        header_layout.addWidget(self.lbl_airline)
        main_layout.addWidget(header_frame)

        # ================= PHOTO PLACEHOLDER =================
        photo_frame = QFrame()
        photo_layout = QVBoxLayout(photo_frame)
        photo_layout.setContentsMargins(15, 15, 15, 0)

        self.photo_box = QLabel("?")
        self.photo_box.setObjectName("PhotoBox")
        self.photo_box.setFixedHeight(180)
        self.photo_box.setAlignment(Qt.AlignCenter)

        photo_layout.addWidget(self.photo_box)
        main_layout.addWidget(photo_frame)

        # ================= ROUTE =================
        route_frame = QFrame()
        route_layout = QHBoxLayout(route_frame)
        route_layout.setContentsMargins(15, 15, 15, 15)

        self.lbl_dep = QLabel("N/A")
        self.lbl_dep.setObjectName("RouteCode")
        self.lbl_dep.setAlignment(Qt.AlignCenter)

        arrow = QLabel("➔")
        arrow.setStyleSheet("color: #f4b400; font-size: 20px;")

        self.lbl_arr = QLabel("N/A")
        self.lbl_arr.setObjectName("RouteCode")
        self.lbl_arr.setAlignment(Qt.AlignCenter)

        route_layout.addWidget(self.lbl_dep, 1)
        route_layout.addWidget(arrow)
        route_layout.addWidget(self.lbl_arr, 1)
        main_layout.addWidget(route_frame)

        # ================= TELEMETRY GRID =================
        telemetry_frame = QFrame()
        tele_layout = QGridLayout(telemetry_frame)
        tele_layout.setContentsMargins(15, 5, 15, 15)
        tele_layout.setSpacing(10)

        self.val_alt = self.create_telemetry_box(tele_layout, 0, 0, "ALTITUDE")
        self.val_spd = self.create_telemetry_box(tele_layout, 0, 1, "SPEED")
        self.val_hdg = self.create_telemetry_box(tele_layout, 1, 0, "HEADING")
        self.val_vs  = self.create_telemetry_box(tele_layout, 1, 1, "V/SPEED")

        main_layout.addWidget(telemetry_frame)

        main_layout.addStretch()

        # ================= PILOT INFO =================
        pilot_frame = QFrame()
        pilot_frame.setStyleSheet("background-color: #111; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;")
        pilot_layout = QVBoxLayout(pilot_frame)
        pilot_layout.setContentsMargins(15, 10, 15, 15)

        lbl_p = QLabel("PILOT / USERNAME (Click to copy)")
        lbl_p.setObjectName("DataLabel")

        self.btn_pilot = QPushButton("Unknown")
        self.btn_pilot.setObjectName("CopyBtn")
        self.btn_pilot.setCursor(Qt.PointingHandCursor)
        self.btn_pilot.clicked.connect(self.copy_username)

        pilot_layout.addWidget(lbl_p)
        pilot_layout.addWidget(self.btn_pilot)

        main_layout.addWidget(pilot_frame)

        self.current_pilot_name = "Unknown"

    def create_telemetry_box(self, layout, row, col, title):
        box = QFrame()
        box.setObjectName("TelemetryBox")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(10, 8, 10, 8)
        box_layout.setSpacing(2)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("DataLabel")
        lbl_val = QLabel("0")
        lbl_val.setObjectName("DataValue")
        box_layout.addWidget(lbl_title)
        box_layout.addWidget(lbl_val)
        layout.addWidget(box, row, col)
        return lbl_val

    def copy_username(self):
        QApplication.clipboard().setText(self.current_pilot_name)
        self.btn_pilot.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.btn_pilot.setText(self.current_pilot_name))

    def set_flight_data(self, callsign, info):
        airline_name = get_airline_name(callsign)
        self.lbl_callsign.setText(callsign)
        self.lbl_badge.setText(info.get("aircraftType", "Unknown").upper())
        self.lbl_airline.setText(airline_name)

        dep = info.get("plan_departing", "N/A")
        arr = info.get("plan_arriving", "N/A")
        self.lbl_dep.setText(dep if dep else "???")
        self.lbl_arr.setText(arr if arr else "???")

        self.val_alt.setText(f"{int(info.get('altitude', 0)):,} ft")
        self.val_spd.setText(f"{int(info.get('speed', 0))} kts")
        self.val_hdg.setText(f"{int(info.get('heading', 0))}°")
        self.val_vs.setText("0 ft/m")

        self.current_pilot_name = info.get("playerName", "Unknown")
        self.btn_pilot.setText(self.current_pilot_name)

        # ================= LOGIKA LOAD FOTO (ZOOM 125%) =================
        photo_path = find_aircraft_photo(callsign, info.get("aircraftType", ""))

        if photo_path:
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                target_w, target_h = 310, 180

                # KUNCI ZOOM 125%: Perbesar target scaling sebelum dipotong
                zoom_factor = 1.25
                scale_w = int(target_w * zoom_factor)
                scale_h = int(target_h * zoom_factor)

                # 1. Perbesar gambar agar menutupi area yang lebih besar
                scaled = pixmap.scaled(scale_w, scale_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

                # 2. Potong bagian tengahnya tepat seukuran kotak asli (310x180)
                x_offset = (scaled.width() - target_w) // 2
                y_offset = (scaled.height() - target_h) // 2
                cropped = scaled.copy(x_offset, y_offset, target_w, target_h)

                self.photo_box.setPixmap(cropped)
                self.photo_box.setText("")
                self.photo_box.setStyleSheet("background-color: #000; border: 1px solid #444; border-radius: 6px;")
            else:
                self.photo_box.clear()
                self.photo_box.setText("?")
                self.photo_box.setStyleSheet("")
        else:
            self.photo_box.clear()
            self.photo_box.setText("?")
            self.photo_box.setStyleSheet("")

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
