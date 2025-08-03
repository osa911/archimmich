from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QLinearGradient
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect

class AlbumThumbnail(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.original_pixmap = None
        self.current_size = 212
        self.setFixedSize(self.current_size, self.current_size)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

        # Set transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setPixmap(self, pixmap):
        self.original_pixmap = pixmap
        self.updatePixmap()
        self.update()

    def updatePixmap(self):
        """Update the displayed pixmap based on current size."""
        if self.original_pixmap:
            # Scale to cover the entire area while maintaining aspect ratio
            scaled_size = self.original_pixmap.size()
            scaled_size.scale(self.current_size, self.current_size, Qt.KeepAspectRatioByExpanding)
            self.pixmap = self.original_pixmap.scaled(scaled_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

            # Center the scaled image if it's larger than the target size
            if self.pixmap.width() > self.current_size or self.pixmap.height() > self.current_size:
                x = (self.pixmap.width() - self.current_size) // 2
                y = (self.pixmap.height() - self.current_size) // 2
                self.pixmap = self.pixmap.copy(x, y, self.current_size, self.current_size)
        else:
            self.pixmap = None

    def updateSize(self, size):
        """Update the widget and image size."""
        self.current_size = size
        self.updatePixmap()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Create rounded rect path
        padding = 4  # Padding for shadow
        content_size = self.current_size - (padding * 2)  # Adjust for padding
        rect = QRectF(padding, padding, content_size, content_size)  # Smaller to account for shadow
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