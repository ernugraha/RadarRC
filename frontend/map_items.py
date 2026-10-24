# frontend/map_items.py

import os
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPolygonF, QBrush, QColor, QPen, QPainterPath
from PySide6.QtSvg import QSvgRenderer

_SVG_CACHE = {}

AIRCRAFT_CATEGORIES = {
    "an225": ["AN-225", "A225"], "concorde": ["CONCORDE", "CONC"],
    "four_engine_wing_on_top": ["DREAMLIFTER", "BLCF", "A124", "C-17", "C17"],
    "glider": ["GLIDER", "GLID"],
    "light_aircraft": ["CESSNA", "C172", "C182", "C208", "C402", "SR22", "DA40", "DA50", "DA62", "PA28", "P28A", "P28B", "TBM", "PC12", "EXTRA", "E300", "WRIGHT", "CAPRONI", "PIPER", "CUB"],
    "narrow_body": ["A220", "A318", "A319", "A320", "A321", "707", "B707", "717", "B717", "727", "B727", "737", "B737", "B738", "B739", "B38M", "B39M", "757", "B752", "B753", "MD80", "MD90", "MD95", "COMET"],
    "regional_jet": ["CRJ", "E170", "E175", "E190", "E195", "E290", "E295", "EMBRAER"],
    "small_private_jet": ["LEARJET", "LJ", "CITATION", "C525", "C560", "C680", "C750", "GLF", "GLEX", "FA", "F900", "FALCON", "GLOBAL"],
    "turboprop": ["ATR", "AT72", "AT75", "AT76", "Q400", "DH8D", "DHC6", "CARAVAN", "TWIN OTTER", "KINGAIR", "KING AIR", "BE20", "BE9L", "BE30", "B200", "B300", "B350", "AN-22", "AN-24", "AN-26", "AN-32"],
    "widebody": ["A330", "A332", "A333", "A338", "A339", "A350", "A359", "A35K", "767", "B762", "B763", "B764", "777", "B772", "B773", "B77W", "B778", "B779", "787", "B788", "B789", "B78X", "L-1011", "DC-10", "MD-11", "BELUGA", "A306", "A310"],
    "widebody_four_engine": ["A340", "A342", "A343", "A345", "A346", "747", "B741", "B742", "B743", "B744", "B748", "A380", "A388"]
}

def load_icons(icons_dir="assets/icons"):
    if not os.path.exists(icons_dir): return
    for filename in os.listdir(icons_dir):
        if filename.endswith(".svg"):
            name = filename[:-4]
            renderer = QSvgRenderer(os.path.join(icons_dir, filename))
            if renderer.isValid(): _SVG_CACHE[name] = renderer

def get_icon_for_aircraft(ac_type):
    if not ac_type: return None
    ac_type_upper = ac_type.upper().replace(" ", "")
    for icon_name, keywords in AIRCRAFT_CATEGORIES.items():
        for kw in keywords:
            if kw.replace(" ", "") in ac_type_upper: return icon_name
    return None

