# frontend/map_view.py

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

class MapView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFocusPolicy(Qt.StrongFocus)

    def mousePressEvent(self, event):
        # Jika klik kiri dan bukan pada pesawat, bersihkan seleksi
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item is None or not hasattr(item, 'callsign'):
                self.scene().clearSelection()
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def zoom_in(self):
        self.scale(1.25, 1.25)

    def zoom_out(self):
        self.scale(0.8, 0.8)
