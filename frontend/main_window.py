# frontend/main_window.py

import os
from PySide6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QColor, QPen, QPixmap, QTransform
from PySide6.QtCore import Qt

from frontend.styles import MAIN_STYLESHEET
from frontend.ui_components import TopBar, Sidebar, BottomToolbar, MapControls
from frontend.map_items import AircraftItem
from frontend.map_view import MapView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RadarRC")
        self.resize(1400, 900)
        self.setStyleSheet(MAIN_STYLESHEET)

        self.aircraft_items = {}

        self.scene = QGraphicsScene()
        self.view = MapView(self.scene, self)
        self.setCentralWidget(self.view)

        self.setup_map()

        self.top_bar = TopBar(self.view)
        self.sidebar = Sidebar(self.view)
        self.map_controls = MapControls(self.view, self.view)
        self.bottom_toolbar = BottomToolbar(self.view)

        self.resizeEvent(None)

    def resizeEvent(self, event):
        w = self.width()
        h = self.height()
        self.top_bar.setGeometry(0, 0, w, 80)
        self.sidebar.setGeometry(20, 100, 320, 500)
        # Posisi MapControls disesuaikan karena tombol Edit sudah dihapus
        self.map_controls.setGeometry(w - 60, h // 2 - 50, 40, 100)
        tb_w = 500
        self.bottom_toolbar.setGeometry((w - tb_w)//2, h - 90, tb_w, 60)

    def setup_map(self):
        map_path = "assets/maps/full_map_small.png"

        if not os.path.exists(map_path):
            print(f"[ERROR] File peta tidak ditemukan: {map_path}")
            return

        pixmap = QPixmap(map_path)
        self.map_item = QGraphicsPixmapItem(pixmap)
        self.map_item.setZValue(-2)
        self.map_item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self.scene.addItem(self.map_item)

        # --- NILAI KALIBRASI PETA FINAL ---
        self.map_offset_x = -587.3
        self.map_offset_y = -553.0
        self.map_scale_x = 0.2812
        self.map_scale_y = 0.2812
        # ----------------------------------

        # Terapkan transformasi langsung saat peta dimuat
        transform = QTransform()
        transform.scale(self.map_scale_x, self.map_scale_y)
        self.map_item.setTransform(transform)
        self.map_item.setPos(self.map_offset_x, self.map_offset_y)

        # Garis Bantu Origin (Opsional, hapus komentar jika ingin menyembunyikannya)
        # pen = QPen(QColor(255, 0, 0, 200))
        # pen.setWidth(2)
        # self.scene.addLine(-500, 0, 500, 0, pen)
        # self.scene.addLine(0, -500, 0, 500, pen)

        self.scene.setSceneRect(-10000, -10000, 20000, 20000)
        self.view.centerOn(0, 0)
        self.view.scale(0.5, 0.5)

    def update_aircraft(self, data_dict):
        for callsign, info in data_dict.items():
            if "x" not in info or "y" not in info:
                continue
            x = info["x"]
            y = info["y"]
            heading = info.get("heading", 0)

            if callsign not in self.aircraft_items:
                plane = AircraftItem(callsign)
                self.scene.addItem(plane)
                self.aircraft_items[callsign] = plane

            self.aircraft_items[callsign].update_data(x, y, heading)
