# frontend/ui_components.py

import os
import re
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QWidget, QScrollArea, QGridLayout,
                               QApplication, QSizePolicy, QCheckBox, QSlider)
from PySide6.QtCore import Qt, Signal, QTimer, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QPen, QColor
from frontend.airlines import get_airline_name, get_airline_keys, get_airline_icao
from frontend.airports import get_airport_name

# ==========================================
# FUNGSI PENCARI ASET (FOTO & LOGO)
# ==========================================
def find_aircraft_photo(callsign, aircraft_type, photo_dir="assets/aircraft"):
    if not os.path.exists(photo_dir): return None
    at_lower = aircraft_type.lower()
    ac_clean = at_lower.replace(" ", "").replace("-", "")
    nums = ''.join(re.findall(r'\d+', ac_clean))
    model_candidates = set()
    if nums:
        model_candidates.add(nums)
        if "boeing" in at_lower: model_candidates.add(f"b{nums}")
        if "airbus" in at_lower: model_candidates.add(f"a{nums}")
    if ac_clean: model_candidates.add(ac_clean)
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
        if os.path.isfile(path): return path
    return None

def find_airline_logo(callsign, logo_dir="assets/logos"):
    if not os.path.exists(logo_dir): return None
    airline_name = get_airline_name(callsign)
    formatted_name = airline_name.replace(" ", "_").lower()
    for filename in os.listdir(logo_dir):
        if filename.endswith(".svg") and formatted_name in filename.lower():
            return os.path.join(logo_dir, filename)
    return None

def find_airport_photo(icao, photo_dir="assets/airports"):
    if not os.path.exists(photo_dir): return None
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(photo_dir, f"{icao.lower()}{ext}")
        if os.path.isfile(path): return path
    return None

# ==========================================
# TOP BAR
# ==========================================
class TopBar(QWidget):
    search_triggered = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 0)
        logo = QLabel("RadarRC")
        logo.setObjectName("AppLogo")

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("Find flights (e.g., BAW123, PilotName)... (Press Enter)")
        self.search_bar.setFixedWidth(450)
        self.search_bar.returnPressed.connect(self.on_search_enter)

        layout.addWidget(logo)
        layout.addStretch()
        layout.addWidget(self.search_bar)
        layout.addStretch()

    def on_search_enter(self):
        query = self.search_bar.text().strip()
        if query: self.search_triggered.emit(query)

# ==========================================
# SIDEBAR KIRI
# ==========================================
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
        row1.setSpacing(5)

        self.lbl_callsign = QLabel("CALLSIGN")
        self.lbl_callsign.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        self.lbl_callsign.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.lbl_type = QLabel("TYPE")
        self.lbl_type.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold;")
        self.lbl_type.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        self.lbl_speed = QLabel("0 kts")
        self.lbl_speed.setObjectName("AccentText")

        row1.addWidget(self.lbl_callsign, 3)
        row1.addWidget(self.lbl_type, 2)
        row1.addWidget(self.lbl_speed)

        self.lbl_route = QLabel("N/A - N/A")
        self.lbl_route.setObjectName("SubText")

        p_layout.addLayout(row1)
        p_layout.addWidget(self.lbl_route)

    def set_data(self, callsign, info):
        self.original_callsign = callsign
        icao = get_airline_icao(callsign)
        parts = callsign.split("-")
        flight_num = parts[-1] if len(parts) > 1 else ""
        display_name = f"{icao}{flight_num}" if icao != "???" else parts[0]
        self.lbl_callsign.setText(display_name)

        ac_type = info.get("aircraftType", "Unknown").upper()
        if len(ac_type) > 12: ac_type = ac_type[:10] + "..."
        self.lbl_type.setText(ac_type)
        self.lbl_speed.setText(f"{int(info.get('speed', 0))} kts")

        dep_code = info.get("plan_departing", "")
        arr_code = info.get("plan_arriving", "")
        if dep_code and arr_code:
            self.lbl_route.setText(f"{dep_code} - {arr_code}")
        else:
            self.lbl_route.setText("N/A - N/A")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit(self.original_callsign)
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
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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

