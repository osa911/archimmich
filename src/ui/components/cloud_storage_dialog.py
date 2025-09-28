"""
Cloud Storage Configuration Dialog for ArchImmich
Provides a professional interface for configuring cloud storage providers.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QWidget, QFormLayout, QComboBox, QCheckBox, QGroupBox,
    QMessageBox, QProgressBar, QTextEdit, QFrame, QSpacerItem, QSizePolicy,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap
import json
import os
from src.utils.helpers import get_resource_path, get_path_in_app
from src.managers.cloud_storage_manager import CloudStorageManager


class CloudStorageTestThread(QThread):
    """Thread for testing cloud storage connections without blocking UI."""

    test_completed = pyqtSignal(bool, str)

    def __init__(self, storage_type, config):
        super().__init__()
        self.storage_type = storage_type
        self.config = config
        self.cloud_manager = CloudStorageManager()

    def run(self):
        """Run the connection test."""
        try:
            if self.storage_type == "webdav":
                success, message = self.cloud_manager.test_webdav_connection(
                    self.config['url'],
                    self.config['username'],
                    self.config['password'],
                    self.config.get('auth_type', 'basic')
                )
            elif self.storage_type == "s3":
                success, message = self.cloud_manager.test_s3_connection(
                    self.config['endpoint_url'],
                    self.config['access_key'],
                    self.config['secret_key'],
                    self.config['bucket_name'],
                    self.config.get('region', 'us-east-1')
                )
            else:
                success, message = False, "Unknown storage type"

            self.test_completed.emit(success, message)

        except Exception as e:
            self.test_completed.emit(False, f"Test failed: {str(e)}")
        finally:
            self.cloud_manager.close()


class CloudStorageDialog(QDialog):
    """Professional cloud storage configuration dialog."""

    configuration_saved = pyqtSignal(dict)

    def __init__(self, parent=None, existing_config=None):
        super().__init__(parent)
        self.existing_config = existing_config or {}
        self.test_thread = None
        self.setup_ui()
        self.load_existing_config()

    def setup_ui(self):
        """Setup the dialog UI."""
        # Set window title based on whether we're editing or creating
        if self.existing_config:
            preset_name = self.existing_config.get('display_name', 'Unknown Preset')
            self.setWindowTitle(f"Edit Cloud Storage: {preset_name}")
        else:
            self.setWindowTitle("Add New Cloud Storage")
        self.setModal(True)
        self.resize(735, 650)  # Added 5px to width from 730px
        self.setMinimumSize(635, 550)  # Added 5px to minimum width from 630px

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Configure Cloud Storage")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Configure cloud storage providers for exporting your archives. "
            "Your credentials are stored securely and encrypted."
        )
        desc_label.setWordWrap(True)
        # Use default styling
        main_layout.addWidget(desc_label)

        # Preset name
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset Name:"))
        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setPlaceholderText("e.g., Work WebDAV, Personal S3, Backup Server")
        self.preset_name_edit.setMinimumWidth(400)
        preset_layout.addWidget(self.preset_name_edit)
        main_layout.addLayout(preset_layout)

        # Tab widget for different storage types
        self.tab_widget = QTabWidget()
        self.setup_webdav_tab()
        self.setup_s3_tab()
        main_layout.addWidget(self.tab_widget)

        # Test connection section
        self.setup_test_section(main_layout)

        # Buttons
        self.setup_buttons(main_layout)

    def setup_webdav_tab(self):
        """Setup WebDAV configuration tab."""
        webdav_tab = QWidget()
        layout = QVBoxLayout(webdav_tab)
        layout.setSpacing(15)

        # WebDAV group
        webdav_group = QGroupBox("WebDAV Configuration")
        webdav_layout = QFormLayout(webdav_group)
        webdav_layout.setSpacing(10)

        # Server URL
        self.webdav_url_edit = QLineEdit()
        self.webdav_url_edit.setPlaceholderText("https://your-nextcloud.com/remote.php/dav/files/username/")
        self.webdav_url_edit.setToolTip("Enter your WebDAV server URL")
        self.webdav_url_edit.setMinimumWidth(400)  # Increased width
        webdav_layout.addRow("Server URL:", self.webdav_url_edit)

        # Username
        self.webdav_username_edit = QLineEdit()
        self.webdav_username_edit.setPlaceholderText("Your username")
        self.webdav_username_edit.setMinimumWidth(400)  # Increased width
        webdav_layout.addRow("Username:", self.webdav_username_edit)

        # Password
        self.webdav_password_edit = QLineEdit()
        self.webdav_password_edit.setEchoMode(QLineEdit.Password)
        self.webdav_password_edit.setPlaceholderText("Your password or app password")
        self.webdav_password_edit.setMinimumWidth(400)  # Increased width
        webdav_layout.addRow("Password:", self.webdav_password_edit)

        # Authentication type with info icon
        self.webdav_auth_combo = QComboBox()
        self.webdav_auth_combo.addItems(["Standard", "Digest"])
        self.webdav_auth_combo.setToolTip("Choose authentication method")

        # Info button with detailed tooltip
        info_button = QPushButton("?")
        info_button.setFixedSize(20, 20)
        info_button.setStyleSheet("""
            QPushButton {
                border: 1px solid palette(mid);
                border-radius: 10px;
                background-color: palette(button);
                color: palette(text);
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        info_button.setToolTip("""
<b>Authentication Types:</b><br><br>
<b>Standard:</b> Most common method. Credentials are sent with each request.
Works with all WebDAV servers including Nextcloud, ownCloud, and most others.<br><br>
<b>Digest:</b> More secure method. Server sends a challenge, client responds with a hash.
Some servers require this for enhanced security.
        """)

        # Create a horizontal layout for the combo and info button
        auth_widget_layout = QHBoxLayout()
        auth_widget_layout.setContentsMargins(0, 0, 0, 0)
        auth_widget_layout.addWidget(self.webdav_auth_combo)
        auth_widget_layout.addWidget(info_button)
        auth_widget_layout.addStretch()

        auth_widget = QWidget()
        auth_widget.setLayout(auth_widget_layout)
        webdav_layout.addRow("Authentication:", auth_widget)

        # Remote directory
        self.webdav_remote_dir_edit = QLineEdit()
        self.webdav_remote_dir_edit.setPlaceholderText("ArchImmich/Exports")
        self.webdav_remote_dir_edit.setToolTip("Directory on the server where files will be uploaded")
        self.webdav_remote_dir_edit.setMinimumWidth(400)  # Increased width
        webdav_layout.addRow("Remote Directory:", self.webdav_remote_dir_edit)

        layout.addWidget(webdav_group)

        # Help text
        help_text = QTextEdit()
        help_text.setMaximumHeight(140)
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <b>WebDAV Setup Help:</b><br>
        • <b>Nextcloud/ownCloud:</b> Use your server URL + /remote.php/dav/files/username/<br>
        • <b>Other WebDAV:</b> Use your WebDAV server URL<br>
        • <b>App Passwords:</b> For Nextcloud, use an app password instead of your main password<br>
        • <b>Remote Directory:</b> Leave empty to use the root directory
        """)
        # Use default styling - no custom styles needed
        layout.addWidget(help_text)

        layout.addStretch()
        self.tab_widget.addTab(webdav_tab, "WebDAV")

    def setup_s3_tab(self):
        """Setup S3 configuration tab."""
        s3_tab = QWidget()
        layout = QVBoxLayout(s3_tab)
        layout.setSpacing(15)

        # S3 group
        s3_group = QGroupBox("S3 Configuration")
        s3_layout = QFormLayout(s3_group)
        s3_layout.setSpacing(10)

        # Endpoint URL
        self.s3_endpoint_edit = QLineEdit()
        self.s3_endpoint_edit.setPlaceholderText("https://s3.amazonaws.com or https://your-minio.com")
        self.s3_endpoint_edit.setToolTip("S3 endpoint URL")
        self.s3_endpoint_edit.setMinimumWidth(400)  # Increased width
        s3_layout.addRow("Endpoint URL:", self.s3_endpoint_edit)

        # Access Key
        self.s3_access_key_edit = QLineEdit()
        self.s3_access_key_edit.setPlaceholderText("Your access key")
        self.s3_access_key_edit.setMinimumWidth(400)  # Increased width
        s3_layout.addRow("Access Key:", self.s3_access_key_edit)

        # Secret Key
        self.s3_secret_key_edit = QLineEdit()
        self.s3_secret_key_edit.setEchoMode(QLineEdit.Password)
        self.s3_secret_key_edit.setPlaceholderText("Your secret key")
        self.s3_secret_key_edit.setMinimumWidth(400)  # Increased width
        s3_layout.addRow("Secret Key:", self.s3_secret_key_edit)

        # Bucket Name
        self.s3_bucket_edit = QLineEdit()
        self.s3_bucket_edit.setPlaceholderText("your-bucket-name")
        self.s3_bucket_edit.setMinimumWidth(400)  # Increased width
        s3_layout.addRow("Bucket Name:", self.s3_bucket_edit)

        # Region
        self.s3_region_edit = QLineEdit()
        self.s3_region_edit.setPlaceholderText("us-east-1")
        self.s3_region_edit.setText("us-east-1")
        self.s3_region_edit.setMinimumWidth(400)  # Increased width
        s3_layout.addRow("Region:", self.s3_region_edit)

        # Remote path prefix
        self.s3_remote_prefix_edit = QLineEdit()
        self.s3_remote_prefix_edit.setPlaceholderText("ArchImmich/Exports/")
        self.s3_remote_prefix_edit.setToolTip("Prefix for uploaded files")
        self.s3_remote_prefix_edit.setMinimumWidth(400)  # Increased width
        s3_layout.addRow("Remote Path Prefix:", self.s3_remote_prefix_edit)

        layout.addWidget(s3_group)

        # Help text
        help_text = QTextEdit()
        help_text.setMaximumHeight(140)
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <b>S3 Setup Help:</b><br>
        • <b>AWS S3:</b> Use s3.amazonaws.com as endpoint<br>
        • <b>MinIO:</b> Use your MinIO server URL<br>
        • <b>Other S3-compatible:</b> Use your service's endpoint URL<br>
        • <b>Bucket:</b> Must already exist and be accessible<br>
        • <b>Region:</b> Use the correct region for your bucket
        """)
        # Use default styling - no custom styles needed
        layout.addWidget(help_text)

        layout.addStretch()
        self.tab_widget.addTab(s3_tab, "S3 Compatible")

    def setup_test_section(self, parent_layout):
        """Setup connection test section."""
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout(test_group)

        # Test button
        self.test_button = QPushButton("Test Connection")
        self.test_button.setIcon(QIcon(get_resource_path("src/resources/icons/download-icon.svg")))
        self.test_button.clicked.connect(self.test_connection)
        test_layout.addWidget(self.test_button)

        # Test progress
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        test_layout.addWidget(self.test_progress)

        # Test result
        self.test_result_label = QLabel()
        self.test_result_label.setWordWrap(True)
        self.test_result_label.setVisible(False)
        test_layout.addWidget(self.test_result_label)

        parent_layout.addWidget(test_group)

    def setup_buttons(self, parent_layout):
        """Setup dialog buttons."""
        button_layout = QHBoxLayout()

        # Save button
        self.save_button = QPushButton("Save Configuration")
        # Use default styling
        self.save_button.clicked.connect(self.save_configuration)
        button_layout.addWidget(self.save_button)

        button_layout.addStretch()

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        parent_layout.addLayout(button_layout)

    def showEvent(self, event):
        """Override showEvent to center the dialog when it's shown."""
        super().showEvent(event)
        # Use QTimer to center after the dialog is fully rendered
        QTimer.singleShot(0, self.center_on_parent)

    def center_on_parent(self):
        """Center the dialog relative to the parent window."""
        # Find the main window (top-level window)
        main_window = None
        if self.parent():
            # Walk up the parent hierarchy to find the main window
            current = self.parent()
            while current:
                if current.isWindow():
                    main_window = current
                    break
                current = current.parent()

        if main_window:
            # Get main window geometry
            main_window_geometry = main_window.geometry()

            # Calculate center position
            x = main_window_geometry.x() + (main_window_geometry.width() - self.width()) // 2
            y = main_window_geometry.y() + (main_window_geometry.height() - self.height()) // 2

            # Move dialog to center position
            self.move(x, y)
        else:
            # If no main window, center on screen
            screen = QApplication.desktop().screenGeometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    def load_existing_config(self):
        """Load existing configuration if provided."""
        if not self.existing_config:
            return

        config = self.existing_config

        # Load preset name
        self.preset_name_edit.setText(config.get('display_name', ''))

        if config.get('type') == 'webdav':
            self.tab_widget.setCurrentIndex(0)
            self.webdav_url_edit.setText(config.get('url', ''))
            self.webdav_username_edit.setText(config.get('username', ''))
            self.webdav_password_edit.setText(config.get('password', ''))
            # Map backend auth_type to display name
            auth_type = config.get('auth_type', 'basic')
            display_name = "Standard" if auth_type == "basic" else "Digest"
            self.webdav_auth_combo.setCurrentText(display_name)
            self.webdav_remote_dir_edit.setText(config.get('remote_directory', ''))
        elif config.get('type') == 's3':
            self.tab_widget.setCurrentIndex(1)
            self.s3_endpoint_edit.setText(config.get('endpoint_url', ''))
            self.s3_access_key_edit.setText(config.get('access_key', ''))
            self.s3_secret_key_edit.setText(config.get('secret_key', ''))
            self.s3_bucket_edit.setText(config.get('bucket_name', ''))
            self.s3_region_edit.setText(config.get('region', 'us-east-1'))
            self.s3_remote_prefix_edit.setText(config.get('remote_prefix', ''))

    def test_connection(self):
        """Test the cloud storage connection."""
        if self.test_thread and self.test_thread.isRunning():
            return

        # Get current configuration
        config = self.get_current_config()
        if not config:
            return

        # Start test
        self.test_button.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, 0)  # Indeterminate progress
        self.test_result_label.setVisible(False)

        # Start test thread
        self.test_thread = CloudStorageTestThread(config['type'], config)
        self.test_thread.test_completed.connect(self.on_test_completed)
        self.test_thread.start()

    def on_test_completed(self, success, message):
        """Handle test completion."""
        self.test_button.setEnabled(True)
        self.test_progress.setVisible(False)
        self.test_result_label.setVisible(True)

        if success:
            self.test_result_label.setText(f"✓ {message}")
            self.test_result_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.test_result_label.setText(f"✗ {message}")
            self.test_result_label.setStyleSheet("color: red; font-weight: bold;")

    def get_current_config(self):
        """Get current configuration from the form."""
        # Get preset name
        preset_name = self.preset_name_edit.text().strip()
        if not preset_name:
            QMessageBox.warning(self, "Missing Information",
                              "Please enter a preset name.")
            return None

        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:  # WebDAV
            url = self.webdav_url_edit.text().strip()
            username = self.webdav_username_edit.text().strip()
            password = self.webdav_password_edit.text().strip()
            remote_dir = self.webdav_remote_dir_edit.text().strip()

            if not url or not username or not password:
                QMessageBox.warning(self, "Missing Information",
                                  "Please fill in all required WebDAV fields.")
                return None

            return {
                'type': 'webdav',
                'display_name': preset_name,
                'url': url,
                'username': username,
                'password': password,
                'auth_type': 'basic' if self.webdav_auth_combo.currentText() == 'Standard' else 'digest',
                'remote_directory': remote_dir
            }

        elif current_tab == 1:  # S3
            endpoint = self.s3_endpoint_edit.text().strip()
            access_key = self.s3_access_key_edit.text().strip()
            secret_key = self.s3_secret_key_edit.text().strip()
            bucket = self.s3_bucket_edit.text().strip()
            region = self.s3_region_edit.text().strip()
            remote_prefix = self.s3_remote_prefix_edit.text().strip()

            if not endpoint or not access_key or not secret_key or not bucket:
                QMessageBox.warning(self, "Missing Information",
                                  "Please fill in all required S3 fields.")
                return None

            return {
                'type': 's3',
                'display_name': preset_name,
                'endpoint_url': endpoint,
                'access_key': access_key,
                'secret_key': secret_key,
                'bucket_name': bucket,
                'region': region or 'us-east-1',
                'remote_prefix': remote_prefix
            }

        return None

    def save_configuration(self):
        """Save the configuration."""
        config = self.get_current_config()
        if not config:
            return

        # Test connection before saving
        if not self.test_result_label.isVisible() or "✓" not in self.test_result_label.text():
            reply = QMessageBox.question(
                self, "Save Without Testing?",
                "You haven't tested the connection yet. Do you want to save anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # Save configuration
        self.configuration_saved.emit(config)
        self.accept()

    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.terminate()
            self.test_thread.wait()
        event.accept()
