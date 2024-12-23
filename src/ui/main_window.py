from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QScrollArea, QFrame,
    QComboBox, QPushButton, QFileDialog, QWidget, QProgressBar, QSpacerItem, QSizePolicy, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QGuiApplication, QPixmap

from src.ui.components.auto_scroll_text_edit import AutoScrollTextEdit
from src.utils.helpers import display_avatar, get_resource_path, load_settings
from src.managers.login_manager import LoginManager
from src.managers.export_manager import ExportManager

VERSION = "0.0.2"

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
        self.load_saved_settings()

        self.buckets = []
        self.output_dir = ""

    def load_saved_settings(self):
        # Load saved settings on startup
        server_ip, api_key = load_settings()
        if server_ip and api_key:
            self.server_ip_field.setText(server_ip)
            self.api_key_field.setText(api_key)
            self.is_remember_me_checkbox.setChecked(True)

    def init_main_logo_layout(self):
        # Add Logo
        image_label = QLabel()
        pixmap = QPixmap(get_resource_path("src/resources/immich-logo.svg"))
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        image_label.setScaledContents(True)
        image_label.setFixedSize(132, 45)

        layout = QHBoxLayout()
        layout.addWidget(image_label)
        layout.setAlignment(Qt.AlignHCenter)
        return layout

    def init_login_widget(self):
        # Login Fields
        self.login_widget = QWidget()
        self.login_layout = QVBoxLayout(self.login_widget)

        # Server IP Field
        self.server_ip_label = QLabel("Server IP:")
        self.server_ip_field = QLineEdit()
        self.server_ip_field.setPlaceholderText("Enter server IP (e.g., http://192.168.1.1:2283)")
        self.login_layout.addWidget(self.server_ip_label)
        self.login_layout.addWidget(self.server_ip_field)

        # API Key Field
        self.api_key_label = QLabel("API Key:")
        self.api_key_field = QLineEdit()
        self.api_key_field.setPlaceholderText("Enter API key")
        self.login_layout.addWidget(self.api_key_label)
        self.login_layout.addWidget(self.api_key_field)

        # Remember Me Checkbox
        self.is_remember_me_checkbox = QCheckBox("Remember me")
        self.login_layout.addWidget(self.is_remember_me_checkbox)

        # Login Button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        self.login_layout.addWidget(login_button)

        return self.login_widget

    def reset_login_fields(self):
        self.api_key_field.setText("")
        self.server_ip_field.setText("")
        self.is_remember_me_checkbox.setChecked(False)

    def setup_ui(self):
        self.layout.addLayout(self.init_main_logo_layout())
        self.layout.addWidget(self.init_login_widget())

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
        self.divider1.setStyleSheet("background-color: '#ededed';")
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

        self.stop_button = QPushButton("Stop Export")
        self.stop_button.setStyleSheet("background-color: '#f44336'; color: white;")
        self.stop_button.clicked.connect(self.stop_export)
        self.stop_button.hide()
        self.layout.addWidget(self.stop_button)

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
        self.stop_button.hide()
        self.export_button.show()

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
        self.reset_login_fields()
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

        self.login_widget.show()
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
            self.output_dir_label.setText("<span style='color: red;'>* Output Directory (required):</span>")

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

        self.login_manager.set_credentials(server_ip, api_key, self.is_remember_me_checkbox.isChecked())
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

            self.login_widget.hide()

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
        inputs = self.get_user_input_values()

        for bucket in buckets:
            bucket_name = self.export_manager.format_time_bucket(bucket['timeBucket'], inputs["size"])
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

    def get_selected_buckets(self):
        return [
            self.bucket_list_layout.itemAt(i).widget().objectName()
            for i in range(1, self.bucket_list_layout.count())
            if isinstance(self.bucket_list_layout.itemAt(i).widget(), QCheckBox) and
            self.bucket_list_layout.itemAt(i).widget().isChecked()
        ]

    def setup_progress_bar(self, total):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Overall Progress: 0%")
        self.progress_bar.show()

    def process_buckets_individually(self, selected_buckets, inputs, archive_size_bytes):
        for i, time_bucket in enumerate(selected_buckets, start=1):
            if self.stop_flag():
                self.log("Export stopped by user.")
                break

            bucket_name = self.export_manager.format_time_bucket(time_bucket, inputs["size"])
            self.log(f"Processing bucket {i}/{len(selected_buckets)}: {bucket_name}")

            asset_ids = self.fetch_assets_for_bucket(time_bucket, inputs)
            if not asset_ids:
                self.log(f"No assets found for bucket: {bucket_name}")
                self.update_progress_bar(i, len(selected_buckets))
                continue

            self.download_and_save_archive(asset_ids, bucket_name, archive_size_bytes)
            self.update_progress_bar(i, len(selected_buckets))

    def process_all_buckets_combined(self, selected_buckets, inputs, archive_size_bytes):
        all_asset_ids = []
        for time_bucket in selected_buckets:
            asset_ids = self.fetch_assets_for_bucket(time_bucket, inputs)
            all_asset_ids.extend(asset_ids)

        if not all_asset_ids:
            self.log("No assets found in selected buckets.")
            return

        self.download_and_save_archive(all_asset_ids, "Combined_Archive", archive_size_bytes)

    def fetch_assets_for_bucket(self, time_bucket, inputs):
        assets = self.export_manager.get_timeline_bucket_assets(
            time_bucket,
            is_archived=inputs["isArchived"],
            size=inputs["size"],
            with_partners=inputs["withPartners"],
            with_stacked=inputs["withStacked"]
        )
        if self.stop_flag():
            self.log("Export stopped by user during image fetch.")
            return []
        return [a['id'] for a in assets]

    def download_and_save_archive(self, asset_ids, archive_name, archive_size_bytes):
        archive_info = self.export_manager.prepare_archive(asset_ids, archive_size_bytes)
        total_size = archive_info["totalSize"]
        self.log(f"Preparing archive: Total size = {self.export_manager.format_size(total_size)}")

        self.export_manager.download_archive(
            asset_ids, archive_name, total_size, self.current_download_progress_bar
        )
        self.archives_display.show()
        self.archives_display.append(f"{archive_name}.zip")

    def update_progress_bar(self, current, total):
        self.progress_bar.setValue(current)
        percentage = int((current / total) * 100)
        self.progress_bar.setFormat(f"Overall Progress: {percentage}%")
        QApplication.processEvents()

    def finalize_export(self):
        self.log("Export completed successfully or stopped.")
        self.stop_button.hide()
        self.export_button.show()
        self.archives_section.show()

    def start_export(self):
        self.log("Starting export process...")
        self.stop_requested = False
        self.export_button.hide()
        self.stop_button.show()

        selected_buckets = self.get_selected_buckets()
        if not selected_buckets:
            self.log("Error: No buckets selected for export.")
            self.stop_button.hide()
            self.export_button.show()
            return

        self.setup_progress_bar(len(selected_buckets))
        self.log(f"Total buckets to process: {len(selected_buckets)}")

        inputs = self.get_user_input_values()
        archive_size_bytes = self.get_archive_size_in_bytes()
        download_option = self.download_by_combo.currentText()

        if download_option == f"Per {inputs['size'].capitalize()}":
            self.process_buckets_individually(selected_buckets, inputs, archive_size_bytes)
        elif download_option == "Single Archive":
            self.process_all_buckets_combined(selected_buckets, inputs, archive_size_bytes)

        self.finalize_export()