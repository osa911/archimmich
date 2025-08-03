from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QLinearGradient
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect

class AlbumThumbnail(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.setFixedSize(222, 222)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        # Set transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setPixmap(self, pixmap):
        if pixmap:
            # Scale to cover the entire area while maintaining aspect ratio
            scaled_size = pixmap.size()
            scaled_size.scale(222, 222, Qt.KeepAspectRatioByExpanding)
            self.pixmap = pixmap.scaled(scaled_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

            # Center the scaled image if it's larger than the target size
            if self.pixmap.width() > 222 or self.pixmap.height() > 222:
                x = (self.pixmap.width() - 222) // 2
                y = (self.pixmap.height() - 222) // 2
                self.pixmap = self.pixmap.copy(x, y, 222, 222)
        else:
            self.pixmap = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Create rounded rect path
        rect = QRectF(4, 4, 214, 214)  # Smaller to account for shadow
        path = QPainterPath()
        path.addRoundedRect(rect, 15, 15)

        # Draw shadow path (slightly larger)
        shadowPath = QPainterPath()
        shadowPath.addRoundedRect(rect.adjusted(-2, -2, 2, 2), 15, 15)

        # Draw content
        painter.setClipPath(path)

        if not self.pixmap:
            # Draw gradient background for placeholder
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0, QColor("#f5f5f5"))
            gradient.setColorAt(1, QColor("#e8e8e8"))
            painter.fillPath(path, gradient)
        else:
            # Draw image
            painter.drawPixmap(rect.toRect(), self.pixmap)

        # Draw border
        painter.setPen(QColor(0, 0, 0, 20))
        painter.drawPath(path)