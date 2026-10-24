# frontend/main_window.py

import os
import time
from PySide6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QFrame, QGraphicsOpacityEffect
from PySide6.QtGui import QColor, QPen, QPixmap, QTransform
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer

from frontend.styles import MAIN_STYLESHEET
from frontend.ui_components import (TopBar, Sidebar, BottomToolbar, MapControls,
                                    FlightInfoPanel, FilterPanel, SettingsPanel, WeatherPanel)
from frontend.map_items import AircraftItem, load_icons, TrailItem
from frontend.map_view import MapView
from frontend.airlines import get_airline_icao
from frontend.trail_manager import TrailManager
from PySide6.QtSvgWidgets import QGraphicsSvgItem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RadarRC")
        self.resize(1400, 900)
        self.setStyleSheet(MAIN_STYLESHEET)

        # KUNCI PERBAIKAN: Memuat dari folder 'planes'
        load_icons("assets/planes")

        self.aircraft_items = {}
        self.current_data = {}
        self.current_atis_data = {}
        self.last_sidebar_update = 0

        self.trail_manager = TrailManager(max_points=10000)
        self.current_trail_item = None
        self.follow_callsign = None

        # State Variables
        self.filter_hide_ground = False
        self.filter_min_alt = 0
        self.filter_hide_heli = False
        self.show_boundaries = True
        self.show_trails = True
        self.show_all_labels = False
        self.sidebar_visible = True
        self.active_popup = None

        # Inisialisasi Peta
        self.scene = QGraphicsScene()
        self.view = MapView(self.scene, self)
        self.view.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(self.view)

        self.setup_map()

        # Hubungkan sinyal interaksi manual peta
        self.view.user_panned.connect(self.stop_following)

        # Inisialisasi UI
        self.top_bar = TopBar(self.view)
        self.sidebar = Sidebar(self.view)
        self.info_panel = FlightInfoPanel(self.view)
        self.map_controls = MapControls(self.view, self.view)
        self.bottom_toolbar = BottomToolbar(self.view)

        # Panel Popup
        self.filter_panel = FilterPanel(self.view)
        self.settings_panel = SettingsPanel(self.view)
        self.weather_panel = WeatherPanel(self.view)

        # Koneksi Sinyal
        self.info_panel.closed.connect(self.close_flight_panel)
        self.scene.selectionChanged.connect(self.on_aircraft_selected)
        self.sidebar.flight_clicked.connect(self.focus_on_aircraft)
        self.top_bar.search_triggered.connect(self.perform_search)

        self.bottom_toolbar.tool_clicked.connect(self.on_tool_clicked)
        self.filter_panel.filters_changed.connect(self.apply_filters)
        self.settings_panel.settings_changed.connect(self.apply_settings)

        # Animasi Sidebar & Info Panel
        self.sidebar_anim = QPropertyAnimation(self.sidebar, b"geometry")
        self.sidebar_anim.setDuration(300)
        self.sidebar_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.info_anim = QPropertyAnimation(self.info_panel, b"geometry")
        self.info_anim.setDuration(300)
        self.info_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.resizeEvent(None)
        self.sidebar.show()
        self.info_panel.hide()

    def stop_following(self):
        self.follow_callsign = None

    def on_tool_clicked(self, tool_name):
        if self.active_popup == tool_name:
            self.hide_active_popup()
            self.active_popup = None
            return

        self.hide_active_popup()

        if tool_name == "Filters":
            self.show_popup(self.filter_panel)
        elif tool_name == "Settings":
            self.show_popup(self.settings_panel)
        elif tool_name == "Weather":
            self.weather_panel.update_atis(self.current_atis_data)
            self.show_popup(self.weather_panel)
        elif tool_name == "Widgets":
            if self.info_panel.isVisible() and self.info_panel.geometry().x() == 20:
                self.scene.clearSelection()
            else:
                self.sidebar_visible = not self.sidebar_visible
                self.update_sidebar_animation()
            return

        self.active_popup = tool_name

    def hide_active_popup(self):
        for p in [self.filter_panel, self.settings_panel, self.weather_panel]:
            if hasattr(p, 'anim_opacity'): p.anim_opacity.stop()
            if hasattr(p, 'anim_geom'): p.anim_geom.stop()
            p.setVisible(False)

    def show_popup(self, panel):
        panel.setVisible(True)
        opacity_effect = QGraphicsOpacityEffect(panel)
        panel.setGraphicsEffect(opacity_effect)

        panel.anim_opacity = QPropertyAnimation(opacity_effect, b"opacity")
        panel.anim_opacity.setDuration(200)
        panel.anim_opacity.setStartValue(0.0)
        panel.anim_opacity.setEndValue(1.0)

        w = self.width()
        h = self.height()
        tb_w = 400
        tb_x = (w - tb_w) // 2
        tb_y = h - 90

        popup_w = panel.width() if panel.width() > 0 else 280
        popup_h = panel.height() if panel.height() > 0 else 180

        end_rect = QRect(tb_x + (tb_w - popup_w)//2, tb_y - popup_h - 10, popup_w, popup_h)
        start_rect = QRect(end_rect.x(), end_rect.y() + 15, end_rect.width(), end_rect.height())

        panel.anim_geom = QPropertyAnimation(panel, b"geometry")
        panel.anim_geom.setDuration(200)
        panel.anim_geom.setEasingCurve(QEasingCurve.OutCubic)
        panel.anim_geom.setStartValue(start_rect)
        panel.anim_geom.setEndValue(end_rect)

        panel.anim_opacity.start()
        panel.anim_geom.start()

    def update_sidebar_animation(self):
        panel_height = min(750, self.height() - 120)
        self.sidebar_anim.stop()
        self.sidebar_anim.setStartValue(self.sidebar.geometry())

        if self.sidebar_visible:
            self.sidebar_anim.setEndValue(QRect(20, 100, 340, panel_height))
        else:
            self.sidebar_anim.setEndValue(QRect(-360, 100, 340, panel_height))

        self.sidebar_anim.start()

    def apply_filters(self, hide_ground, min_alt, hide_heli):
        self.filter_hide_ground = hide_ground
        self.filter_min_alt = min_alt
        self.filter_hide_heli = hide_heli

    def apply_settings(self, show_bounds, show_trails, show_labels):
        self.show_boundaries = show_bounds
        self.show_trails = show_trails
        self.show_all_labels = show_labels

        if hasattr(self, 'boundaries_item'):
            self.boundaries_item.setVisible(self.show_boundaries)

        for plane in self.aircraft_items.values():
            plane.always_show_label = self.show_all_labels
            plane.update()

    def update_atis(self, atis_dict):
        self.current_atis_data = atis_dict
        if self.weather_panel.isVisible():
            self.weather_panel.update_atis(atis_dict)

    def resizeEvent(self, event):
        w = self.width()
        h = self.height()
        self.top_bar.setGeometry(0, 0, w, 80)
        panel_height = min(750, h - 120)

        if self.sidebar_visible:
            self.sidebar.setGeometry(20, 100, 340, panel_height)
        else:
            self.sidebar.setGeometry(-360, 100, 340, panel_height)

        self.info_panel.setGeometry(-360, 100, 340, panel_height)
        self.map_controls.setGeometry(w - 60, h // 2 - 50, 40, 100)

        tb_w = 400
        tb_x = (w - tb_w) // 2
        tb_y = h - 90
        self.bottom_toolbar.setGeometry(tb_x, tb_y, tb_w, 60)

    def setup_map(self):
        self.scene.setBackgroundBrush(QColor("#131313"))
        map_path = "assets/maps/full_map_small.png"
        if os.path.exists(map_path):
            pixmap = QPixmap(map_path)
            self.map_item = QGraphicsPixmapItem(pixmap)
            self.map_item.setZValue(-2)
            self.map_item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
            self.scene.addItem(self.map_item)
            transform = QTransform()
            transform.scale(0.2812, 0.2812)
            self.map_item.setTransform(transform)
            self.map_item.setPos(-587.3, -553.0)

        boundaries_path = "assets/maps/boundaries.svg"
        if os.path.exists(boundaries_path):
            self.boundaries_item = QGraphicsSvgItem(boundaries_path)
            self.boundaries_item.setZValue(-1.5)
            self.boundaries_item.setOpacity(0.3)
            self.scene.addItem(self.boundaries_item)

        self.scene.setSceneRect(-10000, -10000, 20000, 20000)
        self.view.centerOn(0, 0)
        self.view.scale(0.5, 0.5)

    def perform_search(self, query):
        query = query.lower()
        matched = None
        for callsign, info in self.current_data.items():
            if query in callsign.lower() or query in f"{get_airline_icao(callsign)}{callsign.split('-')[-1]}".lower() or query in info.get("aircraftType", "").lower():
                matched = callsign
                break
        if matched:
            self.focus_on_aircraft(matched)
            self.top_bar.search_bar.clear()
        else:
            self.top_bar.search_bar.setPlaceholderText("Flight not found. Try again...")

    def focus_on_aircraft(self, callsign):
        if callsign in self.aircraft_items:
            item = self.aircraft_items[callsign]
            self.scene.clearSelection()
            item.setSelected(True)

            self.follow_callsign = callsign
            current_zoom = self.view.transform().m11()

            if current_zoom < 2.0:
                self.view.scale(2.0 / current_zoom, 2.0 / current_zoom)

            self.view.smooth_center_on(item.pos())

    def close_flight_panel(self):
        self.scene.clearSelection()

    def animate_panels(self, show_info):
        self.sidebar_anim.stop()
        self.info_anim.stop()
        panel_height = min(750, self.height() - 120)

        if show_info:
            self.info_panel.show()
            self.sidebar_anim.setStartValue(self.sidebar.geometry())
            self.sidebar_anim.setEndValue(QRect(-360, 100, 340, panel_height))

            self.info_anim.setStartValue(self.info_panel.geometry())
            self.info_anim.setEndValue(QRect(20, 100, 340, panel_height))

            self.sidebar_anim.start()
            self.info_anim.start()
        else:
            self.sidebar_anim.setStartValue(self.sidebar.geometry())
            if self.sidebar_visible:
                self.sidebar_anim.setEndValue(QRect(20, 100, 340, panel_height))
            else:
                self.sidebar_anim.setEndValue(QRect(-360, 100, 340, panel_height))

            self.info_anim.setStartValue(self.info_panel.geometry())
            self.info_anim.setEndValue(QRect(-360, 100, 340, panel_height))

            self.sidebar_anim.start()
            self.info_anim.start()

            QTimer.singleShot(300, self.check_hide_info_panel)

    def check_hide_info_panel(self):
        if self.info_panel.geometry().x() <= -360:
            self.info_panel.hide()

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

                    self.follow_callsign = callsign

                    trail_points = self.trail_manager.get_trail(callsign)
                    if len(trail_points) > 1 and self.show_trails:
                        self.current_trail_item = TrailItem()
                        self.current_trail_item.set_points(trail_points)
                        self.scene.addItem(self.current_trail_item)
        else:
            self.follow_callsign = None
            self.animate_panels(show_info=False)

    def update_aircraft(self, data_dict):
        filtered_data = {}
        for callsign, info in data_dict.items():
            if self.filter_hide_ground and info.get("isOnGround", False): continue
            if info.get("altitude", 0) < self.filter_min_alt: continue
            if self.filter_hide_heli and info.get("aircraftType", "").upper().startswith("H"): continue
            filtered_data[callsign] = info

        self.current_data = filtered_data
        active_callsigns = set(filtered_data.keys())

        for callsign, info in filtered_data.items():
            if "x" not in info or "y" not in info: continue
            x, y = info["x"], info["y"]
            heading = info.get("heading", 0)
            alt = info.get("altitude", 0)
            ac_type = info.get("aircraftType", "")

            icao = get_airline_icao(callsign)
            flight_num = callsign.split("-")[-1] if "-" in callsign else ""
            label_text = f"{icao}{flight_num}" if icao != "???" else callsign

            if callsign not in self.aircraft_items:
                plane = AircraftItem(callsign, ac_type)
                plane.always_show_label = self.show_all_labels
                self.scene.addItem(plane)
                self.aircraft_items[callsign] = plane

            self.aircraft_items[callsign].update_data(x, y, heading, ac_type, label_text)
            self.trail_manager.add_point(callsign, x, y, alt)

        if self.follow_callsign and self.follow_callsign in self.aircraft_items:
            item = self.aircraft_items[self.follow_callsign]
            self.view.centerOn(item.pos())

        for callsign in list(self.aircraft_items.keys()):
            if callsign not in active_callsigns:
                item = self.aircraft_items.pop(callsign)
                self.scene.removeItem(item)

        self.trail_manager.sync_to_db()
        self.trail_manager.cleanup(active_callsigns)

        selected_items = self.scene.selectedItems()
        selected_callsign = selected_items[0].callsign if (selected_items and isinstance(selected_items[0], AircraftItem)) else None

        if selected_callsign:
            if selected_callsign not in active_callsigns:
                self.scene.clearSelection()
                if self.current_trail_item:
                    self.scene.removeItem(self.current_trail_item)
                    self.current_trail_item = None
            elif self.current_trail_item and self.show_trails:
                trail_points = self.trail_manager.get_trail(selected_callsign)
                self.current_trail_item.set_points(trail_points)

        now = time.time()
        if now - self.last_sidebar_update > 1.0:
            self.sidebar.update_data(filtered_data)
            self.last_sidebar_update = now
