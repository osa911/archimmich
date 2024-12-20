from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QScrollArea, QFrame,
    QComboBox, QPushButton, QFileDialog, QWidget, QProgressBar, QSpacerItem, QSizePolicy, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QGuiApplication, QPixmap, QIcon

from src.ui.components.auto_scroll_text_edit import AutoScrollTextEdit
from src.utils.helpers import display_avatar, get_resource_path
from src.managers.login_manager import LoginManager
from src.managers.export_manager import ExportManager

VERSION = "0.0.1"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stop_requested = False
        self.login_manager = LoginManager()

        self.setWindowTitle("ArchImmich")
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        window_width = 850
        window_height = 850
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # UI Initialization
        self.setup_ui()

        self.buckets = []
        self.output_dir = ""

    def setup_ui(self):
        # Add Logo
        self.image_label = QLabel()
        pixmap = QPixmap(get_resource_path("src/resources/immich-logo.svg"))
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.image_label.setScaledContents(True)
        self.image_label.setFixedSize(132, 45)

        self.image_layout = QHBoxLayout()
        self.image_layout.addWidget(self.image_label)
        self.image_layout.setAlignment(Qt.AlignHCenter)
        self.layout.addLayout(self.image_layout)

        # Login Fields
        self.server_ip_label = QLabel("Server IP:")
        self.server_ip_field = QLineEdit()
        self.server_ip_field.setPlaceholderText("Enter server IP (e.g., http://192.168.1.1:2283)")
        self.layout.addWidget(self.server_ip_label)
        self.layout.addWidget(self.server_ip_field)

        self.api_key_label = QLabel("API Key:")
        self.api_key_field = QLineEdit()
        self.api_key_field.setPlaceholderText("Enter API key")
        self.layout.addWidget(self.api_key_label)
        self.layout.addWidget(self.api_key_field)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        self.layout.addWidget(self.login_button)

        # Avatar and Login Status
        self.avatar_text_container = QWidget()
        self.avatar_text_layout = QHBoxLayout(self.avatar_text_container)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(50, 50)
        self.avatar_label.hide()
        self.login_status = QLabel("")
        self.login_status.setStyleSheet("color: green; font-size: 14px;")
        self.avatar_text_layout.addWidget(self.avatar_label)
        self.avatar_text_layout.addWidget(self.login_status)
        self.avatar_text_layout.setContentsMargins(0, 0, 0, 0)
        self.avatar_text_layout.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.avatar_text_container)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)

        # Config Section
        self.config_section = QWidget()
        self.config_section.hide()
        self.config_layout = QVBoxLayout(self.config_section)
        self.is_archived_check = QCheckBox("Is Archived?")
        self.config_layout.addWidget(self.is_archived_check)
        self.with_partners_check = QCheckBox("With Partners?")
        self.config_layout.addWidget(self.with_partners_check)
        self.with_stacked_check = QCheckBox("With Stacked?")
        self.config_layout.addWidget(self.with_stacked_check)

        self.archive_size_label = QLabel("Archive Size (GB):")
        self.archive_size_field = QLineEdit()
        self.archive_size_field.setPlaceholderText("Enter size in GB")
        self.archive_size_field.setValidator(QIntValidator(1, 1024))
        self.archive_size_field.setText("4")
        self.config_layout.addWidget(self.archive_size_label)
        self.config_layout.addWidget(self.archive_size_field)

        self.size_combo_label = QLabel("Size:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["DAY", "MONTH"])
        self.size_combo.setCurrentText("MONTH")
        self.size_combo.currentIndexChanged.connect(self.update_download_by_combo)
        self.config_layout.addWidget(self.size_combo_label)
        self.config_layout.addWidget(self.size_combo)

        self.download_by_label = QLabel("Download Archives:")
        self.download_by_combo = QComboBox()
        self.download_by_combo.addItems(["Per Month", "Single Archive"])
        self.config_layout.addWidget(self.download_by_label)
        self.config_layout.addWidget(self.download_by_combo)

        self.layout.addWidget(self.config_section)

        # Output directory
        self.output_dir_label = QLabel("<span><span style='color: red;'>*</span> Output Directory:</span>")
        self.output_dir_button = QPushButton("Choose Directory")
        self.output_dir_button.clicked.connect(self.select_output_dir)
        self.config_layout.addWidget(self.output_dir_label)
        self.config_layout.addWidget(self.output_dir_button)

        self.fetch_button = QPushButton("Fetch Buckets")
        self.fetch_button.clicked.connect(self.fetch_buckets)
        self.fetch_button.hide()
        self.layout.addWidget(self.fetch_button)

        # Dividers
        self.divider1 = QFrame(self)
        self.divider1.setFrameShape(QFrame.HLine)
        self.divider1.setFrameShadow(QFrame.Sunken)
        self.divider1.setStyleSheet("background-color: lightgray;")
        self.divider1.hide()
        self.layout.addWidget(self.divider1)

        self.bucket_list_label = QLabel("Available Buckets:")
        self.layout.addWidget(self.bucket_list_label)
        self.bucket_list_label.hide()

        self.bucket_scroll_area = QScrollArea()
        self.bucket_scroll_area.setWidgetResizable(True)
        self.bucket_scroll_area.setMinimumHeight(160)
        self.bucket_list_widget = QWidget()
        self.bucket_list_layout = QVBoxLayout(self.bucket_list_widget)
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        self.bucket_list_layout.addWidget(self.select_all_checkbox)
        self.bucket_scroll_area.setWidget(self.bucket_list_widget)
        self.layout.addWidget(self.bucket_scroll_area)
        self.bucket_scroll_area.hide()

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.start_export)
        self.export_button.hide()
        self.layout.addWidget(self.export_button)

        self.current_download_progress_bar = QProgressBar(self)
        self.current_download_progress_bar.setRange(0, 100)
        self.current_download_progress_bar.setFormat("Current Download: 0%")
        self.current_download_progress_bar.setValue(0)
        self.current_download_progress_bar.setTextVisible(True)
        self.current_download_progress_bar.setStyleSheet("""
            QProgressBar {
                text-align: center;
                color: white;
                background-color: #333333;
                border: 1px solid #555555;
            }
            QProgressBar::chunk {
                background-color: #1f20ff;
            }
        """)
        self.current_download_progress_bar.hide()
        self.layout.addWidget(self.current_download_progress_bar)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        self.archives_section = QWidget()
        self.archives_layout = QHBoxLayout(self.archives_section)
        self.archives_label = QLabel("Downloaded Archives:")
        self.archives_layout.addWidget(self.archives_label)
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.archives_layout.addWidget(self.open_folder_button)
        self.archives_section.hide()
        self.layout.addWidget(self.archives_section)

        self.archives_display = AutoScrollTextEdit()
        self.archives_display.setPlaceholderText("Downloaded archives will appear here...")
        self.archives_display.hide()
        self.layout.addWidget(self.archives_display)

        self.stop_button = QPushButton("Stop Export")
        self.stop_button.setStyleSheet("background-color: '#f44336'; color: white;")
        self.stop_button.clicked.connect(self.stop_export)
        self.stop_button.hide()
        self.layout.addWidget(self.stop_button)

        self.divider2 = QFrame(self)
        self.divider2.setFrameShape(QFrame.HLine)
        self.divider2.setFrameShadow(QFrame.Sunken)
        self.divider2.setStyleSheet("background-color: '#ededed';")
        self.divider2.hide()
        self.layout.addWidget(self.divider2)

        self.logs = AutoScrollTextEdit()
        self.logs.setMinimumHeight(200)
        self.layout.addWidget(self.logs)

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.hide()
        self.layout.addWidget(self.logout_button)

    def log(self, message):
        self.logs.append(message)

    def stop_export(self):
        self.log("Stop requested. Stopping export process...")
        self.stop_requested = True

    def stop_flag(self):
        return self.stop_requested

    def update_download_by_combo(self):
        self.download_by_combo.clear()
        self.download_by_combo.addItems([f"Per {self.size_combo.currentText().capitalize()}", "Single Archive"])

    def logout(self):
        self.log("Logging out...")
        self.login_manager.logout()
        # Reset UI Elements
        self.login_status.setText("")
        self.login_status.setStyleSheet("color: red;")
        self.api_key_field.setText("")
        self.server_ip_field.setText("")
        self.config_section.hide()
        self.fetch_button.hide()
        self.export_button.hide()
        self.archives_section.hide()
        self.progress_bar.hide()
        self.avatar_label.hide()
        self.avatar_text_container.hide()
        self.bucket_list_label.hide()
        self.bucket_scroll_area.hide()
        self.divider1.hide()
        self.divider2.hide()
        self.archives_display.hide()
        self.current_download_progress_bar.hide()

        self.log("You have been logged out.")
        self.buckets = []
        self.output_dir = ""

        self.api_key_label.show()
        self.api_key_field.show()
        self.server_ip_label.show()
        self.server_ip_field.show()
        self.login_button.show()
        self.logout_button.hide()

    def get_archive_size_in_bytes(self):
        size_in_gb = self.archive_size_field.text()
        if not size_in_gb.isdigit():
            self.log("Invalid archive size input. Please enter a valid number in GB.")
            return None
        return int(size_in_gb) * 1024 ** 3

    def select_output_dir(self):
        self.output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if self.output_dir:
            self.log(f"Selected Output Directory: {self.output_dir}")
            self.output_dir_label.setText(
                f"<span><span style='color: red;'>*</span> Output Directory: <b>{self.output_dir}</b></span>"
            )
            self.output_dir_label.setStyleSheet("")
        else:
            self.log("No directory selected.")
            self.output_dir_label.setText("<span style='color: red;'>Output Directory * (required):</span>")

    def validate_login_inputs(self):
        is_valid = True
        self.api_key_field.setStyleSheet("")
        self.server_ip_field.setStyleSheet("")

        if not self.api_key_field.text().strip():
            self.log("Error: API key cannot be empty.")
            self.api_key_field.setStyleSheet("border: 2px solid red;")
            is_valid = False

        if not self.server_ip_field.text().strip():
            self.log("Error: Server IP cannot be empty.")
            self.server_ip_field.setStyleSheet("border: 2px solid red;")
            is_valid = False

        return is_valid

    def validate_bucket_inputs(self):
        is_valid = True
        self.archive_size_label.setStyleSheet("")
        self.archive_size_field.setStyleSheet("")
        self.output_dir_label.setText("<span><span style='color: red;'>*</span> Output Directory: </span>")

        archive_size_bytes = self.get_archive_size_in_bytes()
        if archive_size_bytes is None:
            self.log("Error: Archive size must be specified in GB.")
            self.archive_size_label.setStyleSheet("color: red; font-weight: bold;")
            self.archive_size_field.setStyleSheet("border: 2px solid red;")
            is_valid = False

        if not self.output_dir:
            self.log("Error: Output directory must be selected.")
            self.output_dir_label.setStyleSheet("color: red; font-weight: bold;")
            is_valid = False

        return is_valid

    def login(self):
        self.log("Attempting to login...")
        if not self.validate_login_inputs():
            return

        server_ip = self.server_ip_field.text().strip()
        api_key = self.api_key_field.text().strip()

        self.login_manager.set_credentials(server_ip, api_key)
        try:
            user = self.login_manager.login()
            user_name = user.get('name', 'Unknown User')
            user_email = user.get('email', 'Unknown Email')
            self.login_status.setText(
                f"<p>Logged in successfully.</p><p>User: <b>{user_name}</b></p><p>Email: <b>{user_email}</b></p>"
            )
            self.login_status.setStyleSheet("color: green; font-size: 14px;")
            self.log("Login successful!")
            self.log(f"User: {user_name} | Email: {user_email}")

            fetch_avatar = self.login_manager.get_avatar_fetcher()
            if fetch_avatar:
                display_avatar(self, fetch_avatar)
            self.avatar_label.show()
            self.avatar_text_container.show()

            self.api_key_label.hide()
            self.api_key_field.hide()
            self.server_ip_label.hide()
            self.server_ip_field.hide()
            self.login_button.hide()

            self.config_section.show()
            self.fetch_button.show()
            self.logout_button.show()
            self.archives_display.show()

        except Exception as e:
            self.log(f"Login failed: {str(e)}")
            self.login_status.setText("Login failed. Please check your API key or server.")
            self.login_status.setStyleSheet("color: red; font-size: 14px;")

    def get_user_input_values(self):
        return {
            "isArchived": self.is_archived_check.isChecked(),
            "size": self.size_combo.currentText(),
            "withPartners": self.with_partners_check.isChecked(),
            "withStacked": self.with_stacked_check.isChecked(),
        }

    def fetch_buckets(self):
        if not self.validate_bucket_inputs():
            return

        self.log("Fetching buckets...")
        inputs = self.get_user_input_values()
        api_manager = self.login_manager.api_manager
        self.export_manager = ExportManager(api_manager, self.logs, self.output_dir, self.stop_flag)

        self.buckets = self.export_manager.get_timeline_buckets(
            is_archived=inputs["isArchived"],
            size=inputs["size"],
            with_partners=inputs["withPartners"],
            with_stacked=inputs["withStacked"]
        )
        self.log(f"Buckets fetched successfully: {len(self.buckets)} buckets found.")
        self.populate_bucket_list(self.buckets)
        self.bucket_scroll_area.show()
        self.export_button.show()
        self.divider1.show()
        self.divider2.show()
        self.bucket_list_label.show()

    def populate_bucket_list(self, buckets):
        for i in reversed(range(self.bucket_list_layout.count())):
            widget = self.bucket_list_layout.itemAt(i).widget()
            if widget and widget != self.select_all_checkbox:
                widget.deleteLater()

        for bucket in buckets:
            bucket_name = self.export_manager.format_time_bucket(bucket['timeBucket'])
            asset_count = bucket['count']
            asset_text = "asset" if asset_count == 1 else "assets"
            checkbox = QCheckBox(f"{bucket_name} | ({asset_count} {asset_text})")
            checkbox.setObjectName(bucket['timeBucket'])
            self.bucket_list_layout.addWidget(checkbox)

    def toggle_select_all(self, state):
        for i in range(1, self.bucket_list_layout.count()):
            checkbox = self.bucket_list_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(state == Qt.Checked)

    def open_output_folder(self):
        if self.output_dir:
            import webbrowser
            webbrowser.open(f"file://{self.output_dir}")
            self.log(f"Opening output directory: {self.output_dir}")
        else:
            self.log("No output directory set. Please choose an output directory first.")

    def start_export(self):
        self.log("Starting export process...")
        self.stop_requested = False
        self.stop_button.show()

        selected_buckets = [
            self.bucket_list_layout.itemAt(i).widget().objectName()
            for i in range(1, self.bucket_list_layout.count())
            if isinstance(self.bucket_list_layout.itemAt(i).widget(), QCheckBox) and
            self.bucket_list_layout.itemAt(i).widget().isChecked()
        ]

        if not selected_buckets:
            self.log("Error: No buckets selected for export.")
            self.stop_button.hide()
            return

        total_buckets = len(selected_buckets)
        self.progress_bar.setRange(0, total_buckets)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Overall Progress: 0%")
        self.progress_bar.show()

        self.log(f"Total buckets to process: {total_buckets}")

        inputs = self.get_user_input_values()
        archive_size_bytes = self.get_archive_size_in_bytes()

        for i, time_bucket in enumerate(selected_buckets, start=1):
            if self.stop_flag():
                self.log("Export stopped by user.")
                break

            bucket_name = self.export_manager.format_time_bucket(time_bucket)
            self.log(f"Processing bucket {i}/{total_buckets}: {bucket_name}")

            assets = self.export_manager.get_timeline_bucket_assets(
                time_bucket,
                is_archived=inputs["isArchived"],
                size=inputs["size"],
                with_partners=inputs["withPartners"],
                with_stacked=inputs["withStacked"]
            )
            if self.stop_flag():
                self.log("Export stopped by user during image fetch.")
                break

            asset_ids = [a['id'] for a in assets]
            asset_count = len(asset_ids)
            if asset_count == 0:
                self.log(f"No images found for bucket: {bucket_name}")
                self.progress_bar.setValue(i)
                self.progress_bar.setFormat(f"Overall Progress: {int((i / total_buckets) * 100)}%")
                QApplication.processEvents()
                continue

            archive_info = self.export_manager.prepare_archive(asset_ids, archive_size_bytes)
            if self.stop_flag():
                self.log("Export stopped by user during archive preparation.")
                break

            total_size = archive_info["totalSize"]
            self.log(f"Preparing archive: Total size = {self.export_manager.format_size(total_size)} ({asset_count} assets)")

            self.export_manager.download_archive(asset_ids, bucket_name, total_size, self.current_download_progress_bar)
            if self.stop_flag():
                self.log("Export stopped by user during archive download.")
                break

            # Add archive info to the archive display
            self.archives_display.show()
            self.archives_display.append(f"{bucket_name}.zip")

            self.progress_bar.setValue(i)
            percentage = int((i / total_buckets) * 100)
            self.progress_bar.setFormat(f"Overall Progress: {percentage}%")
            QApplication.processEvents()

        self.log("Export completed successfully or stopped.")
        self.stop_button.hide()
        self.archives_section.show()