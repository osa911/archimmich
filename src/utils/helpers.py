import os
import sys
import json
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor
from PIL import Image, ImageOps
from io import BytesIO

def get_resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and PyInstaller builds."""
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller temporary folder for bundled files
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def display_avatar(app_window, fetch_avatar):
    try:
        if fetch_avatar is None:
            # If we have no fetcher, display a default avatar instead
            render_default_avatar(app_window)
            return

        response = fetch_avatar()
        response.raise_for_status()

        # Load the image using Pillow
        image = Image.open(BytesIO(response.content))

        # Correct orientation based on EXIF metadata
        image = ImageOps.exif_transpose(image)

        # Determine the format to save the image
        fmt = image.format if image.format else "PNG"

        # Convert Pillow Image to QPixmap
        buffer = BytesIO()
        image.save(buffer, format=fmt)
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())

        # Scale the pixmap to fit the label
        size = min(app_window.avatar_label.width(), app_window.avatar_label.height())
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
        app_window.avatar_label.setPixmap(rounded_pixmap)
        app_window.logs.append("Avatar displayed successfully.")

    except Exception as e:
        app_window.logs.append(f"Failed to process avatar image: {str(e)}")

def render_default_avatar(app_window):
    """Draws a default circular avatar with a simple person silhouette."""
    size = min(app_window.avatar_label.width(), app_window.avatar_label.height())
    if size == 0:
        size = 50  # fallback if avatar_label is not yet sized

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Draw background circle (all integers)
    painter.setBrush(QBrush(QColor("#888888")))  # gray background
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)

    # Draw a simple person silhouette in white
    painter.setBrush(QBrush(Qt.white))

    # Head
    head_radius = size * 0.2
    head_x = (size - head_radius) / 2
    head_y = size * 0.2
    painter.drawEllipse(int(head_x), int(head_y), int(head_radius), int(head_radius))

    # Body
    body_width = head_radius * 0.5
    body_height = size * 0.3
    body_x = (size - body_width) / 2
    body_y = head_y + head_radius
    painter.drawRect(int(body_x), int(body_y), int(body_width), int(body_height))

    # Arms
    arm_length = size * 0.2
    arm_y = body_y + body_height * 0.3
    painter.drawRect(int(body_x - arm_length), int(arm_y), int(arm_length), int(body_width * 0.3))
    painter.drawRect(int(body_x + body_width), int(arm_y), int(arm_length), int(body_width * 0.3))

    # Legs
    leg_length = size * 0.2
    leg_y = body_y + body_height
    painter.drawRect(int(body_x), int(leg_y), int(body_width * 0.3), int(leg_length))
    painter.drawRect(int(body_x + body_width * 0.7), int(leg_y), int(body_width * 0.3), int(leg_length))

    painter.end()

    app_window.avatar_label.setPixmap(pixmap)
    app_window.logs.append("Default avatar displayed.")

CONFIG_FILE = "archimich_config.json"

def save_settings(server_ip, api_key):
    settings = {
        "server_ip": server_ip,
        "api_key": api_key
    }
    with open(CONFIG_FILE, "w") as config_file:
        json.dump(settings, config_file)
    print("Settings saved successfully.")


def load_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as config_file:
            try:
                settings = json.load(config_file)
                return settings.get("server_ip", ""), settings.get("api_key", "")
            except json.JSONDecodeError:
                print("Error decoding configuration file. Resetting settings.")
                return "", ""
    return "", ""