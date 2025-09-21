from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QWidget,
    QHBoxLayout, QPushButton, QSplitter, QWIDGETSIZE_MAX
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication, QPixmap, QIcon

from src.ui.components.auto_scroll_text_edit import AutoScrollTextEdit
from src.ui.components.debug_settings_dialog import DebugSettingsDialog
from src.ui.components.about_dialog import AboutDialog
from src.ui.components.login_component import LoginComponent
from src.ui.components.export_component import ExportComponent
from src.utils.helpers import display_avatar, load_settings, Logger, get_resource_path
from src.managers.login_manager import LoginManager
from src.constants import VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT

class MainWindow(QMainWindow):
    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        self.login_manager = LoginManager(config=self.config)

        # Window setup
        self.setup_window()

        # Create main UI
        self.setup_ui()

        # Initialize logger after UI setup
        self.logger = Logger(self.logs)
        self.log(f"ArchImmich v{VERSION} started")
        self.log(f"Log file location: {self.logger.get_log_file_path()}")

        # Set logger on login manager so API manager gets it when created
        self.login_manager.set_logger(self.logger)

        # Load saved settings
        self.load_saved_settings()

    def setup_window(self):
        """Setup main window properties."""
        self.setWindowTitle("ArchImmich")
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - WINDOW_WIDTH) // 2
        y = (screen_geometry.height() - WINDOW_HEIGHT) // 2
        self.setGeometry(x, y, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Set minimum width and height
        self.setMinimumWidth(MIN_WINDOW_WIDTH)
        self.setMinimumHeight(MIN_WINDOW_HEIGHT)

        # Enable window maximization by removing maximum height restriction
        # and ensuring proper window flags are set
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        # Create a scroll area for the main content
        from PyQt5.QtWidgets import QScrollArea
        main_scroll_area = QScrollArea()
        main_scroll_area.setWidgetResizable(True)
        main_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setCentralWidget(main_scroll_area)

        # Create the content widget that will be scrollable
        self.central_widget = QWidget()
        main_scroll_area.setWidget(self.central_widget)

    def setup_ui(self):
        """Setup the main UI layout and components."""
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove main layout margins

        # Create menu bar
        self.setup_menu_bar()

        # Create header with logo and user info
        self.setup_header()

        # Create login component with centering
        self.login_component = LoginComponent(self.login_manager, logger=None)  # Logger will be set later
        self.login_component.login_successful.connect(self.on_login_successful)
        self.login_component.login_failed.connect(self.on_login_failed)

        # Create container to center the login component vertically
        self.login_container = QWidget()
        login_container_layout = QVBoxLayout(self.login_container)
        login_container_layout.addStretch()  # Top spacer
        login_container_layout.addWidget(self.login_component)
        login_container_layout.addStretch()  # Bottom spacer

        self.layout.addWidget(self.login_container)

        # Create export component (initially hidden)
        self.export_component = ExportComponent(self.login_manager, logger=None)  # Logger will be set later
        self.export_component.export_finished.connect(self.on_export_finished)
        self.export_component.hide()

        # Create splitter for export component and logs
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.export_component)

        # Logs section
        self.logs = AutoScrollTextEdit()
        self.logs.setMinimumHeight(100)
        self.logs.setMaximumHeight(150)
        self.logs_container = QWidget()
        logs_layout = QVBoxLayout(self.logs_container)
        self.logs_container.setMaximumHeight(150)
        logs_layout.setContentsMargins(0, 5, 0, 0)
        logs_layout.addWidget(self.logs)
        self.main_splitter.addWidget(self.logs_container)

        # Set initial sizes - give more space to export component
        self.main_splitter.setSizes([600, 100])

        self.layout.addWidget(self.main_splitter)

        # Initialize auto-scroll setting from config
        auto_scroll_enabled = self.config.get('debug', {}).get('auto_scroll_logs', True)
        self.logs.set_auto_scroll(auto_scroll_enabled)

    def setup_header(self):
        """Setup the header bar with logo on left and user info on right."""
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(15, 15, 15, 0)

        # Logo on the left
        self.setup_logo_left()

        # Spacer to push user info to the right
        self.header_layout.addStretch()

        # User info on the right
        self.setup_user_info_right()

        # Initially hide the entire header until login
        self.header_widget.hide()
        self.layout.addWidget(self.header_widget)

    def setup_logo_left(self):
        """Setup the logo on the left side of header."""
        self.logo_container = QWidget()
        logo_layout = QVBoxLayout(self.logo_container)  # Changed to vertical layout
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(5)  # Small spacing between logo and version

        image_label = QLabel()
        pixmap = QPixmap(get_resource_path("src/resources/immich-logo.svg"))
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        image_label.setScaledContents(True)
        image_label.setFixedSize(132, 45)

        # Server version under logo
        self.server_version_label = QLabel("")
        self.server_version_label.setStyleSheet("color: #666666; font-size: 12px;")
        self.server_version_label.setAlignment(Qt.AlignLeft)
        self.server_version_label.hide()  # Initially hidden until login

        logo_layout.addWidget(image_label)
        logo_layout.addWidget(self.server_version_label)
        self.header_layout.addWidget(self.logo_container)

    def setup_user_info_right(self):
        """Setup user info on the right side of header."""
        self.user_info_container = QWidget()
        self.user_info_layout = QHBoxLayout(self.user_info_container)
        self.user_info_layout.setContentsMargins(0, 0, 0, 0)
        self.user_info_layout.setSpacing(10)

        # Text container for user info and logout button
        self.text_container = QWidget()
        text_layout = QVBoxLayout(self.text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(5)

        self.login_status = QLabel("")
        self.login_status.setStyleSheet("color: green; font-size: 14px;")
        self.login_status.setAlignment(Qt.AlignRight)
        text_layout.addWidget(self.login_status)

        # Logout button under the user text
        self.logout_button = QPushButton("Logout")
        self.logout_button.setIcon(QIcon(get_resource_path("src/resources/icons/logout-icon.svg")))
        self.logout_button.setMaximumWidth(90)
        self.logout_button.setMaximumHeight(25)
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.hide()
        text_layout.addWidget(self.logout_button, alignment=Qt.AlignRight)

        # Avatar
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(50, 50)
        self.avatar_label.hide()

        # Add to user info layout: text container (with logout button) + avatar
        self.user_info_layout.addWidget(self.text_container)
        self.user_info_layout.addWidget(self.avatar_label)

        # Initially hide the entire user info container
        self.user_info_container.hide()
        self.header_layout.addWidget(self.user_info_container)

    def setup_menu_bar(self):
        """Setup the main window menu bar."""
        menubar = self.menuBar()

        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        debug_settings_action = settings_menu.addAction('Debug Settings')
        debug_settings_action.triggered.connect(self.show_debug_settings)

        # Add separator
        settings_menu.addSeparator()

        # About action in Settings menu
        about_action = settings_menu.addAction('About ArchImmich')
        about_action.triggered.connect(self.show_about)

    def show_debug_settings(self):
        """Show the debug settings dialog."""
        dialog = DebugSettingsDialog(self.config, self)
        dialog.exec_()

    def show_about(self):
        """Show the about dialog."""
        dialog = AboutDialog(self)
        dialog.exec_()

    def load_saved_settings(self):
        """Load saved settings on startup."""
        server_ip, api_key = load_settings()
        if hasattr(self, 'login_component'):
            self.login_component.load_saved_settings(server_ip, api_key)

    def log(self, message):
        """Log a message both to UI and file."""
        if hasattr(self, 'logger'):
            self.logger.append(message)
        else:
            # Fallback if logger isn't initialized yet
            self.logs.append(message)

    def on_login_successful(self, user_data):
        """Handle successful login."""
        user = user_data['user']
        server_version = user_data['server_version']
        avatar_fetcher = user_data['avatar_fetcher']

        user_name = user.get('name', 'Unknown User')
        user_email = user.get('email', 'Unknown Email')

        # Update UI with user information (right side)
        self.login_status.setText(
            f"<b>{user_name}</b><br>{user_email}"
        )
        self.login_status.setStyleSheet("color: green; font-size: 14px;")

        # Update server version (left side under logo)
        if server_version:
            self.server_version_label.setText(f"Server: {server_version}")
            self.server_version_label.show()

        # Display avatar and show user info container (includes logout button)
        if avatar_fetcher:
            display_avatar(self, avatar_fetcher)
        # show avatar even if no avatar is found. (it will be a placeholder)
        self.avatar_label.show()
        self.logout_button.show()
        self.user_info_container.show()

        # Show the header now that we're logged in
        self.header_widget.show()

        # Hide login container and show export component
        self.login_container.hide()
        self.export_component.show()

        # Reset logs maximum height
        self.logs.setMaximumHeight(QWIDGETSIZE_MAX)
        self.logs_container.setMaximumHeight(QWIDGETSIZE_MAX)

        # Set logger for components
        self.login_component.logger = self.logger
        self.export_component.logger = self.logger

        # Reset export state and enable tabs
        self.export_component.reset_export_state()

    def on_login_failed(self, error_message):
        """Handle failed login."""
        # Don't show header for failed login, let the login component handle the error display
        self.log(f"Login failed: {error_message}")

    def on_export_finished(self):
        """Handle export completion."""
        self.log("Export process completed.")

    def logout(self):
        """Handle logout process."""
        self.log("Logging out...")

        # Stop any ongoing export process before logout
        if hasattr(self.export_component, 'stop_requested') and not self.export_component.stop_requested:
            # Check if export is currently running (stop button is visible)
            self.log("Stopping ongoing export process...")
            self.export_component.stop_export()

        self.login_manager.logout()

        # Reset UI elements
        self.login_status.setText("")
        self.server_version_label.setText("")
        self.server_version_label.hide()
        self.login_status.setStyleSheet("color: red;")

        # Don't reset login fields - keep credentials for convenience
        # Users can use individual clear buttons (×) in each field if needed

        # Reset export component
        self.export_component.reset_filters()
        self.export_component.hide_export_ui()
        self.export_component.albums_scroll_area.hide()
        self.export_component.clear_albums_list()
        self.export_component.reset_export_state()

        # Hide/show appropriate UI sections
        self.export_component.hide()
        self.avatar_label.hide()
        self.logout_button.hide()
        self.user_info_container.hide()

        # Hide the entire header when logged out
        self.header_widget.hide()

        # Reset logs maximum height
        self.logs.setMaximumHeight(150)
        self.logs_container.setMaximumHeight(150)

        self.log("You have been logged out.")

        # Show login container
        self.login_container.show()