# ==========================================
# PANEL INFO PESAWAT (KANAN)
# ==========================================
class FlightInfoPanel(QFrame):
    closed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InfoPanel")
        self.setVisible(False)

        # --- SCROLL AREA DITAMBAHKAN DI SINI ---
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # ---------------------------------------

        # HEADER
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
        self.lbl_airline.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        header_layout.addLayout(row1)
        header_layout.addWidget(self.lbl_airline)
        main_layout.addWidget(header_frame)

        # FOTO PESAWAT
        photo_frame = QFrame()
        photo_layout = QVBoxLayout(photo_frame)
        photo_layout.setContentsMargins(15, 15, 15, 0)

        self.photo_box = QLabel("?")
        self.photo_box.setFixedSize(310, 210)
        self.photo_box.setAlignment(Qt.AlignCenter)
        photo_layout.addWidget(self.photo_box, alignment=Qt.AlignHCenter)
        main_layout.addWidget(photo_frame)

        # RUTE
        route_frame = QFrame()
        route_layout = QHBoxLayout(route_frame)
        route_layout.setContentsMargins(15, 15, 15, 15)
        route_layout.setSpacing(10)

        dep_layout = QVBoxLayout()
        dep_layout.setSpacing(0)
        self.lbl_dep = QLabel("N/A")
        self.lbl_dep.setObjectName("RouteCode")
        self.lbl_dep.setAlignment(Qt.AlignCenter)
        self.lbl_dep_name = QLabel("")
        self.lbl_dep_name.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        self.lbl_dep_name.setAlignment(Qt.AlignCenter)
        dep_layout.addWidget(self.lbl_dep)
        dep_layout.addWidget(self.lbl_dep_name)

        arrow = QLabel("->")
        arrow.setStyleSheet("color: #f4b400; font-size: 20px; font-weight: bold;")
        arrow.setAlignment(Qt.AlignCenter)

        arr_layout = QVBoxLayout()
        arr_layout.setSpacing(0)
        self.lbl_arr = QLabel("N/A")
        self.lbl_arr.setObjectName("RouteCode")
        self.lbl_arr.setAlignment(Qt.AlignCenter)
        self.lbl_arr_name = QLabel("")
        self.lbl_arr_name.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        self.lbl_arr_name.setAlignment(Qt.AlignCenter)
        arr_layout.addWidget(self.lbl_arr)
        arr_layout.addWidget(self.lbl_arr_name)

        route_layout.addLayout(dep_layout, 1)
        route_layout.addWidget(arrow)
        route_layout.addLayout(arr_layout, 1)
        main_layout.addWidget(route_frame)

        # TELEMETRI
        telemetry_frame = QFrame()
        tele_layout = QGridLayout(telemetry_frame)
        tele_layout.setContentsMargins(15, 5, 15, 15)
        tele_layout.setSpacing(10)
        self.val_alt = self.create_telemetry_box(tele_layout, 0, 0, "ALTITUDE")
        self.val_spd = self.create_telemetry_box(tele_layout, 0, 1, "SPEED")
        self.val_hdg = self.create_telemetry_box(tele_layout, 1, 0, "HEADING")
        self.val_vs  = self.create_telemetry_box(tele_layout, 1, 1, "V/SPEED")
        main_layout.addWidget(telemetry_frame)

        # main_layout.addStretch() # DIHAPUS

        # PILOT
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

        # --- MASUKKAN KE SCROLL AREA ---
        self.scroll.setWidget(content)
        outer_layout.addWidget(self.scroll)

        self.current_pilot_name = "Unknown"

    def create_telemetry_box(self, layout, row, col, title):
        box = QFrame()
        box.setObjectName("TelemetryBox")
        # KUNCI PERBAIKAN: Paksa style langsung di sini agar border tidak hilang di dalam QScrollArea
        box.setStyleSheet("""
            QFrame {
                background-color: #222;
                border: 1px solid #555;
                border-radius: 6px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

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
        real_airline = get_airline_name(callsign)
        self.lbl_callsign.setText(callsign)
        self.lbl_badge.setText(info.get("aircraftType", "Unknown").upper())

        logo_path = find_airline_logo(callsign)
        if logo_path:
            self.lbl_airline.setText(f"<img src='{logo_path}' height='16' style='vertical-align:middle;'> &nbsp; {real_airline}")
            self.lbl_airline.setTextFormat(Qt.RichText)
        else:
            self.lbl_airline.setText(real_airline)

        dep_code = info.get("plan_departing", "")
        arr_code = info.get("plan_arriving", "")

        self.lbl_dep.setText(dep_code if dep_code else "N/A")
        self.lbl_arr.setText(arr_code if arr_code else "N/A")

        dep_name = get_airport_name(dep_code) if dep_code else ""
        arr_name = get_airport_name(arr_code) if arr_code else ""
        self.lbl_dep_name.setText(dep_name.upper())
        self.lbl_arr_name.setText(arr_name.upper())

        self.val_alt.setText(f"{int(info.get('altitude', 0)):,} ft")
        self.val_spd.setText(f"{int(info.get('speed', 0))} kts")
        self.val_hdg.setText(f"{int(info.get('heading', 0))} deg")
        self.val_vs.setText("0 ft/m")

        self.current_pilot_name = info.get("playerName", "Unknown")
        self.btn_pilot.setText(self.current_pilot_name)

        photo_path = find_aircraft_photo(callsign, info.get("aircraftType", ""))
        if photo_path:
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                target_w, target_h = 310, 210
                zoom_factor = 1.25
                scale_w = int(target_w * zoom_factor)
                scale_h = int(target_h * zoom_factor)
                scaled = pixmap.scaled(scale_w, scale_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x_offset = (scaled.width() - target_w) // 2
                y_offset = (scaled.height() - target_h) // 2
                cropped = scaled.copy(x_offset, y_offset, target_w, target_h)
                rounded_pixmap = QPixmap(target_w, target_h)
                rounded_pixmap.fill(Qt.transparent)
                painter = QPainter(rounded_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(QRectF(0.5, 0.5, target_w - 1, target_h - 1), 6, 6)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, cropped)
                painter.setClipping(False)
                pen = QPen(QColor("#444"))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)
                painter.end()
                self.photo_box.setPixmap(rounded_pixmap)
                self.photo_box.setText("")
                self.photo_box.setStyleSheet("background: transparent; border: none;")
            else:
                self.show_placeholder()
        else:
            self.show_placeholder()

    def show_placeholder(self):
        self.photo_box.clear()
        self.photo_box.setText("?")
        self.photo_box.setStyleSheet("background-color: #222; border: 1px solid #444; border-radius: 6px; color: #555; font-size: 48px; font-weight: bold;")

# ==========================================
# PANEL INFO BANDARA (KANAN)
# ==========================================
class AirportInfoPanel(QFrame):
    closed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InfoPanel")
        self.setVisible(False)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1e3a8a; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)

        row1 = QHBoxLayout()
        self.lbl_icao = QLabel("ICAO")
        self.lbl_icao.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")

        btn_close = QPushButton("X")
        btn_close.setFixedSize(25, 25)
        btn_close.setStyleSheet("background: #333; color: white; border-radius: 12px; font-weight: bold;")
        btn_close.clicked.connect(self.closed.emit)

        row1.addWidget(self.lbl_icao)
        row1.addStretch()
        row1.addWidget(btn_close)

        self.lbl_name = QLabel("Airport Name")
        self.lbl_name.setStyleSheet("color: #ccc; font-size: 14px;")

        header_layout.addLayout(row1)
        header_layout.addWidget(self.lbl_name)
        main_layout.addWidget(header_frame)

        # FOTO BANDARA
        photo_frame = QFrame()
        photo_layout = QVBoxLayout(photo_frame)
        photo_layout.setContentsMargins(15, 15, 15, 0)
        self.photo_box = QLabel("?")
        self.photo_box.setFixedSize(310, 180)
        self.photo_box.setAlignment(Qt.AlignCenter)
        photo_layout.addWidget(self.photo_box, alignment=Qt.AlignHCenter)
        main_layout.addWidget(photo_frame)

        # ATC SECTION
        atc_frame = QFrame()
        atc_layout = QVBoxLayout(atc_frame)
        atc_layout.setContentsMargins(15, 10, 15, 10)

        lbl_atc_title = QLabel("ACTIVE CONTROLLERS")
        lbl_atc_title.setObjectName("DataLabel")
        atc_layout.addWidget(lbl_atc_title)

        self.lbl_twr = QLabel("Tower: -")
        self.lbl_gnd = QLabel("Ground: -")
        self.lbl_ctr = QLabel("Center: -")
        for lbl in [self.lbl_twr, self.lbl_gnd, self.lbl_ctr]:
            lbl.setStyleSheet("color: #4ade80; font-size: 14px; font-weight: bold; margin-top: 2px;")
            atc_layout.addWidget(lbl)

        main_layout.addWidget(atc_frame)

        # ATIS SECTION
        atis_frame = QFrame()
        atis_frame.setStyleSheet("background-color: #111; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;")
        atis_layout = QVBoxLayout(atis_frame)
        atis_layout.setContentsMargins(15, 10, 15, 15)

        lbl_atis_title = QLabel("ATIS INFORMATION")
        lbl_atis_title.setObjectName("DataLabel")

        self.txt_atis = QLabel("ATIS Offline")
        self.txt_atis.setStyleSheet("color: #aaa; font-family: 'Consolas', monospace; font-size: 11px;")
        self.txt_atis.setWordWrap(True)

        atis_layout.addWidget(lbl_atis_title)
        atis_layout.addWidget(self.txt_atis)
        main_layout.addWidget(atis_frame)

        self.scroll.setWidget(content)
        outer_layout.addWidget(self.scroll)

    def set_airport_data(self, icao, name, atc_info, atis_data):
        self.lbl_icao.setText(icao)
        self.lbl_name.setText(name)

        photo_path = find_airport_photo(icao)
        if photo_path:
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                target_w, target_h = 310, 180
                scaled = pixmap.scaled(target_w, target_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x_offset = (scaled.width() - target_w) // 2
                y_offset = (scaled.height() - target_h) // 2
                cropped = scaled.copy(x_offset, y_offset, target_w, target_h)

                rounded_pixmap = QPixmap(target_w, target_h)
                rounded_pixmap.fill(Qt.transparent)
                painter = QPainter(rounded_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(QRectF(0.5, 0.5, target_w - 1, target_h - 1), 6, 6)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, cropped)
                painter.setClipping(False)
                pen = QPen(QColor("#444"))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)
                painter.end()

                self.photo_box.setPixmap(rounded_pixmap)
                self.photo_box.setText("")
                self.photo_box.setStyleSheet("background: transparent; border: none;")
            else:
                self.show_placeholder()
        else:
            self.show_placeholder()

        self.lbl_twr.setText("Tower: -")
        self.lbl_gnd.setText("Ground: -")
        self.lbl_ctr.setText("Center: -")

        if atc_info:
            if "TWR" in atc_info: self.lbl_twr.setText(f"Tower: {atc_info['TWR']}")
            if "GND" in atc_info: self.lbl_gnd.setText(f"Ground: {atc_info['GND']}")
            if "CTR" in atc_info: self.lbl_ctr.setText(f"Center: {atc_info['CTR']}")

        if atis_data and atis_data.get("content"):
            self.txt_atis.setText(atis_data.get("content"))
        else:
            self.txt_atis.setText("ATIS Offline")

    def show_placeholder(self):
        self.photo_box.clear()
        self.photo_box.setText("?")
        self.photo_box.setStyleSheet("background-color: #222; border: 1px solid #444; border-radius: 6px; color: #555; font-size: 48px; font-weight: bold;")

# ==========================================
# PANEL POPUP (FILTERS, SETTINGS, WEATHER)
# ==========================================
class FilterPanel(QFrame):
    filters_changed = Signal(bool, int, bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PopupPanel")
        self.setVisible(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.addWidget(QLabel("FILTERS", objectName="HeaderText"))

        self.chk_ground = QCheckBox("Hide Aircraft on Ground")
        self.chk_ground.stateChanged.connect(self.emit)
        layout.addWidget(self.chk_ground)

        self.chk_heli = QCheckBox("Hide Helicopters")
        self.chk_heli.stateChanged.connect(self.emit)
        layout.addWidget(self.chk_heli)

        layout.addWidget(QLabel("Min Altitude:"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 10000)
        self.slider.valueChanged.connect(self.emit)
        layout.addWidget(self.slider)

        self.lbl_alt = QLabel("0 ft", objectName="AccentText")
        self.slider.valueChanged.connect(lambda v: self.lbl_alt.setText(f"{v} ft"))
        layout.addWidget(self.lbl_alt)

    def emit(self):
        self.filters_changed.emit(self.chk_ground.isChecked(), self.slider.value(), self.chk_heli.isChecked())

class SettingsPanel(QFrame):
    settings_changed = Signal(bool, bool, bool, bool) # bounds, trails, labels, airports

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PopupPanel")
        self.setVisible(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.addWidget(QLabel("SETTINGS", objectName="HeaderText"))

        self.chk_bounds = QCheckBox("Show Airspace Boundaries")
        self.chk_bounds.setChecked(True)
        self.chk_bounds.stateChanged.connect(self.emit)
        layout.addWidget(self.chk_bounds)

        self.chk_trails = QCheckBox("Show Aircraft Trails")
        self.chk_trails.setChecked(True)
        self.chk_trails.stateChanged.connect(self.emit)
        layout.addWidget(self.chk_trails)

        self.chk_labels = QCheckBox("Always Show Labels")
        self.chk_labels.stateChanged.connect(self.emit)
        layout.addWidget(self.chk_labels)

        # TOGGLE PIN BANDARA
        self.chk_airports = QCheckBox("Show Airport Markers")
        self.chk_airports.setChecked(True)
        self.chk_airports.stateChanged.connect(self.emit)
        layout.addWidget(self.chk_airports)

    def emit(self):
        self.settings_changed.emit(
            self.chk_bounds.isChecked(),
            self.chk_trails.isChecked(),
            self.chk_labels.isChecked(),
            self.chk_airports.isChecked()
        )

class WeatherPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PopupPanel")
        self.setVisible(False)
        self.setFixedWidth(300)
        self.setFixedHeight(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(QLabel("ACTIVE ATIS (WEATHER)", objectName="HeaderText"))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

    def update_atis(self, atis_dict):
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget: widget.deleteLater()

        if not atis_dict:
            self.content_layout.addWidget(QLabel("No active ATIS."))
            return

        for icao, data in atis_dict.items():
            lbl = QLabel(f"[{icao}] {data.get('content', 'No Info')}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #ccc; font-family: monospace; font-size: 11px; border-bottom: 1px solid #444; padding-bottom: 5px; margin-top: 5px;")
            self.content_layout.addWidget(lbl)

# ==========================================
# TOOLBAR BAWAH & MAP CONTROLS
# ==========================================
class BottomToolbar(QFrame):
    tool_clicked = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomToolbar")
        self.setFixedHeight(60)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(10)

        buttons = ["Settings", "Weather", "Filters", "Widgets"]
        for text in buttons:
            btn = QPushButton(text)
            btn.setObjectName("ToolBtn")
            btn.clicked.connect(lambda checked, t=text: self.tool_clicked.emit(t))
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
