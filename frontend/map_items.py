# frontend/map_items.py

import os
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPolygonF, QBrush, QColor, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Cache global untuk menyimpan gambar ikon agar tidak lag
_ICON_CACHE = {}

# Pemetaan Tipe Pesawat ke Nama File SVG
AIRCRAFT_CATEGORIES = {
    "an225": ["AN-225"],
    "concorde": ["CONCORDE"],
    "four_engine_wing_on_top": ["747", "A380", "BELUGA", "DREAMLIFTER"],
    "glider": ["GLIDER"],
    "light_aircraft": ["CESSNA", "CIRRUS", "DIAMOND", "PIPER", "EXTRA 300", "WRIGHT", "CAPRONI"],
    "narrow_body": ["A220", "A320", "707", "727", "737", "757", "COMET", "MD-90"],
    "regional_jet": ["CRJ", "E190", "EMBRAER"],
    "small_private_jet": ["LEARJET"],
    "turboprop": ["ATR", "Q400", "CARAVAN", "TWIN OTTER", "KING AIR", "AN-22"],
    "widebody": ["A330", "A350", "767", "777", "787", "L-1011", "DC-10", "MD-11"],
    "widebody_four_engine": ["A340"]
}

def load_icons(icons_dir="assets/icons"):
    """Memuat semua file SVG ke dalam memori (Cache) agar render cepat."""
    if not os.path.exists(icons_dir):
        print(f"[WARNING] Folder ikon tidak ditemukan: {icons_dir}")
        return

    for filename in os.listdir(icons_dir):
        if filename.endswith(".svg"):
            name = filename[:-4]
            path = os.path.join(icons_dir, filename)

            renderer = QSvgRenderer(path)
            # Render ke ukuran 32x32 piksel (cukup untuk radar)
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()

            _ICON_CACHE[name] = pixmap
    print(f"[INFO] Berhasil memuat {len(_ICON_CACHE)} ikon pesawat.")

def get_icon_for_aircraft(ac_type):
    """Mencocokkan tipe pesawat dengan nama file ikon."""
    if not ac_type:
        return None

    ac_type_upper = ac_type.upper()

    for icon_name, keywords in AIRCRAFT_CATEGORIES.items():
        for kw in keywords:
            if kw in ac_type_upper:
                return icon_name

    return None # Mengembalikan None jika tidak cocok (Militer, Heli, dll)

class AircraftItem(QGraphicsItem):
    def __init__(self, callsign, aircraft_type=""):
        super().__init__()
        self.callsign = callsign
        self.aircraft_type = aircraft_type
        self.heading = 0
        self.size = 4 # Ukuran untuk panah default
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setTransformOriginPoint(0, 0)

    def update_data(self, x, y, heading, aircraft_type=""):
        self.setPos(x / 100.0, y / 100.0)

        # Perbarui tipe pesawat jika berubah
        if aircraft_type and self.aircraft_type != aircraft_type:
            self.aircraft_type = aircraft_type

        if self.heading != heading:
            self.heading = heading
            self.setRotation(self.heading)

    def boundingRect(self):
        # Perbesar sedikit area klik agar mudah dipilih
        return QRectF(-16, -16, 32, 32)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # Cari ikon berdasarkan tipe pesawat
        icon_name = get_icon_for_aircraft(self.aircraft_type)
        pixmap = _ICON_CACHE.get(icon_name) if icon_name else None

        if pixmap:
            # Gambar Ikon SVG
            if self.isSelected():
                # Beri efek seleksi (lingkaran putih)
                painter.setPen(QPen(Qt.white, 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(-12, -12, 24, 24)

            # Gambar di tengah dengan rotasi (rotasi diurus oleh setRotation)
            painter.drawPixmap(-pixmap.width() // 2, -pixmap.height() // 2, pixmap)
        else:
            # Gambar Default: Panah Kuning (Untuk Militer, Heli, dll)
            painter.setBrush(QBrush(QColor("#f4b400")))

            if self.isSelected():
                painter.setPen(QPen(Qt.white, 1.5))
            else:
                painter.setPen(Qt.NoPen)

            s = self.size
            polygon = QPolygonF([
                QPointF(0, -s * 1.2),
                QPointF(s * 0.8, s * 1.0),
                QPointF(0, s * 0.6),
                QPointF(-s * 0.8, s * 1.0)
            ])
            painter.drawPolygon(polygon)
