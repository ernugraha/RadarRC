# frontend/map_view.py

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, Signal, QVariantAnimation, QEasingCurve, QPointF
from PySide6.QtGui import QPainter

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

    def set_calibration_mode(self, enabled):
        """Memungkinkan drag pada item (bandara) saat kalibrasi."""
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag) # Matikan pan peta
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag) # Nyalakan pan peta

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.user_panned.emit()
        super().mouseMoveEvent(event)

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