class AircraftItem(QGraphicsItem):
    def __init__(self, callsign, aircraft_type=""):
        super().__init__()
        self.callsign = callsign
        self.aircraft_type = aircraft_type
        self.heading = 0
        self.size = 8
        self.icon_size = 20
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setTransformOriginPoint(0, 0)

    def update_data(self, x, y, heading, aircraft_type=""):
        self.setPos(x / 100.0, y / 100.0)
        if aircraft_type and self.aircraft_type != aircraft_type:
            self.aircraft_type = aircraft_type
        if self.heading != heading:
            self.heading = heading
            self.setRotation(self.heading)

    def boundingRect(self): return QRectF(-15, -15, 30, 30)
    def shape(self):
        path = QPainterPath()
        path.addEllipse(QRectF(-15, -15, 30, 30))
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.isSelected():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
            painter.drawEllipse(-12, -12, 24, 24)

        icon_name = get_icon_for_aircraft(self.aircraft_type)
        renderer = _SVG_CACHE.get(icon_name) if icon_name else None

        if renderer:
            target_rect = QRectF(-self.icon_size/2, -self.icon_size/2, self.icon_size, self.icon_size)
            renderer.render(painter, target_rect)
        else:
            painter.setBrush(QBrush(QColor("#f4b400")))
            painter.setPen(QPen(QColor("#000000"), 1))
            s = self.size
            painter.drawPolygon(QPolygonF([
                QPointF(0, -s * 1.2), QPointF(s * 0.8, s * 1.0),
                QPointF(0, s * 0.6), QPointF(-s * 0.8, s * 1.0)
            ]))

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

        # ALGORITMA CHAIKIN (Corner Cutting)
        # Menghaluskan seluruh titik, termasuk data paling lama (ekor)
        pts = points
        for _ in range(2): # Lakukan 2 iterasi agar mulus sempurna
            new_pts = []
            new_pts.append(pts[0]) # Pertahankan titik awal
            for i in range(len(pts) - 1):
                p0 = pts[i]
                p1 = pts[i+1]

                # Rumus Chaikin: 75% titik awal + 25% titik akhir
                q_x = p0["x"] * 0.75 + p1["x"] * 0.25
                q_y = p0["y"] * 0.75 + p1["y"] * 0.25
                q_alt = p0["alt"] * 0.75 + p1["alt"] * 0.25

                # Rumus Chaikin: 25% titik awal + 75% titik akhir
                r_x = p0["x"] * 0.25 + p1["x"] * 0.75
                r_y = p0["y"] * 0.25 + p1["y"] * 0.75
                r_alt = p0["alt"] * 0.25 + p1["alt"] * 0.75

                new_pts.append({"x": q_x, "y": q_y, "alt": q_alt})
                new_pts.append({"x": r_x, "y": r_y, "alt": r_alt})
            new_pts.append(pts[-1]) # Pertahankan titik akhir
            pts = new_pts

        self.trail_points = pts
        self.update()

    def boundingRect(self):
        if not self.trail_points: return QRectF()
        min_x = min(p["x"] for p in self.trail_points) / 100.0
        max_x = max(p["x"] for p in self.trail_points) / 100.0
        min_y = min(p["y"] for p in self.trail_points) / 100.0
        max_y = max(p["y"] for p in self.trail_points) / 100.0
        return QRectF(min_x - 20, min_y - 20, (max_x - min_x) + 40, (max_y - min_y) + 40)

    def paint(self, painter, option, widget=None):
        if len(self.trail_points) < 2: return
        painter.setRenderHint(QPainter.Antialiasing)

        line_width = 3.0

        # Karena titiknya sudah sangat rapat dan halus (dari Chaikin),
        # kita hanya perlu menggambar garis lurus antar titik.
        for i in range(1, len(self.trail_points)):
            p1 = self.trail_points[i-1]
            p2 = self.trail_points[i]

            avg_alt = (p1["alt"] + p2["alt"]) / 2.0
            color = self._get_smooth_color(avg_alt)

            pen = QPen(color)
            pen.setWidthF(line_width)
            pen.setCosmetic(True)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

            pt1 = QPointF(p1["x"] / 100.0, p1["y"] / 100.0)
            pt2 = QPointF(p2["x"] / 100.0, p2["y"] / 100.0)

            painter.drawLine(pt1, pt2)

    def _get_smooth_color(self, alt):
        keys = [
            (0, 255, 255, 255), (1000, 244, 180, 0), (2500, 76, 175, 80),
            (4000, 0, 188, 212), (5500, 33, 150, 243), (7000, 156, 39, 176), (9000, 244, 67, 54)
        ]
        if alt <= 0: return QColor(255, 255, 255)
        if alt >= 9000: return QColor(244, 67, 54)

        for i in range(len(keys) - 1):
            alt1, r1, g1, b1 = keys[i]
            alt2, r2, g2, b2 = keys[i+1]
            if alt1 <= alt <= alt2:
                ratio = (alt - alt1) / (alt2 - alt1)
                return QColor(int(r1 + (r2 - r1) * ratio), int(g1 + (g2 - g1) * ratio), int(b1 + (b2 - b1) * ratio))
        return QColor(255, 255, 255)
