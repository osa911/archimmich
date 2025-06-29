from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QComboBox, QPushButton, QFileDialog, QProgressBar, QScrollArea, QFrame,
    QApplication, QRadioButton, QButtonGroup, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator

from src.ui.components.auto_scroll_text_edit import AutoScrollTextEdit
from src.ui.components.export_methods import ExportMethods
from src.ui.components.divider_factory import HorizontalDivider, VerticalDivider
from src.managers.export_manager import ExportManager

import os


class ExportComponent(QWidget, ExportMethods):
    # Signals
    export_finished = pyqtSignal()

    def __init__(self, login_manager, logger=None):
        super().__init__()
        self.login_manager = login_manager
        self.logger = logger
        self.stop_requested = False
        self.buckets = []
        self.output_dir = ""
        self.export_manager = None
        # Resume functionality state
        self.paused_export_state = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the two-column export component UI."""
        # Main horizontal layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 0, 10, 0)  # Remove main layout margins
        self.main_layout.setSpacing(0)  # No spacing, divider will handle separation
        self.setup_tab_widget(self.main_layout)

    def setup_tab_widget(self, layout: QVBoxLayout | QHBoxLayout):
        """Setup the tab widget."""
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.setup_timeline_tab(), "Timeline")
        self.tab_widget.addTab(self.setup_albums_tab(), "Albums")
        layout.addWidget(self.tab_widget)

    def setup_timeline_tab(self):
        """Setup the timeline tab."""
        timeline_tab = QWidget()
        timeline_layout = QHBoxLayout(timeline_tab)
        timeline_layout.setContentsMargins(10, 5, 10, 10)
        timeline_layout.setSpacing(10)
        # Create left sidebar (30% width)
        self.setup_sidebar(timeline_layout)

        # Add vertical divider with margins
        divider_container = VerticalDivider(
            margins={'left': 10, 'right': 5},
            with_container=True
        )
        timeline_layout.addWidget(divider_container)

        # Create right main area (70% width)
        self.setup_main_area(timeline_layout)
        return timeline_tab

    def setup_sidebar(self, layout: QVBoxLayout | QHBoxLayout):
        """Setup the left sidebar with controls."""
        sidebar = QWidget()
        sidebar.setMaximumWidth(285)  # Fixed max width for sidebar
        sidebar.setMinimumWidth(285)  # Minimum width for usability

        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)  # Small internal margins
        self.sidebar_layout.setSpacing(10)

        # Fetch button at the top
        self.init_fetch_button(self.sidebar_layout)

        # Add horizontal divider after fetch button
        self.sidebar_layout.addWidget(HorizontalDivider())

        # Configuration section
        self.init_config_section(self.sidebar_layout)

        # Add stretch to push everything to the top
        self.sidebar_layout.addStretch()

        # Add sidebar to main layout
        layout.addWidget(sidebar)

    def setup_main_area(self, layout: QVBoxLayout | QHBoxLayout):
        """Setup the right main area for content."""
        self.main_area = QWidget()
        self.main_area_layout = QVBoxLayout(self.main_area)
        self.main_area_layout.setContentsMargins(0, 0, 0, 0)  # Small internal margins

        # Bucket list section
        self.init_bucket_list()

        # Control buttons section (output directory and export)
        self.init_control_buttons()

        # Progress bars
        self.init_progress_bars()

        # Archives display
        self.init_archives_display()

        # Add main area to layout
        layout.addWidget(self.main_area)

    def init_config_section(self, layout: QVBoxLayout | QHBoxLayout):
        """Initialize configuration options in sidebar."""
        # Filter options
        filters_label = QLabel("Filters:")
        filters_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(filters_label)

        # Create 2-column layout for filters
        filters_container = QWidget()
        filters_layout = QHBoxLayout(filters_container)
        filters_layout.setContentsMargins(0, 0, 0, 0)

        # Left column
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.is_archived_check = QCheckBox("Is Archived?")
        left_layout.addWidget(self.is_archived_check)

        self.with_partners_check = QCheckBox("With Partners?")
        left_layout.addWidget(self.with_partners_check)

        self.is_favorite_check = QCheckBox("Is Favorite?")
        self.is_favorite_check.setChecked(False)
        left_layout.addWidget(self.is_favorite_check)

        # Right column
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.with_stacked_check = QCheckBox("With Stacked?")
        right_layout.addWidget(self.with_stacked_check)

        self.is_trashed_check = QCheckBox("Is Trashed?")
        self.is_trashed_check.setChecked(False)
        right_layout.addWidget(self.is_trashed_check)

        # Add empty label for alignment
        right_layout.addWidget(QLabel(""))  # Spacer to balance columns

        # Add columns to container
        filters_layout.addWidget(left_column)
        filters_layout.addWidget(right_column)

        layout.addWidget(filters_container)

        # Add horizontal divider after filters
        layout.addWidget(HorizontalDivider())

        # Visibility radio buttons
        self.init_visibility_radios()

        # Add horizontal divider after visibility
        layout.addWidget(HorizontalDivider())

        # Download type radio buttons
        self.init_download_radios()

        # Archive size
        self.archive_size_label = QLabel("Archive Size (GB):")
        self.archive_size_label.setStyleSheet("font-weight: bold;")
        self.archive_size_field = QLineEdit()
        self.archive_size_field.setPlaceholderText("Enter size in GB")
        self.archive_size_field.setValidator(QIntValidator(1, 1024))
        self.archive_size_field.setText("4")
        layout.addWidget(self.archive_size_label)
        layout.addWidget(self.archive_size_field)

    def init_visibility_radios(self):
        """Initialize visibility radio buttons."""
        visibility_label = QLabel("Visibility:")
        visibility_label.setStyleSheet("font-weight: bold;")
        self.sidebar_layout.addWidget(visibility_label)

        # Create button group for visibility
        self.visibility_group = QButtonGroup()

        # First row
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)

        self.visibility_none = QRadioButton("Not specified")
        self.visibility_none.setChecked(True)  # Default
        self.visibility_archive = QRadioButton("Archive")
        self.visibility_timeline = QRadioButton("Timeline")

        row1_layout.addWidget(self.visibility_none)
        row1_layout.addWidget(self.visibility_archive)
        row1_layout.addWidget(self.visibility_timeline)

        # Second row
        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)

        self.visibility_hidden = QRadioButton("Hidden")
        self.visibility_locked = QRadioButton("Locked")

        row2_layout.addWidget(self.visibility_hidden)
        row2_layout.addWidget(self.visibility_locked)
        row2_layout.addStretch()

        # Add to button group
        self.visibility_group.addButton(self.visibility_none, 0)
        self.visibility_group.addButton(self.visibility_archive, 1)
        self.visibility_group.addButton(self.visibility_timeline, 2)
        self.visibility_group.addButton(self.visibility_hidden, 3)
        self.visibility_group.addButton(self.visibility_locked, 4)

        self.sidebar_layout.addWidget(row1)
        self.sidebar_layout.addWidget(row2)

    def setup_albums_tab(self):
        albums_tab = QWidget()
        albums_layout = QVBoxLayout(albums_tab)
        albums_layout.setContentsMargins(10, 5, 10, 10)
        albums_layout.setSpacing(10)

        # Fetch albums button
        fetch_layout = QHBoxLayout()
        self.fetch_albums_button = QPushButton("Fetch Albums")
        self.fetch_albums_button.clicked.connect(self.fetch_albums)
        fetch_layout.addWidget(self.fetch_albums_button)
        fetch_layout.addStretch()
        albums_layout.addLayout(fetch_layout)
        albums_layout.addStretch()

        # Albums list
        self.albums_scroll_area = QScrollArea()
        self.albums_scroll_area.setWidgetResizable(True)
        self.albums_scroll_area.hide()
        albums_list_widget = QWidget()
        self.albums_list_layout = QVBoxLayout(albums_list_widget)

        self.select_all_albums_checkbox = QCheckBox("Select All")
        self.select_all_albums_checkbox.stateChanged.connect(self.toggle_select_all_albums)
        self.albums_list_layout.addWidget(self.select_all_albums_checkbox)

        self.albums_scroll_area.setWidget(albums_list_widget)
        albums_layout.addWidget(self.albums_scroll_area)

        albums_tab.setLayout(albums_layout)
        return albums_tab

    def clear_albums_list(self):
        while self.albums_list_layout.count() > 1:
            item = self.albums_list_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

    def fetch_albums(self):
        if self.albums_scroll_area.isHidden():
            self.albums_scroll_area.show()
            self.tab_widget.currentWidget().layout().setStretchFactor(self.albums_scroll_area, 1)

        # Clear existing albums
        self.clear_albums_list()

        # Fetch albums
        try:
            api_manager = self.login_manager.api_manager
            self.export_manager = ExportManager(api_manager, self.logger, "", self.stop_flag)
            self.albums = self.export_manager.get_albums()

            # Add albums to the list or show no albums message
            if self.albums:
                for album in self.albums:
                    checkbox = QCheckBox(f"{album['albumName']} ({album['assetCount']} assets)")
                    checkbox.setChecked(self.select_all_albums_checkbox.isChecked())
                    self.albums_list_layout.addWidget(checkbox)
            else:
                no_albums_label = QLabel("No albums found")
                no_albums_label.setStyleSheet("color: gray; padding: 10px;")
                no_albums_label.setAlignment(Qt.AlignCenter)
                self.albums_list_layout.addWidget(no_albums_label)
                # Hide select all checkbox when no albums
                self.select_all_albums_checkbox.hide()

        except Exception as e:
            if self.logger:
                self.logger.append(f"Error fetching albums: {str(e)}")
            # Show error message in the UI
            error_label = QLabel(f"Error fetching albums: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setWordWrap(True)
            self.albums_list_layout.addWidget(error_label)
            # Hide select all checkbox on error
            self.select_all_albums_checkbox.hide()

    def toggle_select_all_albums(self, state):
        for i in range(1, self.albums_list_layout.count()):
            checkbox = self.albums_list_layout.itemAt(i).widget()
            if checkbox:
                checkbox.setChecked(state == Qt.Checked)

    def get_selected_albums(self):
        selected_albums = []
        for i in range(1, self.albums_list_layout.count()):
            checkbox = self.albums_list_layout.itemAt(i).widget()
            if checkbox and checkbox.isChecked():
                album = self.albums[i - 1]
                selected_albums.append(album)
        return selected_albums

    def init_download_radios(self):
        """Initialize download type radio buttons."""
        download_label = QLabel("Download Archives:")
        download_label.setStyleSheet("font-weight: bold;")
        self.sidebar_layout.addWidget(download_label)

        # Create button group for download type
        self.download_group = QButtonGroup()

        download_layout = QHBoxLayout()
        self.download_per_bucket = QRadioButton("Per Bucket")
        self.download_single = QRadioButton("Single Archive")
        self.download_per_bucket.setChecked(True)

        download_layout.addWidget(self.download_per_bucket)
        download_layout.addWidget(self.download_single)
        download_layout.addStretch()

        # Add to button group
        self.download_group.addButton(self.download_per_bucket, 0)
        self.download_group.addButton(self.download_single, 1)

        download_widget = QWidget()
        download_widget.setLayout(download_layout)
        self.sidebar_layout.addWidget(download_widget)

    def get_visibility_value(self):
        """Get the selected visibility value."""
        if self.visibility_none.isChecked():
            return ""
        elif self.visibility_archive.isChecked():
            return "archive"
        elif self.visibility_timeline.isChecked():
            return "timeline"
        elif self.visibility_hidden.isChecked():
            return "hidden"
        elif self.visibility_locked.isChecked():
            return "locked"
        return ""

    def get_download_option(self):
        """Get the selected download option."""
        if self.download_per_bucket.isChecked():
            return "Per Bucket"
        else:
            return "Single Archive"

    def init_bucket_list(self):
        """Initialize bucket list display in main area."""
        # Create horizontal layout for bucket list label and order button
        bucket_header_layout = QHBoxLayout()

        self.bucket_list_label = QLabel("Available Buckets:")
        self.bucket_list_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.bucket_list_label.hide()
        bucket_header_layout.addWidget(self.bucket_list_label)

        # Add stretch to push order button to the right
        bucket_header_layout.addStretch()

        # Order section on the right
        self.order_label = QLabel("Order by:")
        self.order_label.hide()
        bucket_header_layout.addWidget(self.order_label)

        self.order_button = QPushButton("↓") # Start with descending
        self.order_button.setMaximumWidth(30)
        self.order_button.setToolTip("Toggle sort order (↓ descending/newest first, ↑ ascending/oldest first)")
        self.order_button.clicked.connect(self.toggle_order)
        self.order_button.hide()
        bucket_header_layout.addWidget(self.order_button)

        self.main_area_layout.addLayout(bucket_header_layout)

        self.bucket_scroll_area = QScrollArea()
        self.bucket_scroll_area.setWidgetResizable(True)
        self.bucket_scroll_area.setMinimumHeight(200)
        self.bucket_list_widget = QWidget()
        self.bucket_list_layout = QVBoxLayout(self.bucket_list_widget)

        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        self.bucket_list_layout.addWidget(self.select_all_checkbox)

        self.bucket_scroll_area.setWidget(self.bucket_list_widget)
        self.bucket_scroll_area.hide()
        self.main_area_layout.addWidget(self.bucket_scroll_area)

    def init_fetch_button(self, layout: QVBoxLayout | QHBoxLayout):
        """Initialize fetch button at the top of main area."""
        fetch_layout = QHBoxLayout()
        self.fetch_button = QPushButton("Fetch Buckets")
        self.fetch_button.clicked.connect(self.fetch_buckets)
        fetch_layout.addWidget(self.fetch_button)
        fetch_layout.addStretch()  # Push to left
        layout.addLayout(fetch_layout)

    def init_control_buttons(self):
        """Initialize output directory and export controls in main area."""
        # Add some spacing
        self.main_area_layout.addWidget(QLabel("")) # Spacer

        self.output_dir_label = QLabel("<span><span style='color: red;'>*</span> Select output directory:</span>")
        self.output_dir_label.hide()
        self.main_area_layout.addWidget(self.output_dir_label)

        # Output directory button row
        output_layout = QHBoxLayout()
        self.output_dir_button = QPushButton("Choose Directory")
        self.output_dir_button.clicked.connect(self.select_output_dir)
        self.output_dir_button.hide()
        output_layout.addWidget(self.output_dir_button)
        output_layout.addStretch() # Push to left
        self.main_area_layout.addLayout(output_layout)

        # Export buttons row (no title)
        export_layout = QHBoxLayout()

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.start_export)
        self.export_button.hide()
        export_layout.addWidget(self.export_button)

        self.stop_button = QPushButton("Stop Export")
        self.stop_button.setStyleSheet("background-color: '#f44336'; color: white;")
        self.stop_button.clicked.connect(self.stop_export)
        self.stop_button.hide()
        export_layout.addWidget(self.stop_button)

        self.resume_button = QPushButton("Resume Export")
        self.resume_button.setStyleSheet("background-color: '#4CAF50'; color: white;")
        self.resume_button.clicked.connect(self.resume_export)
        self.resume_button.hide()
        export_layout.addWidget(self.resume_button)

        # Add stretch to push buttons to the left
        export_layout.addStretch()
        self.main_area_layout.addLayout(export_layout)

    def init_progress_bars(self):
        """Initialize progress bars in main area."""
        self.current_download_progress_bar = QProgressBar()
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
        self.main_area_layout.addWidget(self.current_download_progress_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.main_area_layout.addWidget(self.progress_bar)

    def init_archives_display(self):
        """Initialize archives display section in main area."""
        self.archives_section = QWidget()
        self.archives_layout = QHBoxLayout(self.archives_section)

        self.archives_label = QLabel("Downloaded Archives:")
        self.archives_label.setStyleSheet("font-weight: bold;")
        self.archives_layout.addWidget(self.archives_label)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.archives_layout.addWidget(self.open_folder_button)

        self.archives_section.hide()
        self.main_area_layout.addWidget(self.archives_section)

        self.archives_display = AutoScrollTextEdit()
        self.archives_display.setPlaceholderText("Downloaded archives will appear here...")
        self.archives_display.setMaximumHeight(150)  # Limit height
        self.archives_display.hide()  # Initially hidden
        self.main_area_layout.addWidget(self.archives_display)

    def fetch_buckets(self):
        """Fetch buckets from the API."""
        if not self.validate_fetch_inputs():
            return

        try:
            if self.logger:
                self.logger.append("Fetching buckets...")
            inputs = self.get_user_input_values()
            api_manager = self.login_manager.api_manager
            # Don't require output_dir for fetching buckets
            self.export_manager = ExportManager(api_manager, self.logger, "", self.stop_flag)

            # Check if server supports Range headers and hide resume button if not
            self.check_and_hide_resume_button_if_needed()

            # Clear existing buckets before fetching new ones
            self.buckets = []

            self.buckets = self.export_manager.get_timeline_buckets(
                is_archived=inputs["is_archived"],
                with_partners=inputs["with_partners"],
                with_stacked=inputs["with_stacked"],
                visibility=inputs["visibility"],
                is_favorite=inputs["is_favorite"],
                is_trashed=inputs["is_trashed"],
                order=inputs["order"]
            )

            if not self.buckets:
                if self.logger:
                    self.logger.append("No buckets found.")

                # Clear and hide bucket list UI when no buckets found
                self.clear_bucket_list()
                self.bucket_scroll_area.hide()
                self.bucket_list_label.hide()
                self.order_label.hide()
                self.order_button.hide()

                # Hide output directory and export sections
                self.output_dir_label.hide()
                self.output_dir_button.hide()
                self.export_button.hide()

                # Hide archives display
                self.archives_display.hide()
                return

            if self.logger:
                self.logger.append(f"Buckets fetched successfully: {len(self.buckets)} buckets found.")

            # Clear existing bucket list widgets before populating
            for i in reversed(range(self.bucket_list_layout.count())):
                widget = self.bucket_list_layout.itemAt(i).widget()
                if widget and widget != self.select_all_checkbox:
                    widget.deleteLater()

            self.populate_bucket_list(self.buckets)
            self.bucket_scroll_area.show()
            self.bucket_list_label.show()

            # Show order controls
            self.order_label.show()
            self.order_button.show()

            # Show output directory and export sections
            self.output_dir_label.show()
            self.output_dir_button.show()
            self.export_button.show()

            # Show archives display area
            self.archives_display.show()

        except Exception as e:
            error_msg = str(e).lower()
            if not ("api error" in error_msg):
                if self.logger:
                    self.logger.append(f"Error fetching buckets: {str(e)}")
            # Reset UI state in case of error
            self.buckets = []
            self.bucket_scroll_area.hide()
            self.bucket_list_label.hide()

            # Hide order controls
            self.order_label.hide()
            self.order_button.hide()

            # Hide output directory and export sections
            self.output_dir_label.hide()
            self.output_dir_button.hide()
            self.export_button.hide()

            # Hide archives display
            self.archives_display.hide()

    def start_export(self):
        """Start the export process."""
        # Validate export inputs (including output directory)
        if not self.validate_export_inputs():
            return

        if self.logger:
            self.logger.append("Starting export process...")
        self.stop_requested = False
        # Clear any existing paused state when starting fresh
        self.paused_export_state = None
        self.export_button.hide()
        self.resume_button.hide()  # Hide resume button when starting new export
        self.stop_button.show()

        # Hide output directory button during export to prevent changes
        self.output_dir_button.hide()

        selected_buckets = self.get_selected_buckets()
        if not selected_buckets:
            if self.logger:
                self.logger.append("Error: No buckets selected for export.")
            self.stop_button.hide()
            self.export_button.show()
            return

        # Update export manager with correct output directory
        api_manager = self.login_manager.api_manager
        self.export_manager = ExportManager(api_manager, self.logger, self.output_dir, self.stop_flag)

        # Check if server supports Range headers and hide resume button if not
        self.check_and_hide_resume_button_if_needed()

        self.setup_progress_bar(len(selected_buckets))
        if self.logger:
            self.logger.append(f"Total buckets to process: {len(selected_buckets)}")

        inputs = self.get_user_input_values()
        archive_size_bytes = self.get_archive_size_in_bytes()
        download_option = self.get_download_option()

        if download_option.startswith("Per"):
            self.process_buckets_individually(selected_buckets, inputs, archive_size_bytes)
        elif download_option == "Single Archive":
            self.process_all_buckets_combined(selected_buckets, inputs, archive_size_bytes)

        self.finalize_export()

    def process_buckets_individually(self, selected_buckets, inputs, archive_size_bytes):
        """Process each bucket individually."""
        # Check for existing archives before starting
        bucket_names = [self.export_manager.format_time_bucket(tb) for tb in selected_buckets]
        existing_files, missing_files = self.export_manager.check_existing_archives(bucket_names)

        if existing_files and self.logger:
            self.logger.append(f"Existing files will be skipped if they match expected size.")

        for i, time_bucket in enumerate(selected_buckets, start=1):
            if self.stop_flag():
                # Save current state for resume
                self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Per Bucket", i - 1)
                if self.logger:
                    self.logger.append("Export paused by user.")
                self.show_resume_button()
                return

            bucket_name = self.export_manager.format_time_bucket(time_bucket)
            if self.logger:
                self.logger.append(f"Processing bucket {i}/{len(selected_buckets)}: {bucket_name}")

            try:
                asset_ids = self.fetch_assets_for_bucket(time_bucket, inputs)
                if not asset_ids:
                    if self.logger:
                        self.logger.append(f"No assets found for bucket: {bucket_name}")
                    self.update_progress_bar(i, len(selected_buckets))
                    continue

                download_result = self.download_and_save_archive(asset_ids, bucket_name, archive_size_bytes)
                if download_result == "paused":
                    # Save state and show resume button
                    self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Per Bucket", i - 1)
                    self.show_resume_button()
                    return

            except Exception as e:
                if self.logger:
                    self.logger.append(f"Error processing bucket {bucket_name}: {str(e)}")

            self.update_progress_bar(i, len(selected_buckets))
            QApplication.processEvents()

        # Clear paused state on successful completion
        self.paused_export_state = None

    def process_all_buckets_combined(self, selected_buckets, inputs, archive_size_bytes):
        """Process all buckets into a single combined archive."""
        # Check if combined archive already exists
        existing_files, missing_files = self.export_manager.check_existing_archives(["Combined_Archive"])
        if existing_files and self.logger:
            self.logger.append(f"Combined archive will be skipped if it matches expected size.")

        all_asset_ids = []
        try:
            for time_bucket in selected_buckets:
                if self.stop_flag():
                    # Save current state for resume
                    self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Single Archive", 0)
                    if self.logger:
                        self.logger.append("Export paused by user.")
                    self.show_resume_button()
                    return

                asset_ids = self.fetch_assets_for_bucket(time_bucket, inputs)
                all_asset_ids.extend(asset_ids)

            if not all_asset_ids:
                if self.logger:
                    self.logger.append("No assets found in selected buckets.")
                return

            download_result = self.download_and_save_archive(all_asset_ids, "Combined_Archive", archive_size_bytes)
            if download_result == "paused":
                # Save state and show resume button
                self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Single Archive", 0)
                self.show_resume_button()
                return
        except Exception as e:
            if self.logger:
                self.logger.append(f"Error processing combined archive: {str(e)}")

        # Clear paused state on successful completion
        self.paused_export_state = None

    def fetch_assets_for_bucket(self, time_bucket, inputs):
        """Fetch assets for a specific bucket."""
        assets = self.export_manager.get_timeline_bucket_assets(
            time_bucket,
            is_archived=inputs["is_archived"],
            with_partners=inputs["with_partners"],
            with_stacked=inputs["with_stacked"],
            visibility=inputs["visibility"],
            is_favorite=inputs["is_favorite"],
            is_trashed=inputs["is_trashed"],
            order=inputs["order"]
        )
        if self.stop_flag():
            if self.logger:
                self.logger.append("Export stopped by user during image fetch.")
            return []
        return [asset["id"] for asset in assets]

    def download_and_save_archive(self, asset_ids, archive_name, archive_size_bytes):
        """Download and save an archive with the given asset IDs."""
        try:
            archive_info = self.export_manager.prepare_archive(asset_ids, archive_size_bytes)
            total_size = archive_info["totalSize"]
            if total_size == 0:
                if self.logger:
                    self.logger.append(f"Failed to prepare archive for {archive_name}")
                return "error"

            if self.logger:
                self.logger.append(f"Preparing archive: Total size = {self.export_manager.format_size(total_size)}")

            download_result = self.export_manager.download_archive(
                asset_ids, archive_name, total_size, self.current_download_progress_bar
            )

            if download_result == "paused":
                return "paused"
            elif download_result == "completed":
                self.archives_display.show()
                self.archives_display.append(f"{archive_name}.zip")
                return "completed"
            else:
                return "error"
        except Exception as e:
            if self.logger:
                self.logger.append(f"Error preparing archive for {archive_name}: {str(e)}")
            return "error"

    def clear_bucket_list(self):
        """Clear all bucket checkboxes from the list."""
        for i in reversed(range(self.bucket_list_layout.count())):
            widget = self.bucket_list_layout.itemAt(i).widget()
            if widget and widget != self.select_all_checkbox:
                widget.deleteLater()

        # Reset select all checkbox
        self.select_all_checkbox.setChecked(False)

    def resume_export(self):
        """Resume a paused export."""
        if not self.paused_export_state:
            if self.logger:
                self.logger.append("No paused export to resume.")
            return

        if self.logger:
            self.logger.append("Resuming export process...")

        # Hide resume button and show stop button
        self.resume_button.hide()
        self.stop_button.show()

        # Hide output directory button during export to prevent changes
        self.output_dir_button.hide()

        # Reset stop flag
        self.stop_requested = False

        # Resume from where we left off
        state = self.paused_export_state
        selected_buckets = state['selected_buckets']
        inputs = state['inputs']
        archive_size_bytes = state['archive_size_bytes']
        download_option = state['download_option']
        current_bucket_index = state.get('current_bucket_index', 0)

        # Update export manager with correct output directory
        api_manager = self.login_manager.api_manager
        self.export_manager = ExportManager(api_manager, self.logger, self.output_dir, self.stop_flag)

        # Check if server supports Range headers and hide resume button if not
        self.check_and_hide_resume_button_if_needed()

        if self.logger:
            self.logger.append(f"Resuming from bucket {current_bucket_index + 1}/{len(selected_buckets)}")

        if download_option.startswith("Per"):
            self.process_buckets_individually_resume(selected_buckets, inputs, archive_size_bytes, current_bucket_index)
        elif download_option == "Single Archive":
            # For single archive, we resume by retrying the download
            self.process_all_buckets_combined(selected_buckets, inputs, archive_size_bytes)

        # Only finalize if not paused
        if not self.paused_export_state:
            self.finalize_export()

    def process_buckets_individually_resume(self, selected_buckets, inputs, archive_size_bytes, start_index=0):
        """Process buckets individually starting from a specific index for resume."""
        for i, time_bucket in enumerate(selected_buckets[start_index:], start=start_index + 1):
            if self.stop_flag():
                # Save current state for resume
                self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Per Bucket", i - 1)
                if self.logger:
                    self.logger.append("Export paused by user.")
                return

            bucket_name = self.export_manager.format_time_bucket(time_bucket)
            if self.logger:
                self.logger.append(f"Processing bucket {i}/{len(selected_buckets)}: {bucket_name}")

            try:
                asset_ids = self.fetch_assets_for_bucket(time_bucket, inputs)
                if not asset_ids:
                    if self.logger:
                        self.logger.append(f"No assets found for bucket: {bucket_name}")
                    self.update_progress_bar(i, len(selected_buckets))
                    continue

                download_result = self.download_and_save_archive(asset_ids, bucket_name, archive_size_bytes)
                if download_result == "paused":
                    # Save state and show resume button
                    self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Per Bucket", i - 1)
                    self.show_resume_button()
                    return

            except Exception as e:
                if self.logger:
                    self.logger.append(f"Error processing bucket {bucket_name}: {str(e)}")

            self.update_progress_bar(i, len(selected_buckets))
            QApplication.processEvents()

        # Clear paused state on successful completion
        self.paused_export_state = None

    def save_export_state(self, selected_buckets, inputs, archive_size_bytes, download_option, current_bucket_index):
        """Save the current export state for resuming later."""
        self.paused_export_state = {
            'selected_buckets': selected_buckets,
            'inputs': inputs,
            'archive_size_bytes': archive_size_bytes,
            'download_option': download_option,
            'current_bucket_index': current_bucket_index,
            'output_dir': self.output_dir
        }

    def show_resume_button(self):
        """Show resume button and hide stop button, but only if server supports Range headers."""
        self.stop_button.hide()

        # Show output directory button when export is paused
        self.output_dir_button.show()

        # Check if server supports Range headers
        if self.export_manager:
            # server_url = getattr(self.export_manager.api_manager, 'server_url', 'unknown')

            # Check cache first - this is the most reliable source
            # server_supports_range = False  # Default
            # if hasattr(self.export_manager, 'range_support_cache') and server_url in self.export_manager.range_support_cache:
            #     server_supports_range = self.export_manager.range_support_cache[server_url]
            # else:
            #     # Fallback to the method check
            #     server_supports_range = self.export_manager.check_range_header_support(server_url)

            # if server_supports_range:
            #     self.resume_button.show()
            #     if self.logger:
            #         self.logger.append("Export paused. Click 'Resume Export' to continue.")
            # else:
            # Server doesn't support Range headers - show export button instead
            self.export_button.show()
            if self.logger:
                self.logger.append("Export paused. Server doesn't support resume functionality.")
                self.logger.append("Click 'Export' to restart. Already downloaded files will be skipped automatically.")
        else:
            # Fallback if export_manager is not available
            self.export_button.show()
            if self.logger:
                self.logger.append("Export paused. Click 'Export' to restart.")

    def finalize_export(self):
        """Finalize the export process."""
        if not self.paused_export_state:
            # Only finalize if not paused
            self.stop_button.hide()
            self.export_button.show()
            self.archives_section.show()
            self.current_download_progress_bar.hide()
            self.progress_bar.hide()

            # Show output directory button when export is finished
            self.output_dir_button.show()

            self.export_finished.emit()

    def check_for_resumable_downloads(self):
        """Check if there are any downloads that can be resumed."""
        if not self.output_dir or not self.export_manager:
            return False

        resume_dir = os.path.join(self.output_dir, ".archimmich_resume")
        if not os.path.exists(resume_dir):
            return False

        # Check for any .resume.json files
        import glob
        resume_files = glob.glob(os.path.join(resume_dir, "*.resume.json"))
        return len(resume_files) > 0

    def check_and_hide_resume_button_if_needed(self):
        """Check if server supports Range headers and hide resume button if not."""
        if self.export_manager:
            server_url = getattr(self.export_manager.api_manager, 'server_url', 'unknown')

            # Check cache first - this is the most reliable source
            server_supports_range = True  # Default
            if hasattr(self.export_manager, 'range_support_cache') and server_url in self.export_manager.range_support_cache:
                server_supports_range = self.export_manager.range_support_cache[server_url]
            else:
                # Fallback to the method check
                server_supports_range = self.export_manager.check_range_header_support(server_url)

            if not server_supports_range:
                # Server doesn't support Range headers - hide resume button permanently
                self.resume_button.hide()
                if self.logger:
                    self.logger.append("Note: Resume functionality disabled - server doesn't support Range headers.")

    def show_resumable_downloads_info(self):
        """Show information about resumable downloads."""
        if self.check_for_resumable_downloads() and self.logger:
            self.logger.append("Found resumable downloads. Individual files can be resumed automatically.")

