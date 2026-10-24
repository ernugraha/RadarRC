# frontend/map_items.py

import os
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPolygonF, QBrush, QColor, QPen, QPainterPath
from PySide6.QtSvg import QSvgRenderer

_SVG_CACHE = {}

AIRCRAFT_CATEGORIES = {
    "an225": ["AN-225"],
    "concorde": ["CONCORDE"],
    "four_engine_wing_on_top": [],
    "glider": ["GLIDER"],
    "light_aircraft": ["CESSNA", "CIRRUS", "DIAMOND", "PIPER", "EXTRA 300", "WRIGHT", "CAPRONI"],
    "narrow_body": ["A220", "A320", "707", "727", "737", "757", "COMET", "MD-90"],
    "regional_jet": ["CRJ", "E190", "EMBRAER"],
    "small_private_jet": ["LEARJET"],
    "turboprop": ["ATR", "Q400", "CARAVAN", "TWIN OTTER", "KING AIR", "AN-22"],
    "widebody": ["A330", "A350", "767", "777", "787", "L-1011", "DC-10", "MD-11", "BELUGA"],
    "widebody_four_engine": ["A340", "747", "A380", "DREAMLIFTER"]
}

def load_icons(icons_dir="assets/icons"):

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

class AircraftItem(QGraphicsItem):
    def __init__(self, callsign, aircraft_type=""):
        super().__init__()
        self.callsign = callsign
        self.aircraft_type = aircraft_type
        self.heading = 0

        # Visual size (piksel layar)
        self.icon_size = 20  # Ukuran SVG
        self.arrow_size = 8  # Ukuran panah default

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

    def boundingRect(self):
        # KUNCI PERBAIKAN: Perbesar kotak batas (30x30)
        # agar saat pesawat berputar, ujung sayapnya tetap masuk ke dalam kotak
        return QRectF(-15, -15, 30, 30)

    def shape(self):
        # KUNCI PERBAIKAN: Gunakan bentuk lingkaran sebagai area klik
        # Ini membuat pesawat sangat mudah diklik (radius 15 pixel dari tengah)
        path = QPainterPath()
        path.addEllipse(QRectF(-15, -15, 30, 30))
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Jika pesawat sedang dipilih, kita beri sedikit efek redup di belakangnya
        if self.isSelected():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 40))) # Sangat transparan
            painter.drawEllipse(-12, -12, 24, 24)

        icon_name = get_icon_for_aircraft(self.aircraft_type)
        renderer = _SVG_CACHE.get(icon_name) if icon_name else None

        if renderer:
            target_rect = QRectF(-self.icon_size/2, -self.icon_size/2, self.icon_size, self.icon_size)
            renderer.render(painter, target_rect)
        else:
            # Panah Default (Militer/Heli)
            painter.setBrush(QBrush(QColor("#f4b400")))
            painter.setPen(QPen(QColor("#000000"), 1))

            s = self.arrow_size
            polygon = QPolygonF([
                QPointF(0, -s * 1.2),
                QPointF(s * 0.8, s * 1.0),
                QPointF(0, s * 0.6),
                QPointF(-s * 0.8, s * 1.0)
            ])
            painter.drawPolygon(polygon)
