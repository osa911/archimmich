"""
About dialog component for ArchImmich.
"""

import webbrowser
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from src.constants import VERSION
from src.utils.helpers import get_resource_path


class AboutDialog(QDialog):
    """About dialog showing app information and links."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About ArchImmich")
        self.setFixedSize(400, 350)
        self.setModal(True)

        # Center the dialog on parent
        if parent:
            parent_geometry = parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - 400) // 2
            y = parent_geometry.y() + (parent_geometry.height() - 350) // 2
            self.move(x, y)

        self.setup_ui()

    def setup_ui(self):
        """Setup the About dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Logo and title section
        self.setup_header(layout)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # App information
        self.setup_app_info(layout)

        # Links section
        self.setup_links(layout)

        # Add stretch to push close button to bottom
        layout.addStretch()

        # Close button
        self.setup_close_button(layout)

    def setup_header(self, layout):
        """Setup the header with logo and title."""
        header_layout = QHBoxLayout()

        # Logo
        logo_label = QLabel()
        try:
            pixmap = QPixmap(get_resource_path("src/resources/immich-logo.svg"))
            scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        except:
            # Fallback if logo not found
            logo_label.setText("📁")
            logo_label.setStyleSheet("font-size: 48px;")

        logo_label.setAlignment(Qt.AlignCenter)

        # Title and version
        title_layout = QVBoxLayout()

        title_label = QLabel("ArchImmich")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        version_label = QLabel(f"Version {VERSION}")
        version_label.setStyleSheet("color: #666666; font-size: 12px;")
        version_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()

        header_layout.addWidget(logo_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)

    def setup_app_info(self, layout):
        """Setup app description."""
        description = QLabel(
            "A modern export and archive tool designed for users of the Immich platform. "
            "Simplifies the process of fetching media buckets and exporting them into archives."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #555555; line-height: 1.4;")
        description.setAlignment(Qt.AlignLeft)
        layout.addWidget(description)

    def setup_links(self, layout):
        """Setup links section."""
        links_layout = QVBoxLayout()
        links_layout.setSpacing(10)

        # GitHub link
        github_layout = QHBoxLayout()
        github_icon = QLabel("🔗")
        github_icon.setStyleSheet("font-size: 16px;")

        github_button = QPushButton("View on GitHub")
        github_button.setStyleSheet("""
            QPushButton {
                background-color: #24292e;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2f363d;
            }
            QPushButton:pressed {
                background-color: #1b1f23;
            }
        """)
        github_button.clicked.connect(self.open_github)

        github_layout.addWidget(github_icon)
        github_layout.addWidget(github_button)
        github_layout.addStretch()

        # Buy Me a Coffee link
        coffee_layout = QHBoxLayout()
        coffee_icon = QLabel("☕")
        coffee_icon.setStyleSheet("font-size: 16px;")

        coffee_button = QPushButton("Buy Me a Coffee")
        coffee_button.setStyleSheet("""
            QPushButton {
                background-color: #ff813f;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #ff9a5a;
            }
            QPushButton:pressed {
                background-color: #e6732e;
            }
        """)
        coffee_button.clicked.connect(self.open_coffee)

        coffee_layout.addWidget(coffee_icon)
        coffee_layout.addWidget(coffee_button)
        coffee_layout.addStretch()

        links_layout.addLayout(github_layout)
        links_layout.addLayout(coffee_layout)

        layout.addLayout(links_layout)

    def setup_close_button(self, layout):
        """Setup close button."""
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 8px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def open_github(self):
        """Open GitHub repository in browser."""
        webbrowser.open("https://github.com/osa911/archimmich")

    def open_coffee(self):
        """Open Buy Me a Coffee page in browser."""
        webbrowser.open("https://buymeacoffee.com/osa911")