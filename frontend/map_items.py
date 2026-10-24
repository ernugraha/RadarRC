# frontend/map_items.py

import os
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QPolygonF, QBrush, QColor, QPen, QPainterPath, QFont
from PySide6.QtSvg import QSvgRenderer

_SVG_CACHE = {}

def load_icons(icons_dir="assets/planes"):
    if not os.path.exists(icons_dir): return
    for filename in os.listdir(icons_dir):
        if filename.endswith(".svg"):
            name = filename[:-4].lower()
            renderer = QSvgRenderer(os.path.join(icons_dir, filename))
            if renderer.isValid(): _SVG_CACHE[name] = renderer

AIRCRAFT_MAPPING = {
    "b737": "b737", "737": "b737", "b738": "b737", "b739": "b737", "b38m": "b737", "b39m": "b737",
    "b747": "b747", "747": "b747", "b741": "b747", "b742": "b747", "b743": "b747", "b744": "b747", "b748": "b747",
    "b757": "b757", "757": "b757", "b767": "b767", "767": "b767",
    "b777": "b777", "777": "b777", "b772": "b777", "b773": "b777", "b77w": "b777", "b778": "b777", "b779": "b777",
    "b787": "b787", "787": "b787", "b788": "b787", "b789": "b787", "b78x": "b787", "b707": "b707", "707": "b707",
    "a320": "a320", "320": "a320", "a319": "a320", "a321": "a320", "a20n": "a320", "a21n": "a320",
    "a330": "a330", "330": "a330", "a332": "a330", "a333": "a330", "a338": "a330", "a339": "a330",
    "a340": "a340", "340": "a340", "a342": "a340", "a343": "a340", "a345": "a340", "a346": "a340",
    "a350": "a350", "350": "a350", "a359": "a350", "a35k": "a350", "a380": "a380", "380": "a380", "a388": "a380",
    "a220": "a220", "220": "a220", "bcs3": "a220", "an225": "an225", "225": "an225", "cncd": "cncd", "concorde": "cncd",
    "crj": "crj700", "crj7": "crj700", "crj9": "crj700", "e190": "e190", "e195": "e190", "e175": "e190", "e170": "e190",
    "atr": "atr72", "at72": "atr72", "at76": "atr72", "atr72": "atr72", "dh8d": "dh8d", "q400": "dh8d", "dhc6": "dhc6",
    "c208": "c172", "c172": "c172", "c182": "c172", "da42": "da42", "da40": "da42", "da62": "da42",
    "md11": "md11", "dc10": "dc10", "lj45": "lj45", "c17": "c17", "a400": "c17", "c5m": "c17", "e3": "e3", "p8": "p8",
    "f16": "f16", "f15": "f15", "f18": "f18h", "f22": "f22", "f35": "f35", "f4": "f4e", "a10": "a10", "b1": "b1",
    "eurofighter": "eurofighter", "typhoon": "eurofighter", "h135": "chopper", "h145": "chopper", "uh60": "chopper",
    "ch47": "chopper", "chopper": "chopper", "helicopter": "chopper"
}

def get_icon_for_aircraft(ac_type):
    if not ac_type: return None
    ac_lower = ac_type.lower().replace(" ", "").replace("-", "")
    if ac_lower in _SVG_CACHE: return ac_lower
    if ac_lower in AIRCRAFT_MAPPING:
        mapped_name = AIRCRAFT_MAPPING[ac_lower]
        if mapped_name in _SVG_CACHE: return mapped_name
    for key, mapped_name in AIRCRAFT_MAPPING.items():
        if key in ac_lower and mapped_name in _SVG_CACHE: return mapped_name
    if "heli" in ac_lower or "chopper" in ac_lower:
        if "chopper" in _SVG_CACHE: return "chopper"
    return None

