# frontend/main_window.py

import os
import time
from PySide6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QFrame
from PySide6.QtGui import QColor, QPen, QPixmap, QTransform
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve

from frontend.styles import MAIN_STYLESHEET
from frontend.ui_components import TopBar, Sidebar, BottomToolbar, MapControls, FlightInfoPanel
from frontend.map_items import AircraftItem, load_icons, TrailItem
from frontend.map_view import MapView
from frontend.airlines import get_airline_icao
from frontend.trail_manager import TrailManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RadarRC")
        self.resize(1400, 900)
        self.setStyleSheet(MAIN_STYLESHEET)

        load_icons("assets/icons")
        self.aircraft_items = {}
        self.current_data = {}
        self.last_sidebar_update = 0

        self.trail_manager = TrailManager(max_points=10000)
        self.current_trail_item = None

        self.scene = QGraphicsScene()
        self.view = MapView(self.scene, self)
        self.view.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(self.view)

        self.setup_map()

        self.top_bar = TopBar(self.view)
        self.sidebar = Sidebar(self.view)
        self.info_panel = FlightInfoPanel(self.view)
        self.map_controls = MapControls(self.view, self.view)
        self.bottom_toolbar = BottomToolbar(self.view)

        self.info_panel.closed.connect(self.close_flight_panel)
        self.scene.selectionChanged.connect(self.on_aircraft_selected)
        self.sidebar.flight_clicked.connect(self.focus_on_aircraft)
        self.top_bar.search_triggered.connect(self.perform_search)

        self.sidebar_anim = QPropertyAnimation(self.sidebar, b"geometry")
        self.sidebar_anim.setDuration(300)
        self.sidebar_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.info_anim = QPropertyAnimation(self.info_panel, b"geometry")
        self.info_anim.setDuration(300)
        self.info_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.resizeEvent(None)
        self.sidebar.show()
        self.info_panel.hide()

    def perform_search(self, query):
        query = query.lower()
        matched_callsign = None
        for callsign, info in self.current_data.items():
            # Cari berdasarkan Callsign atau ICAO
            if query in callsign.lower() or query in f"{get_airline_icao(callsign)}{callsign.split('-')[-1]}".lower() or query in info.get("aircraftType", "").lower() or query in info.get("playerName", "").lower():
                matched_callsign = callsign
                break

        if matched_callsign:
            self.focus_on_aircraft(matched_callsign)
            self.top_bar.search_bar.clear()
        else:
            self.top_bar.search_bar.setPlaceholderText("Flight not found. Try again...")

    def resizeEvent(self, event):
        w = self.width()
        h = self.height()
        self.top_bar.setGeometry(0, 0, w, 80)
        panel_height = min(650, h - 150)

        self.sidebar.setGeometry(20, 100, 340, panel_height)
        self.info_panel.setGeometry(-360, 100, 340, panel_height)

        self.map_controls.setGeometry(w - 60, h // 2 - 50, 40, 100)
        tb_w = 500
        self.bottom_toolbar.setGeometry((w - tb_w)//2, h - 90, tb_w, 60)

    def setup_map(self):
        self.scene.setBackgroundBrush(QColor("#131313"))
        map_path = "assets/maps/full_map_small.png"
        if not os.path.exists(map_path): return

        pixmap = QPixmap(map_path)
        self.map_item = QGraphicsPixmapItem(pixmap)
        self.map_item.setZValue(-2)
        self.map_item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.scene.addItem(self.map_item)

        self.map_offset_x = -587.3
        self.map_offset_y = -553.0
        self.map_scale_x = 0.2812
        self.map_scale_y = 0.2812

        transform = QTransform()
        transform.scale(self.map_scale_x, self.map_scale_y)
        self.map_item.setTransform(transform)
        self.map_item.setPos(self.map_offset_x, self.map_offset_y)

        self.scene.setSceneRect(-10000, -10000, 20000, 20000)
        self.view.centerOn(0, 0)
        self.view.scale(0.5, 0.5)

    def focus_on_aircraft(self, callsign):
        if callsign in self.aircraft_items:
            item = self.aircraft_items[callsign]
            self.scene.clearSelection()
            item.setSelected(True)
            self.view.centerOn(item)

    def close_flight_panel(self):
        self.scene.clearSelection()

    def animate_panels(self, show_info):
        self.sidebar_anim.stop()
        self.info_anim.stop()
        panel_height = min(650, self.height() - 150)

        if show_info:
            self.info_panel.show()
            self.sidebar_anim.setEndValue(QRect(-360, 100, 340, panel_height))
            self.info_anim.setEndValue(QRect(20, 100, 340, panel_height))
        else:
            self.sidebar_anim.setEndValue(QRect(20, 100, 340, panel_height))
            self.info_anim.setEndValue(QRect(-360, 100, 340, panel_height))

        self.sidebar_anim.start()
        self.info_anim.start()

    def on_aircraft_selected(self):
        selected_items = self.scene.selectedItems()

        if self.current_trail_item:
            self.scene.removeItem(self.current_trail_item)
            self.current_trail_item = None

        if selected_items:
            item = selected_items[0]
            if isinstance(item, AircraftItem):
                callsign = item.callsign
                if callsign in self.current_data:
                    self.info_panel.set_flight_data(callsign, self.current_data[callsign])
                    self.animate_panels(show_info=True)

                    trail_points = self.trail_manager.get_trail(callsign)
                    if len(trail_points) > 1:
                        self.current_trail_item = TrailItem()
                        self.current_trail_item.set_points(trail_points)
                        self.scene.addItem(self.current_trail_item)
        else:
            self.animate_panels(show_info=False)

    def update_aircraft(self, data_dict):
        self.current_data = data_dict
        active_callsigns = set(data_dict.keys())

        # 1. Tambah/Update Pesawat
        for callsign, info in data_dict.items():
            if "x" not in info or "y" not in info: continue
            x, y = info["x"], info["y"]
            heading = info.get("heading", 0)
            alt = info.get("altitude", 0)
            ac_type = info.get("aircraftType", "")

            if callsign not in self.aircraft_items:
                plane = AircraftItem(callsign, ac_type)
                self.scene.addItem(plane)
                self.aircraft_items[callsign] = plane

            self.aircraft_items[callsign].update_data(x, y, heading, ac_type)
            self.trail_manager.add_point(callsign, x, y, alt)

        # 2. Hapus Pesawat Hantu (Yang sudah keluar dari server)
        for callsign in list(self.aircraft_items.keys()):
            if callsign not in active_callsigns:
                item = self.aircraft_items.pop(callsign)
                self.scene.removeItem(item)

        # 3. Sinkronisasi Trail ke Database
        self.trail_manager.sync_to_db()
        self.trail_manager.cleanup(active_callsigns)

        # 4. Perbarui Trail yang sedang aktif dipilih
        selected_items = self.scene.selectedItems()
        if selected_items and isinstance(selected_items[0], AircraftItem):
            selected_cs = selected_items[0].callsign

            # Jika pesawat yang dipilih tiba-tiba hilang
            if selected_cs not in active_callsigns:
                self.scene.clearSelection()
                if self.current_trail_item:
                    self.scene.removeItem(self.current_trail_item)
                    self.current_trail_item = None
            elif self.current_trail_item:
                trail_points = self.trail_manager.get_trail(selected_cs)
                self.current_trail_item.set_points(trail_points)

        # 5. Update Sidebar
        now = time.time()
        if now - self.last_sidebar_update > 1.0:
            self.sidebar.update_data(data_dict)
            self.last_sidebar_update = now
