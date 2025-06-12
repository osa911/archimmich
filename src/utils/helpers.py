import os
import sys
import json
import logging
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor
from PIL import Image, ImageOps
from io import BytesIO

class Logger:
    def __init__(self, logs_widget=None, test_mode=False):
        self.logs_widget = logs_widget

        # Skip file logging in test mode
        self.test_mode = test_mode
        if test_mode:
            self.current_log_file = "test_log.log"
            self.logger = logging.getLogger('archimmich_test')
            self.logger.setLevel(logging.INFO)
            # Use a null handler in test mode to avoid creating files
            self.logger.addHandler(logging.NullHandler())
            return

        # Get application directory and create logs folder inside it
        app_dir = get_app_directory()
        self.log_dir = os.path.join(app_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)

        # Set up file logging
        log_file = os.path.join(self.log_dir, f"archimmich_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
        self.file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Set up logger
        self.logger = logging.getLogger('archimmich')
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        self.logger.addHandler(self.file_handler)

        # Keep track of the current log file
        self.current_log_file = log_file

    def append(self, message, level=logging.INFO):
        """Log a message both to file and UI widget if available."""
        # Log to file if not in test mode
        if not self.test_mode:
            self.logger.log(level, message)

        # Log to UI if widget is available
        if self.logs_widget:
            self.logs_widget.append(message)

    def get_log_file_path(self):
        """Return the path to the current log file."""
        return self.current_log_file

    def __del__(self):
        """Clean up logging handlers."""
        if hasattr(self, 'file_handler') and not self.test_mode:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

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

def get_app_directory():
    """Get the application directory path."""
    # Get application directory
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return app_dir

CONFIG_FILE = os.path.join(get_app_directory(), "config.json")

def save_settings(server_ip: str, api_key: str):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

        with open(CONFIG_FILE, "w") as file:
            json.dump({"server_ip": server_ip, "api_key": api_key}, file)
        print(f"Settings saved successfully to {CONFIG_FILE}")
    except Exception as e:
        print(f"Failed to save settings: {e}")
        raise

def load_settings(config_file=None):
    """
    Load server_ip and api_key from the config file.

    Args:
        config_file (str, optional): Path to the config file. If None, use the default CONFIG_FILE.

    Returns:
        tuple: (server_ip, api_key)
    """
    if config_file is None:
        config_file = CONFIG_FILE

    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                data = json.load(file)
                return data.get("server_ip", ""), data.get("api_key", "")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading settings: {e}")

    return "", ""