# frontend/map_view.py

from PySide6.QtWidgets import QGraphicsView, QGraphicsLineItem, QGraphicsSimpleTextItem
from PySide6.QtCore import Qt, Signal, QVariantAnimation, QEasingCurve, QPointF, QLineF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
import math

class MapView(QGraphicsView):
    user_panned = Signal()

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFocusPolicy(Qt.StrongFocus)

        self.anim_center = None

        # Variabel Vector Line
        self.vector_start = None
        self.current_line = None
        self.current_text = None

    def clear_vector(self):
        """Menghapus garis vektor dari peta."""
        if self.current_line:
            self.scene().removeItem(self.current_line)
            self.current_line = None
        if self.current_text:
            self.scene().removeItem(self.current_text)
            self.current_text = None
        self.vector_start = None

    def mousePressEvent(self, event):
        # Klik Kiri: Mulai Pan peta, dan hapus vektor
        if event.button() == Qt.LeftButton:
            self.clear_vector()
            super().mousePressEvent(event)

        # Klik Kanan: Mulai menggambar vektor
        elif event.button() == Qt.RightButton:
            self.vector_start = self.mapToScene(event.pos())

            # Hapus garis vektor sebelumnya jika ada
            self.clear_vector()
            self.vector_start = self.mapToScene(event.pos())

            # Buat garis baru (warna hijau neon)
            pen = QPen(QColor("#00ff00"))
            pen.setWidth(2)
            pen.setCosmetic(True)
            self.current_line = self.scene().addLine(QLineF(self.vector_start, self.vector_start), pen)
            self.current_line.setZValue(999)

            # Buat teks untuk info Heading & Jarak
            self.current_text = QGraphicsSimpleTextItem("")
            self.current_text.setBrush(QColor("#00ff00"))
            self.current_text.setFont(QFont("Arial", 10, QFont.Bold))
            self.scene().addItem(self.current_text)
            self.current_text.setZValue(1000)

            event.accept()

    def mouseMoveEvent(self, event):
        # Geser Kanan: Update garis
        if (event.buttons() & Qt.RightButton) and self.vector_start and self.current_line:
            end_pos = self.mapToScene(event.pos())
            self.current_line.setLine(QLineF(self.vector_start, end_pos))

            # Hitung Jarak (Skala: 1px = 100 studs, 3307 studs = 1 NM)
            dx = end_pos.x() - self.vector_start.x()
            dy = self.vector_start.y() - end_pos.y() # Invert Y karena Qt Y ke bawah
            dist_px = math.hypot(dx, dy)
            dist_nm = (dist_px * 100) / 3307.0

            # Hitung Heading (0-360 derajat)
            angle = math.degrees(math.atan2(dx, dy))
            if angle < 0: angle += 360

            # Tampilkan Teks
            text = f"{int(angle):03d}° | {dist_nm:.1f} NM"
            self.current_text.setText(text)
            self.current_text.setPos(end_pos + QPointF(10, -20))

            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Selesai menarik garis
        if event.button() == Qt.RightButton and self.current_line:
            self.vector_start = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def smooth_center_on(self, target_pos):
        if self.anim_center:
            self.anim_center.stop()
        start_pos = self.mapToScene(self.viewport().rect().center())
        self.anim_center = QVariantAnimation(self)
        self.anim_center.setStartValue(start_pos)
        self.anim_center.setEndValue(target_pos)
        self.anim_center.setDuration(400)
        self.anim_center.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_center.valueChanged.connect(self.centerOn)
        self.anim_center.start()

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

    def keyPressEvent(self, event):
        step = 50
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()

        if event.key() == Qt.Key_Left: h_bar.setValue(h_bar.value() - step)
        elif event.key() == Qt.Key_Right: h_bar.setValue(h_bar.value() + step)
        elif event.key() == Qt.Key_Up: v_bar.setValue(v_bar.value() - step)
        elif event.key() == Qt.Key_Down: v_bar.setValue(v_bar.value() + step)
        else: super().keyPressEvent(event)
