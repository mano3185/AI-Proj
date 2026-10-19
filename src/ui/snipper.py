"""Full-screen interactive snipping overlay widget in PyQt6."""

from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor
from PyQt6.QtWidgets import QWidget, QApplication
from PIL import Image

from src.capture.screen import ScreenCapture


class SnippingOverlay(QWidget):
    """Semi-transparent overlay to select a screen bounding box."""

    snip_completed = pyqtSignal(object, QPoint)  # (PIL.Image, QPoint)

    def __init__(self, capture_engine: ScreenCapture | None = None, parent=None):
        super().__init__(parent)
        self.capture_engine = capture_engine or ScreenCapture()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self.start_pos: QPoint | None = None
        self.current_pos: QPoint | None = None
        self.is_selecting = False

        # Fit to cover all monitors/screens
        screens_geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(screens_geo)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            self.current_pos = self.start_pos
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.current_pos = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            end_pos = event.globalPosition().toPoint()

            if self.start_pos:
                rect = QRect(self.start_pos, end_pos).normalized()

                # Filter out accidental tiny clicks (< 8 pixels)
                if rect.width() >= 8 and rect.height() >= 8:
                    self.hide()
                    QApplication.processEvents()

                    # Grab cropped region
                    crop_img = self.capture_engine.capture_region(
                        rect.x(), rect.y(), rect.width(), rect.height()
                    )
                    self.snip_completed.emit(crop_img, rect.bottomRight())
                    self.close()
                    return

            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Semi-transparent dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

        if self.is_selecting and self.start_pos and self.current_pos:
            rect = QRect(self.start_pos, self.current_pos).normalized()

            # Clear the selected rectangle area to show underlying screen cleanly
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(rect, Qt.GlobalColor.transparent)

            # Draw glowing bounding border
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            pen = QPen(QColor(137, 180, 250), 2)  # Catppuccin Blue
            painter.setPen(pen)
            painter.drawRect(rect)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
