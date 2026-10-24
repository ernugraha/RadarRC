# frontend/map_items.py

import os
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPolygonF, QBrush, QColor, QPen, QPainterPath
from PySide6.QtSvg import QSvgRenderer

_SVG_CACHE = {}

AIRCRAFT_CATEGORIES = {
    "an225": ["AN-225", "A225"],
    "concorde": ["CONCORDE", "CONC"],
    "four_engine_wing_on_top": ["DREAMLIFTER", "BLCF", "A124", "C5M", "A400"],
    "glider": ["GLIDER", "GLID"],
    "light_aircraft": ["CESSNA", "C172", "C182", "C208", "C402", "SR22", "DA40", "DA62", "PA28", "P28A", "P28B", "BE20", "BE9L", "BE30", "TBM", "PC12", "EXTRA", "E300", "WRIGHT", "CAPRONI"],
    "narrow_body": ["A220", "A318", "A319", "A320", "A321", "B707", "B717", "B727", "B737", "B738", "B739", "B38M", "B39M", "B752", "B753", "MD80", "MD90", "MD95", "COMET"],
    "regional_jet": ["CRJ", "E170", "E175", "E190", "E195", "E290", "E295"],
    "small_private_jet": ["LEARJET", "LJ", "CITATION", "C525", "C560", "C680", "C750", "GLF", "GLEX", "FA", "F900", "FALCON", "GLOBAL"],
    "turboprop": ["ATR", "AT72", "AT75", "AT76", "Q400", "DH8D", "DHC6", "C208", "BE20", "BE9L", "BE30", "AN-22", "AN-24", "AN-26", "AN-32"],
    "widebody": ["A330", "A332", "A333", "A338", "A339", "A350", "A359", "A35K", "B767", "B762", "B763", "B764", "B777", "B772", "B773", "B77W", "B778", "B779", "B787", "B788", "B789", "B78X", "L-1011", "DC-10", "MD-11", "BELUGA", "A306", "A310"],
    "widebody_four_engine": ["A340", "A342", "A343", "A345", "A346", "B747", "B741", "B742", "B743", "B744", "B748", "A380", "A388"]
}

def load_icons(icons_dir="assets/icons"):
    if not os.path.exists(icons_dir):
        return

    for filename in os.listdir(icons_dir):
        if filename.endswith(".svg"):
            name = filename[:-4]
            path = os.path.join(icons_dir, filename)
            renderer = QSvgRenderer(path)
            if renderer.isValid():
                _SVG_CACHE[name] = renderer

def get_icon_for_aircraft(ac_type):
    if not ac_type: return None
    ac_type_upper = ac_type.upper()

    for icon_name, keywords in AIRCRAFT_CATEGORIES.items():
        for kw in keywords:
            if kw in ac_type_upper:
                return icon_name
    return None

# ==========================================
# CLASS PESAWAT (UKURAN LEBIH KECIL)
# ==========================================
class AircraftItem(QGraphicsItem):
    def __init__(self, callsign, aircraft_type=""):
        super().__init__()
        self.callsign = callsign
        self.aircraft_type = aircraft_type
        self.heading = 0

        # UKURAN DIPERKECIL LAGI
        self.size = 4       # Panah default
        self.icon_size = 10 # Ikon SVG (turun dari 14)

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setTransformOriginPoint(0, 0)

    def update_data(self, x, y, heading, aircraft_type=""):
        self.setPos(x / 100.0, y / 100.0)
        if aircraft_type and self.aircraft_type != aircraft_type:
            self.aircraft_type = aircraft_type
        if self.heading != heading:
            self.heading = heading
            self.setRotation(self.heading)

    def boundingRect(self):
        # Hitbox disesuaikan dengan ukuran baru
        return QRectF(-10, -10, 20, 20)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(QRectF(-10, -10, 20, 20))
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.isSelected():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
            painter.drawEllipse(-8, -8, 16, 16)

        icon_name = get_icon_for_aircraft(self.aircraft_type)
        renderer = _SVG_CACHE.get(icon_name) if icon_name else None

        if renderer:
            target_rect = QRectF(-self.icon_size/2, -self.icon_size/2, self.icon_size, self.icon_size)
            renderer.render(painter, target_rect)
        else:
            painter.setBrush(QBrush(QColor("#f4b400")))
            painter.setPen(QPen(QColor("#000000"), 1))
            s = self.size
            polygon = QPolygonF([
                QPointF(0, -s * 1.2),
                QPointF(s * 0.8, s * 1.0),
                QPointF(0, s * 0.6),
                QPointF(-s * 0.8, s * 1.0)
            ])
            painter.drawPolygon(polygon)

# ==========================================
# CLASS TRAIL (DENGAN EFEK GRADASI)
# ==========================================
class TrailItem(QGraphicsItem):
    def __init__(self):
        super().__init__()
        self.setZValue(-0.5)
        self.trail_points = []

    def set_points(self, points):
        self.trail_points = points
        self.update()

    def boundingRect(self):
        if not self.trail_points: return QRectF()
        min_x = min(p["x"] for p in self.trail_points) / 100.0
        max_x = max(p["x"] for p in self.trail_points) / 100.0
        min_y = min(p["y"] for p in self.trail_points) / 100.0
        max_y = max(p["y"] for p in self.trail_points) / 100.0
        return QRectF(min_x - 10, min_y - 10, (max_x - min_x) + 20, (max_y - min_y) + 20)

    def paint(self, painter, option, widget=None):
        if len(self.trail_points) < 2: return
        painter.setRenderHint(QPainter.Antialiasing)

        total_points = len(self.trail_points)

        for i in range(1, total_points):
            p1 = self.trail_points[i-1]
            p2 = self.trail_points[i]

            # 1. Ambil warna berdasarkan ketinggian
            alt = p2["alt"]
            color = self._get_altitude_color(alt)

            # 2. EFEK GRADASI: Hitung transparansi (alpha) dari ekor ke kepala
            # Titik terbaru (i = total) alpha 255, titik terlama alpha 0
            progress = i / total_points
            alpha = int(progress * 255)
            color.setAlpha(alpha)

            pen = QPen(color)
            pen.setWidth(2.5) # Sedikit lebih tebal untuk efek gradasi
            pen.setCosmetic(True)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

            painter.drawLine(
                QPointF(p1["x"] / 100.0, p1["y"] / 100.0),
                QPointF(p2["x"] / 100.0, p2["y"] / 100.0)
            )

    def _get_altitude_color(self, alt):
        if alt < 300: return QColor(255, 255, 255)         # Putih
        elif alt < 1500: return QColor(244, 180, 0)        # Kuning
        elif alt < 3000: return QColor(76, 175, 80)        # Hijau
        elif alt < 4500: return QColor(0, 188, 212)        # Biru Muda
        elif alt < 6000: return QColor(33, 150, 243)       # Biru Tua
        elif alt < 7000: return QColor(156, 39, 176)       # Ungu
        else: return QColor(244, 67, 54)                   # Merah
