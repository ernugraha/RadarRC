# frontend/map_items.py

from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPolygonF, QBrush, QColor, QPen

class AircraftItem(QGraphicsItem):
    def __init__(self, callsign):
        super().__init__()
        self.callsign = callsign
        self.heading = 0
        self.size = 4  # <-- DIPERKECIL DARI 8 MENJADI 4
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setTransformOriginPoint(0, 0)

    def update_data(self, x, y, heading):
        self.setPos(x / 100.0, y / 100.0)

        if self.heading != heading:
            self.heading = heading
            self.setRotation(self.heading)

    def boundingRect(self):
        return QRectF(-self.size, -self.size, self.size * 2, self.size * 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        # Warna kuning
        painter.setBrush(QBrush(QColor("#f4b400")))

        if self.isSelected():
            painter.setPen(QPen(Qt.white, 1.5))
        else:
            painter.setPen(Qt.NoPen)

        s = self.size
        # Bentuk pesawat yang lebih ramping
        polygon = QPolygonF([
            QPointF(0, -s * 1.2),      # Hidung lancip
            QPointF(s * 0.8, s * 1.0), # Sayap kanan
            QPointF(0, s * 0.6),       # Ekor
            QPointF(-s * 0.8, s * 1.0) # Sayap kiri
        ])
        painter.drawPolygon(polygon)
