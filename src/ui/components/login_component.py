from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QPixmap

from src.utils.helpers import get_resource_path, display_avatar, save_settings


class LoginComponent(QWidget):
    # Signals
    login_successful = pyqtSignal(dict)  # Emits user data when login succeeds
    login_failed = pyqtSignal(str)  # Emits error message when login fails

    def __init__(self, login_manager, logger=None):
        super().__init__()
        self.login_manager = login_manager
        self.logger = logger

        # Store references to containers for theme updates
        self.theme_containers = []

        self.setup_ui()

    def setup_ui(self):
        """Setup the login component UI."""
        self.layout = QVBoxLayout(self)

        # Add Logo
        self.init_logo_layout()

        # Login Fields
        self.init_login_fields()

    def init_logo_layout(self):
        """Initialize the logo layout."""
        image_label = QLabel()
        pixmap = QPixmap(get_resource_path("src/resources/immich-logo.svg"))
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        image_label.setScaledContents(True)
        image_label.setFixedSize(132, 45)

        logo_layout = QHBoxLayout()
        logo_layout.addWidget(image_label)
        logo_layout.setAlignment(Qt.AlignHCenter)
        self.layout.addLayout(logo_layout)

    def init_login_fields(self):
        """Initialize login form fields."""
        # Server IP Field with clear button inside
        self.server_ip_label = QLabel("Server IP:")
        self.layout.addWidget(self.server_ip_label)

        # Create container for server IP field with internal clear button
        server_ip_container = QWidget()
        server_ip_container.setStyleSheet("""
            QWidget {
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
            }
        """)
        # Store reference for theme updates
        self.theme_containers.append(server_ip_container)
        server_ip_layout = QHBoxLayout(server_ip_container)
        server_ip_layout.setContentsMargins(8, 2, 4, 2)  # Left padding for text, minimal right padding
        server_ip_layout.setSpacing(0)

        self.server_ip_field = QLineEdit()
        self.server_ip_field.setPlaceholderText("Enter server IP (e.g., http://192.168.1.1:2283)")
        self.server_ip_field.setStyleSheet("QLineEdit { border: none; background: transparent; }")
        self.server_ip_field.textChanged.connect(self.update_clear_buttons_visibility)
        server_ip_layout.addWidget(self.server_ip_field)

        self.server_ip_clear_button = QPushButton("×")
        self.server_ip_clear_button.setFixedSize(16, 16)
        self.server_ip_clear_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #666666;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #333333;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        self.server_ip_clear_button.clicked.connect(lambda: self.server_ip_field.clear())
        self.server_ip_clear_button.hide()  # Initially hidden
        server_ip_layout.addWidget(self.server_ip_clear_button)

        self.layout.addWidget(server_ip_container)

        # API Key Field with clear button inside
        self.api_key_label = QLabel("API Key:")
        self.layout.addWidget(self.api_key_label)

        # Create container for API key field with internal clear button
        api_key_container = QWidget()
        api_key_container.setStyleSheet("""
            QWidget {
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
            }
        """)
        # Store reference for theme updates
        self.theme_containers.append(api_key_container)
        api_key_layout = QHBoxLayout(api_key_container)
        api_key_layout.setContentsMargins(8, 2, 2, 2)  # Left padding for text, minimal right padding
        api_key_layout.setSpacing(0)

        self.api_key_field = QLineEdit()
        self.api_key_field.setPlaceholderText("Enter API key")
        self.api_key_field.setStyleSheet("QLineEdit { border: none; background: transparent; }")
        self.api_key_field.textChanged.connect(self.update_clear_buttons_visibility)
        api_key_layout.addWidget(self.api_key_field)

        self.api_key_clear_button = QPushButton("×")
        self.api_key_clear_button.setFixedSize(16, 16)
        self.api_key_clear_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #666666;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #333333;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        self.api_key_clear_button.clicked.connect(lambda: self.api_key_field.clear())
        self.api_key_clear_button.hide()  # Initially hidden
        api_key_layout.addWidget(self.api_key_clear_button)

        self.layout.addWidget(api_key_container)

        # Remember Me Checkbox
        self.is_remember_me_checkbox = QCheckBox("Remember me")
        self.layout.addWidget(self.is_remember_me_checkbox)

        # Login Button
        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("login_button")
        self.login_button.clicked.connect(self.login)
        self.layout.addWidget(self.login_button)

        # Error message label (initially hidden)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-size: 14px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        self.layout.addWidget(self.error_label)

    def update_clear_buttons_visibility(self):
        """Update visibility of clear buttons based on field content."""
        self.server_ip_clear_button.setVisible(bool(self.server_ip_field.text().strip()))
        self.api_key_clear_button.setVisible(bool(self.api_key_field.text().strip()))

    def load_saved_settings(self, server_ip, api_key):
        """Load saved login settings."""
        if server_ip and api_key:
            self.server_ip_field.setText(server_ip)
            self.api_key_field.setText(api_key)
            self.is_remember_me_checkbox.setChecked(True)
            # Update clear button visibility after loading settings
            self.update_clear_buttons_visibility()

    def reset_fields(self):
        """Reset all login fields."""
        self.server_ip_field.setText("")
        self.api_key_field.setText("")
        self.is_remember_me_checkbox.setChecked(False)
        self.clear_field_errors()

    def clear_field_errors(self):
        """Clear any error styling from input fields."""
        self.server_ip_field.setStyleSheet("QLineEdit { border: none; background: transparent; }")
        self.api_key_field.setStyleSheet("QLineEdit { border: none; background: transparent; }")
        if hasattr(self, 'error_label'):
            self.error_label.hide()

    def validate_inputs(self):
        """Validate login form inputs."""
        is_valid = True
        self.clear_field_errors()

        if not self.api_key_field.text().strip():
            if self.logger:
                self.logger.append("Error: API key cannot be empty.")
            self.api_key_field.setStyleSheet("border: 2px solid red;")
            is_valid = False

        if not self.server_ip_field.text().strip():
            if self.logger:
                self.logger.append("Error: Server IP cannot be empty.")
            self.server_ip_field.setStyleSheet("border: 2px solid red;")
            is_valid = False

        return is_valid

    def login(self):
        """Handle login process."""
        # Clear any previous error messages
        self.error_label.hide()

        if self.logger:
            self.logger.append("Attempting to login...")

        if not self.validate_inputs():
            return

        server_ip = self.server_ip_field.text().strip()
        api_key = self.api_key_field.text().strip()

        self.login_manager.set_credentials(server_ip, api_key, self.is_remember_me_checkbox.isChecked())

        try:
            user = self.login_manager.login()
            user_name = user.get('name', 'Unknown User')
            user_email = user.get('email', 'Unknown Email')

            if self.logger:
                self.logger.append("Login successful!")
                self.logger.append(f"User: {user_name} | Email: {user_email}")

            # Get server version info
            server_info = self.login_manager.getApiManager().get_server_info()
            server_version = ""
            if server_info:
                version = server_info.get('version', 'unknown')
                server_version = version

            # Prepare user data with all necessary info
            user_data = {
                'user': user,
                'server_version': server_version,
                'avatar_fetcher': self.login_manager.get_avatar_fetcher()
            }

            self.login_successful.emit(user_data)

        except Exception as e:
            error_msg = f"Login failed: {str(e)}"

            # Show error message on the login screen
            self.error_label.setText("Login failed. Please check your API key or server.")
            self.error_label.show()

            if self.logger:
                self.logger.append(error_msg)
            self.login_failed.emit(error_msg)

    def update_theme_containers(self):
        """Update theme-aware containers when system theme changes."""
        container_style = """
            QWidget {
                border: 1px solid palette(mid);
                border-radius: 4px;
                background-color: palette(base);
            }
        """
        for container in self.theme_containers:
            container.setStyleSheet(container_style)

    def changeEvent(self, event):
        """Handle change events, including palette changes."""
        if event.type() == QEvent.PaletteChange:
            # System theme changed, update our themed containers
            self.update_theme_containers()
        super().changeEvent(event)