class AircraftItem(QGraphicsItem):
    def __init__(self, callsign, aircraft_type=""):
        super().__init__()
        self.callsign = callsign
        self.aircraft_type = aircraft_type
        self.heading = 0
        self.size = 8
        self.icon_size = 24
        self.is_hovered = False
        self.always_show_label = False
        self.label_text = callsign.split("-")[0] if "-" in callsign else callsign
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(0, 0)

        # KUNCI: Timer untuk kedipan emergency
        self.is_emergency = False
        self.flash_state = False
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.toggle_flash)

    def toggle_flash(self):
        self.flash_state = not self.flash_state
        self.update()

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def update_data(self, x, y, heading, aircraft_type="", label_text="", is_emergency=False):
        self.setPos(x / 100.0, y / 100.0)
        if aircraft_type and self.aircraft_type != aircraft_type: self.aircraft_type = aircraft_type
        if label_text: self.label_text = label_text
        if self.heading != heading:
            self.heading = heading
            self.setRotation(self.heading)

        # KUNCI: Atur timer kedipan
        if self.is_emergency != is_emergency:
            self.is_emergency = is_emergency
            if self.is_emergency:
                self.flash_timer.start(400) # Kedip setiap 0.4 detik
            else:
                self.flash_timer.stop()
                self.flash_state = False
                self.update()

    def boundingRect(self): return QRectF(-150, -150, 300, 300)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(QRectF(-15, -15, 30, 30))
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Warna normal vs emergency
        if self.is_emergency:
            color = QColor("#ff0000") if self.flash_state else QColor("#f4b400") # Merah / Kuning
        else:
            color = QColor("#f4b400")

        if self.isSelected():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
            painter.drawEllipse(-12, -12, 24, 24)

        # Jika emergency, gambar lingkaran berkedip di belakang ikon
        if self.is_emergency:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(-self.icon_size, -self.icon_size, self.icon_size*2, self.icon_size*2)

        icon_name = get_icon_for_aircraft(self.aircraft_type)
        renderer = _SVG_CACHE.get(icon_name) if icon_name else None

        if renderer:
            target_rect = QRectF(-self.icon_size/2, -self.icon_size/2, self.icon_size, self.icon_size)
            renderer.render(painter, target_rect)
        else:
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#000000"), 1))
            s = self.size
            painter.drawPolygon(QPolygonF([
                QPointF(0, -s * 1.2), QPointF(s * 0.8, s * 1.0),
                QPointF(0, s * 0.6), QPointF(-s * 0.8, s * 1.0)
            ]))

        if self.isSelected() or self.is_hovered or self.always_show_label:
            painter.save()
            painter.rotate(-self.heading)
            font = QFont("Arial", 8, QFont.Bold)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(self.label_text) + 8
            text_height = metrics.height() + 2
            label_rect = QRectF(12, -text_height / 2, text_width, text_height)
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
            painter.drawRoundedRect(label_rect, 3, 3)
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(label_rect, Qt.AlignCenter, self.label_text)
            painter.restore()

# ... (Sisa class AirportItem dan TrailItem biarkan sama seperti sebelumnya) ...
class AirportItem(QGraphicsItem):
    def __init__(self, icao, name):
        super().__init__()
        self.icao = icao
        self.name = name
        self.size = 14
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setZValue(0.5)

    def boundingRect(self): return QRectF(-self.size, -self.size, self.size * 2, self.size * 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#1d4ed8")))
        painter.setPen(QPen(Qt.white, 2))
        painter.drawEllipse(-self.size/2, -self.size/2, self.size, self.size)
        painter.setPen(QPen(Qt.white))
        font = QFont("Arial", 8, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(-self.size/2, -self.size/2, self.size, self.size), Qt.AlignCenter, "T")
        if self.isSelected():
            painter.setPen(QPen(QColor("#f4b400"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(-self.size/2 - 2, -self.size/2 - 2, self.size + 4, self.size + 4)

class TrailItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.setZValue(-0.5)
        self.trail_points = []

    def set_points(self, points):
        if len(points) < 3:
            self.trail_points = points
            self.update()
            return
        pts = points
        for _ in range(2):
            new_pts = [pts[0]]
            for i in range(len(pts) - 1):
                p0, p1 = pts[i], pts[i+1]
                new_pts.append({"x": p0["x"]*0.75 + p1["x"]*0.25, "y": p0["y"]*0.75 + p1["y"]*0.25, "alt": p0["alt"]*0.75 + p1["alt"]*0.25})
                new_pts.append({"x": p0["x"]*0.25 + p1["x"]*0.75, "y": p0["y"]*0.25 + p1["y"]*0.75, "alt": p0["alt"]*0.25 + p1["alt"]*0.75})
            new_pts.append(pts[-1])
            pts = new_pts
        self.trail_points = pts
        self.update()

    def boundingRect(self):
        if not self.trail_points: return QRectF()
        return QRectF(min(p["x"] for p in self.trail_points)/100-20, min(p["y"] for p in self.trail_points)/100-20, (max(p["x"] for p in self.trail_points)-min(p["x"] for p in self.trail_points))/100+40, (max(p["y"] for p in self.trail_points)-min(p["y"] for p in self.trail_points))/100+40)

    def paint(self, painter, option, widget=None):
        if len(self.trail_points) < 2: return
        painter.setRenderHint(QPainter.Antialiasing)

        line_width = 4.0

        for i in range(1, len(self.trail_points)):
            p1, p2 = self.trail_points[i-1], self.trail_points[i]
            color = self._get_smooth_color((p1["alt"] + p2["alt"]) / 2.0)

            pen = QPen(color)
            pen.setWidthF(line_width)
            pen.setCosmetic(True)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

            painter.drawLine(QPointF(p1["x"]/100, p1["y"]/100), QPointF(p2["x"]/100, p2["y"]/100))

    def _get_smooth_color(self, alt):
        keys = [(0,255,255,255), (1000,244,180,0), (2500,76,175,80), (4000,0,188,212), (5500,33,150,243), (7000,156,39,176), (9000,244,67,54)]
        if alt <= 0: return QColor(255,255,255)
        if alt >= 9000: return QColor(244,67,54)
        for i in range(len(keys) - 1):
            a1, r1, g1, b1 = keys[i]
            a2, r2, g2, b2 = keys[i+1]
            if a1 <= alt <= a2:
                rat = (alt - a1) / (a2 - a1)
                return QColor(int(r1+(r2-r1)*rat), int(g1+(g2-g1)*rat), int(b1+(b2-b1)*rat))
        return QColor(255,255,255)
