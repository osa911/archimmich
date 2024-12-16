from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QBrush
from PIL import Image, ImageOps
from io import BytesIO
import requests

def display_avatar(self, avatar_url):
    """
    Fetch and display the user's avatar in the avatar QLabel.
    Args:
        avatar_url (str): The full URL to the user's avatar image.
    """
    self.logs.append(f"Fetching avatar...")

    try:
        response = requests.get(avatar_url, headers=self.getHeaders(), stream=True)
        response.raise_for_status()

        # Load the image using Pillow
        image = Image.open(BytesIO(response.content))

        # Correct orientation based on EXIF metadata
        image = ImageOps.exif_transpose(image)

        # Convert Pillow Image to QPixmap
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())

        # Scale the pixmap to fit the label
        size = min(self.avatar_label.width(), self.avatar_label.height())
        pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        # Create a rounded mask
        rounded_pixmap = QPixmap(size, size)
        rounded_pixmap.fill(Qt.transparent)

        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(pixmap))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.end()

        # Set the rounded pixmap to the QLabel
        self.avatar_label.setPixmap(rounded_pixmap)
        self.avatar_label.show()

        self.logs.append("Avatar displayed successfully.")

    except requests.exceptions.RequestException as e:
        self.logs.append(f"Failed to load avatar: {str(e)}")
    except Exception as e:
        self.logs.append(f"Failed to process avatar image: {str(e)}")