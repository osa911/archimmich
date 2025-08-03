from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox,
    QPushButton, QProgressBar, QScrollArea,
    QApplication, QRadioButton, QButtonGroup, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator, QIcon

from src.ui.components.auto_scroll_text_edit import AutoScrollTextEdit
from src.ui.components.export_methods import ExportMethods
from src.ui.components.divider_factory import HorizontalDivider, VerticalDivider
from src.managers.export_manager import ExportManager
from src.utils.helpers import get_resource_path

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
        self.export_manager = None
        # Resume functionality state
        self.paused_export_state = None
        self.export_in_progress = False
        self.setup_ui()

    def reset_export_state(self):
        """Reset the export state and enable tab switching."""
        self.export_in_progress = False
        if hasattr(self, 'tab_widget'):
            self.tab_widget.tabBar().setEnabled(True)

    def setup_ui(self):
        # Main horizontal layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(15, 0, 15, 5)  # Remove main layout margins
        self.main_layout.setSpacing(0)  # No spacing, divider will handle separation
        self.setup_tab_widget(self.main_layout)

    def setup_tab_widget(self, container_layout: QVBoxLayout | QHBoxLayout):
        """Setup the tab widget."""
        self.tab_widget = QTabWidget()
        timeline_icon = QIcon(get_resource_path("src/resources/icons/timeline-icon.svg"))
        albums_icon = QIcon(get_resource_path("src/resources/icons/albums-icon.svg"))
        self.tab_widget.addTab(self.setup_timeline_tab(), timeline_icon, "Timeline")
        self.tab_widget.addTab(self.setup_albums_tab(), albums_icon, "Albums")
        container_layout.addWidget(self.tab_widget)

    def setup_timeline_tab(self):
        """Setup the timeline tab."""
        timeline_tab = QWidget()
        timeline_layout = QHBoxLayout(timeline_tab)
        timeline_layout.setContentsMargins(10, 5, 10, 10)
        timeline_layout.setSpacing(10)
        # Create left sidebar (30% width)
        self.setup_timeline_sidebar(timeline_layout)

        # Add vertical divider with margins
        divider_container = VerticalDivider(
            margins={'left': 10, 'right': 5},
            with_container=True
        )
        timeline_layout.addWidget(divider_container)

        # Create right main area (70% width)
        self.setup_timeline_main_area(timeline_layout)
        return timeline_tab

    def setup_timeline_sidebar(self, container_layout: QVBoxLayout | QHBoxLayout):
        """Setup the left sidebar with controls."""
        sidebar = QWidget()
        sidebar.setMaximumWidth(285)  # Fixed max width for sidebar
        sidebar.setMinimumWidth(285)  # Minimum width for usability

        self.sidebar_layout = QVBoxLayout(sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)  # Small internal margins
        self.sidebar_layout.setSpacing(10)

        # Fetch button at the top
        self.init_fetch_button(self.sidebar_layout, "Fetch Buckets", self.fetch_buckets)

        # Add horizontal divider after fetch button
        self.sidebar_layout.addWidget(HorizontalDivider())

        # Configuration section
        self.init_config_section(self.sidebar_layout)

        # Add stretch to push everything to the top
        self.sidebar_layout.addStretch()

        # Add sidebar to main layout
        container_layout.addWidget(sidebar)

    def setup_timeline_main_area(self, container_layout: QVBoxLayout | QHBoxLayout):
        """Setup the right main area for content."""
        self.timeline_main_area = QWidget()
        self.timeline_main_area.setObjectName("timeline_main_area")
        self.main_area_layout = QVBoxLayout(self.timeline_main_area)
        self.main_area_layout.setContentsMargins(0, 0, 0, 0)

        # Bucket list section
        self.init_bucket_list()

        # Control buttons section (output directory and export)
        self.init_control_buttons(self.main_area_layout, self.timeline_main_area)

        # Progress bars
        self.init_progress_bars(self.main_area_layout, self.timeline_main_area)

        # Archives display
        self.init_archives_display(self.main_area_layout, self.timeline_main_area)

        # Add main area to layout
        container_layout.addWidget(self.timeline_main_area)

    def init_config_section(self, layout: QVBoxLayout | QHBoxLayout):
        """Initialize configuration options in sidebar."""
        # Filter options
        filters_label = QLabel()
        filters_label.setStyleSheet("font-weight: bold;")
        filters_icon = QIcon(get_resource_path("src/resources/icons/filters-icon.svg"))
        filters_label.setPixmap(filters_icon.pixmap(18, 18))
        filters_text = QLabel("Filters")
        filters_text.setStyleSheet("font-weight: bold;")

        filters_header = QHBoxLayout()
        filters_header.setContentsMargins(0, 0, 0, 0)
        filters_header.addWidget(filters_label)
        filters_header.addWidget(filters_text)
        filters_header.addStretch()
        layout.addLayout(filters_header)

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

        self.is_favorite_check = QCheckBox("Is Favorite?")
        self.is_favorite_check.setChecked(False)
        left_layout.addWidget(self.is_favorite_check)

        self.is_trashed_check = QCheckBox("Is Trashed?")
        self.is_trashed_check.setChecked(False)
        left_layout.addWidget(self.is_trashed_check)

        # Right column
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.with_stacked_check = QCheckBox("With Stacked?")
        right_layout.addWidget(self.with_stacked_check)

        self.with_partners_check = QCheckBox("With Partners?")
        right_layout.addWidget(self.with_partners_check)

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
        visibility_label = QLabel()
        visibility_label.setStyleSheet("font-weight: bold;")
        visibility_icon = QIcon(get_resource_path("src/resources/icons/visibility-icon.svg"))
        visibility_label.setPixmap(visibility_icon.pixmap(18, 18))
        visibility_text = QLabel("Visibility")
        visibility_text.setStyleSheet("font-weight: bold;")

        visibility_header = QHBoxLayout()
        visibility_header.setContentsMargins(0, 0, 0, 0)
        visibility_header.addWidget(visibility_label)
        visibility_header.addWidget(visibility_text)
        visibility_header.addStretch()
        self.sidebar_layout.addLayout(visibility_header)

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
        self.init_fetch_button(albums_layout, "Fetch Albums", self.fetch_albums)

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

        # Bottom area
        self.albums_main_area = QWidget()
        self.albums_main_area.setObjectName("albums_main_area")
        self.albums_main_area_layout = QVBoxLayout(self.albums_main_area)
        self.albums_main_area_layout.setContentsMargins(0, 0, 0, 0)

        # Control buttons section (output directory and export)
        self.init_control_buttons(self.albums_main_area_layout, self.albums_main_area)

        # Progress bars
        self.init_progress_bars(self.albums_main_area_layout, self.albums_main_area)

        # Archives display
        self.init_archives_display(self.albums_main_area_layout, self.albums_main_area)

        albums_layout.addWidget(self.albums_main_area)
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
            self.export_manager = ExportManager(self.login_manager, self.logger, "", self.stop_flag)
            self.albums = self.export_manager.get_albums()

            # Add albums to the list or show no albums message
            if self.albums:
                for album in self.albums:
                    checkbox = QCheckBox(f"{album['albumName']} ({album['assetCount']} assets)")
                    checkbox.setChecked(self.select_all_albums_checkbox.isChecked())
                    self.albums_list_layout.addWidget(checkbox)

                self.select_all_albums_checkbox.setText(f"Select All ({len(self.albums)})")
                self.albums_main_area.output_dir_label.show()
                self.albums_main_area.output_dir_button.show()
                self.albums_main_area.export_button.show()
                self.albums_main_area.export_button.show()
                self.albums_main_area.archives_display.show()

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
        download_label = QLabel()
        download_label.setStyleSheet("font-weight: bold;")
        download_icon = QIcon(get_resource_path("src/resources/icons/archive-icon.svg"))
        download_label.setPixmap(download_icon.pixmap(18, 18))
        download_text = QLabel("Download Archives")
        download_text.setStyleSheet("font-weight: bold;")

        download_header = QHBoxLayout()
        download_header.setContentsMargins(0, 0, 0, 0)
        download_header.addWidget(download_label)
        download_header.addWidget(download_text)
        download_header.addStretch()
        self.sidebar_layout.addLayout(download_header)

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
        self.timeline_main_area.order_label = QLabel("Order by:")
        self.timeline_main_area.order_label.hide()
        bucket_header_layout.addWidget(self.timeline_main_area.order_label)

        self.timeline_main_area.order_button = QPushButton("↓") # Start with descending
        self.timeline_main_area.order_button.setMaximumWidth(30)
        self.timeline_main_area.order_button.setToolTip("Toggle sort order (↓ descending/newest first, ↑ ascending/oldest first)")
        self.timeline_main_area.order_button.clicked.connect(self.toggle_timeline_order)
        self.timeline_main_area.order_button.hide()
        bucket_header_layout.addWidget(self.timeline_main_area.order_button)

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

    def init_fetch_button(self, container_layout: QVBoxLayout | QHBoxLayout, title: str, callback: callable):
        """Initialize fetch button at the top of main area."""
        fetch_layout = QHBoxLayout()
        fetch_button = QPushButton(title)
        fetch_button.setIcon(QIcon(get_resource_path("src/resources/icons/download-icon.svg")))
        fetch_button.clicked.connect(callback)
        fetch_layout.addWidget(fetch_button)
        fetch_layout.addStretch()  # Push to left
        container_layout.addLayout(fetch_layout)

    def init_control_buttons(self, container_layout: QVBoxLayout | QHBoxLayout, main_area: QWidget):
        """Initialize output directory and export controls in main area."""
        main_area.output_dir = ""
        main_area.output_dir_label = QLabel("<span><span style='color: red;'>*</span> Select output directory:</span>")
        main_area.output_dir_label.hide()
        container_layout.addWidget(main_area.output_dir_label)

        # Output directory button row
        output_layout = QHBoxLayout()
        main_area.output_dir_button = QPushButton("Choose Directory")
        main_area.output_dir_button.setIcon(QIcon(get_resource_path("src/resources/icons/folder-icon.svg")))
        main_area.output_dir_button.clicked.connect(lambda: self.select_output_dir(main_area))
        main_area.output_dir_button.hide()
        output_layout.addWidget(main_area.output_dir_button)
        output_layout.addStretch() # Push to left
        container_layout.addLayout(output_layout)

        # Export buttons row (no title)
        export_layout = QHBoxLayout()

        main_area.export_button = QPushButton("Export")
        main_area.export_button.setIcon(QIcon(get_resource_path("src/resources/icons/archive-icon.svg")))
        main_area.export_button.clicked.connect(lambda: self.start_export(main_area))
        main_area.export_button.hide()
        export_layout.addWidget(main_area.export_button)

        main_area.stop_button = QPushButton("Stop Export")
        main_area.stop_button.setStyleSheet("background-color: '#f44336'; color: white;")
        main_area.stop_button.clicked.connect(lambda: self.stop_export(main_area))
        main_area.stop_button.hide()
        export_layout.addWidget(main_area.stop_button)

        main_area.resume_button = QPushButton("Resume Export")
        main_area.resume_button.setStyleSheet("background-color: '#4CAF50'; color: white;")
        main_area.resume_button.clicked.connect(lambda: self.resume_export(main_area))
        main_area.resume_button.hide()
        export_layout.addWidget(main_area.resume_button)

        # Add stretch to push buttons to the left
        export_layout.addStretch()
        container_layout.addLayout(export_layout)

    def init_progress_bars(self, container_layout: QVBoxLayout | QHBoxLayout, main_area: QWidget):
        """Initialize progress bars in main area."""
        main_area.current_download_progress_bar = QProgressBar()
        main_area.current_download_progress_bar.setRange(0, 100)
        main_area.current_download_progress_bar.setFormat("Current Download: 0%")
        main_area.current_download_progress_bar.setValue(0)
        main_area.current_download_progress_bar.setTextVisible(True)
        main_area.current_download_progress_bar.setStyleSheet("""
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
        main_area.current_download_progress_bar.hide()
        container_layout.addWidget(main_area.current_download_progress_bar)

        main_area.progress_bar = QProgressBar()
        main_area.progress_bar.hide()
        container_layout.addWidget(main_area.progress_bar)

    def init_archives_display(self, container_layout: QVBoxLayout | QHBoxLayout, main_area: QWidget):
        """Initialize archives display section in main area."""
        main_area.archives_section = QWidget()
        archives_layout = QHBoxLayout(main_area.archives_section)

        archives_label = QLabel("Downloaded Archives:")
        archives_label.setStyleSheet("font-weight: bold;")
        archives_layout.addWidget(archives_label)

        open_folder_button = QPushButton("Open Folder")
        open_folder_button.clicked.connect(lambda: self.open_output_folder(main_area))
        archives_layout.addWidget(open_folder_button)

        main_area.archives_section.hide()
        container_layout.addWidget(main_area.archives_section)

        main_area.archives_display = AutoScrollTextEdit()
        main_area.archives_display.setPlaceholderText("Downloaded archives will appear here...")
        main_area.archives_display.setMaximumHeight(75)  # Limit height
        main_area.archives_display.hide()  # Initially hidden
        container_layout.addWidget(main_area.archives_display)

    def fetch_buckets(self):
        """Fetch buckets from the API."""
        if not self.validate_fetch_inputs():
            return

        try:
            if self.logger:
                self.logger.append("Fetching buckets...")
            inputs = self.get_user_input_values()
            # Don't require output_dir for fetching buckets
            self.export_manager = ExportManager(self.login_manager, self.logger, "", self.stop_flag)

            # Check if server supports Range headers and hide resume button if not
            self.check_and_hide_resume_button_if_needed(self.timeline_main_area)

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
                self.timeline_main_area.order_label.hide()
                self.timeline_main_area.order_button.hide()

                # Hide output directory and export sections
                self.timeline_main_area.output_dir_label.hide()
                self.timeline_main_area.output_dir_button.hide()
                self.timeline_main_area.export_button.hide()

                # Hide archives display
                self.timeline_main_area.archives_display.hide()
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
            self.timeline_main_area.order_label.show()
            self.timeline_main_area.order_button.show()

            # Show output directory and export sections
            self.timeline_main_area.output_dir_label.show()
            self.timeline_main_area.output_dir_button.show()
            self.timeline_main_area.export_button.show()

            # Show archives display area
            self.timeline_main_area.archives_display.show()

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
            self.timeline_main_area.order_label.hide()
            self.timeline_main_area.order_button.hide()

            # Hide output directory and export sections
            self.timeline_main_area.output_dir_label.hide()
            self.timeline_main_area.output_dir_button.hide()
            self.timeline_main_area.export_button.hide()

            # Hide archives display
            self.timeline_main_area.archives_display.hide()

    def start_export(self, main_area: QWidget):
        """Start the export process."""
        # Validate export inputs (including output directory)
        if not self.validate_export_inputs(main_area):
            return

        if self.logger:
            self.logger.append("Starting export process...")
        self.stop_requested = False
        # Clear any existing paused state when starting fresh
        self.paused_export_state = None
        main_area.resume_button.hide()  # Hide resume button when starting new export

        # Disable only tab switching during export, keep content interactive
        self.export_in_progress = True
        self.tab_widget.tabBar().setEnabled(False)

        selected_items = self.get_selected_albums() if main_area.objectName() == "albums_main_area" else self.get_selected_buckets()

        if not selected_items:
            if self.logger:
                self.logger.append("Error: No items selected for export.")
            return

        main_area.export_button.hide()
        main_area.stop_button.show()

        # Hide output directory button during export to prevent changes
        main_area.output_dir_button.hide()

        # Update export manager with correct output directory
        self.export_manager = ExportManager(self.login_manager, self.logger, main_area.output_dir, self.stop_flag)

        # Check if server supports Range headers and hide resume button if not
        self.check_and_hide_resume_button_if_needed(main_area)

        self.setup_progress_bar(main_area, len(selected_items))
        if self.logger:
            self.logger.append(f"Total items to process: {len(selected_items)}")

        if main_area.objectName() == "albums_main_area":
            self.export_albums(main_area, selected_items)
        else:
            self.export_buckets(main_area, selected_items)

        if self.login_manager.is_logged_in():
            self.finalize_export(main_area)

    def export_albums(self, main_area: QWidget, selected_items):
        for i, album in enumerate(selected_items, start=1):
            result = self.download_and_save_archive(main_area,album["assets"], album["albumName"], self.get_archive_size_in_bytes(), album_id=album["id"])
            if result == "completed":
                self.update_progress_bar(main_area, i, len(selected_items))
                QApplication.processEvents()

    def export_buckets(self, main_area: QWidget, selected_buckets):
        inputs = self.get_user_input_values()
        archive_size_bytes = self.get_archive_size_in_bytes()
        download_option = self.get_download_option()

        if download_option.startswith("Per"):
            self.process_buckets_individually(main_area, selected_buckets, inputs, archive_size_bytes)
        elif download_option == "Single Archive":
            self.process_all_buckets_combined(main_area, selected_buckets, inputs, archive_size_bytes)

    def process_buckets_individually(self, main_area: QWidget, selected_buckets, inputs, archive_size_bytes):
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
                self.show_resume_button(main_area)
                return

            bucket_name = self.export_manager.format_time_bucket(time_bucket)
            if self.logger:
                self.logger.append(f"Processing bucket {i}/{len(selected_buckets)}: {bucket_name}")

            try:
                asset_ids = self.fetch_assets_for_bucket(time_bucket, inputs)
                if not asset_ids:
                    if self.logger:
                        self.logger.append(f"No assets found for bucket: {bucket_name}")
                    self.update_progress_bar(main_area, i, len(selected_buckets))
                    continue

                download_result = self.download_and_save_archive(main_area,asset_ids, bucket_name, archive_size_bytes)
                if download_result == "paused":
                    # Save state and show resume button
                    self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Per Bucket", i - 1)
                    self.show_resume_button(main_area)
                    return

            except Exception as e:
                if self.logger:
                    self.logger.append(f"Error processing bucket {bucket_name}: {str(e)}")

            self.update_progress_bar(main_area, i, len(selected_buckets))
            QApplication.processEvents()

        # Clear paused state on successful completion
        self.paused_export_state = None

    def process_all_buckets_combined(self, main_area: QWidget, selected_buckets, inputs, archive_size_bytes):
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
                    self.show_resume_button(main_area)
                    return

                asset_ids = self.fetch_assets_for_bucket(time_bucket, inputs)
                all_asset_ids.extend(asset_ids)

            if not all_asset_ids:
                if self.logger:
                    self.logger.append("No assets found in selected buckets.")
                return

            download_result = self.download_and_save_archive(main_area, all_asset_ids, "Combined_Archive", archive_size_bytes)
            if download_result == "paused":
                # Save state and show resume button
                self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Single Archive", 0)
                self.show_resume_button(main_area)
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

    def download_and_save_archive(self, main_area: QWidget, asset_ids, archive_name, archive_size_bytes, album_id=None):
        """Download and save an archive with the given asset IDs."""
        try:
            archive_info = self.export_manager.prepare_archive(asset_ids, archive_size_bytes, album_id)
            total_size = archive_info["totalSize"]
            if total_size == 0:
                if self.logger:
                    self.logger.append(f"Failed to prepare archive for \"{archive_name}\"")
                return "error"

            total_archives_number = len(archive_info["archives"])

            if self.logger:
                self.logger.append(f"Preparing archive (\"{archive_name}\"): total size = {self.export_manager.format_size(total_size)};")
                self.logger.append(f"Requested max archive size = {self.export_manager.format_size(archive_size_bytes)};")
                self.logger.append(f"Number of archives = {total_archives_number};")
                if album_id is None:
                    self.logger.append(f"Number of assets = {len(asset_ids)}")
                else:
                    albums_assets_count = sum(len(archive["assetIds"]) for archive in archive_info["archives"])
                    self.logger.append(f"Number of assets = {albums_assets_count}")

            completed_archives_count = 0
            for archive in archive_info["archives"]:
                local_archive_name = f"{archive_name}_{completed_archives_count + 1}" if total_archives_number > 1 else f"{archive_name}"

                self.logger.append(f"Downloading archive {completed_archives_count + 1} of {total_archives_number} for \"{local_archive_name}\"; Archive size = {self.export_manager.format_size(archive['size'])}")
                download_result = self.export_manager.download_archive(
                    archive["assetIds"], local_archive_name, archive["size"], main_area.current_download_progress_bar
                )

                if download_result == "paused":
                    return "paused"
                elif download_result == "cancelled":
                    return "cancelled"
                elif download_result == "completed":
                    main_area.archives_display.show()
                    main_area.archives_display.append(f"{local_archive_name}")
                    completed_archives_count += 1
                    if completed_archives_count == total_archives_number:
                        return "completed"
                    else:
                        continue
                else:
                    return "error"
        except Exception as e:
            if self.logger:
                self.logger.append(f"Error preparing archive for \"{archive_name}\": {str(e)}")
            return "error"

    def clear_bucket_list(self):
        """Clear all bucket checkboxes from the list."""
        for i in reversed(range(self.bucket_list_layout.count())):
            widget = self.bucket_list_layout.itemAt(i).widget()
            if widget and widget != self.select_all_checkbox:
                widget.deleteLater()

        # Reset select all checkbox
        self.select_all_checkbox.setChecked(False)

    def resume_export(self, main_area: QWidget):
        """Resume a paused export."""
        if not self.paused_export_state:
            if self.logger:
                self.logger.append("No paused export to resume.")
            return

        if self.logger:
            self.logger.append("Resuming export process...")

        # Hide resume button and show stop button
        main_area.resume_button.hide()
        main_area.stop_button.show()

        # Hide output directory button during export to prevent changes
        main_area.output_dir_button.hide()

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
        self.export_manager = ExportManager(self.login_manager, self.logger, main_area.output_dir, self.stop_flag)

        # Check if server supports Range headers and hide resume button if not
        self.check_and_hide_resume_button_if_needed(main_area)

        if self.logger:
            self.logger.append(f"Resuming from bucket {current_bucket_index + 1}/{len(selected_buckets)}")

        if download_option.startswith("Per"):
            self.process_buckets_individually_resume(main_area, selected_buckets, inputs, archive_size_bytes, current_bucket_index)
        elif download_option == "Single Archive":
            # For single archive, we resume by retrying the download
            self.process_all_buckets_combined(main_area, selected_buckets, inputs, archive_size_bytes)

        # Only finalize if not paused
        if not self.paused_export_state and self.login_manager.is_logged_in():
            self.finalize_export(main_area)

    def process_buckets_individually_resume(self, main_area: QWidget, selected_buckets, inputs, archive_size_bytes, start_index=0):
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
                    self.update_progress_bar(main_area, i, len(selected_buckets))
                    continue

                download_result = self.download_and_save_archive(main_area, asset_ids, bucket_name, archive_size_bytes)
                if download_result == "paused":
                    # Save state and show resume button
                    self.save_export_state(selected_buckets, inputs, archive_size_bytes, "Per Bucket", i - 1)
                    self.show_resume_button(main_area)
                    return

            except Exception as e:
                if self.logger:
                    self.logger.append(f"Error processing bucket {bucket_name}: {str(e)}")

            self.update_progress_bar(main_area, i, len(selected_buckets))
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
            'output_dir': self.timeline_main_area.output_dir
        }

    def show_resume_button(self, main_area: QWidget):
        """Show resume button and hide stop button, but only if server supports Range headers."""
        if not self.login_manager.is_logged_in():
            return

        main_area.stop_button.hide()

        # Show output directory button when export is paused
        main_area.output_dir_button.show()

        # Check if server supports Range headers
        if self.export_manager:
            # server_url = getattr(self.export_manager.api_manager, 'server_url', 'unknown')

            # # Check cache first - this is the most reliable source
            # server_supports_range = False  # Default
            # if hasattr(self.export_manager, 'range_support_cache') and server_url in self.export_manager.range_support_cache:
            #     server_supports_range = self.export_manager.range_support_cache[server_url]
            # else:
            #     # Fallback to the method check
            #     server_supports_range = self.export_manager.check_range_header_support(server_url)

            # if server_supports_range:
            #     main_area.resume_button.show()
            #     if self.logger:
            #         self.logger.append("Export paused. Click 'Resume Export' to continue.")
            # else:
            #     # Server doesn't support Range headers - show export button instead
            #     main_area.export_button.show()
            if self.logger:
                self.logger.append("Export paused. Server doesn't support resume functionality.")
                self.logger.append("Click 'Export' to restart. Already downloaded files will be skipped automatically.")
        else:
            # Fallback if export_manager is not available
            main_area.export_button.show()
            if self.logger:
                self.logger.append("Export paused. Click 'Export' to restart.")

    def finalize_export(self, main_area: QWidget):
        """Finalize the export process."""
        if not self.paused_export_state:
            # Only finalize if not paused
            main_area.stop_button.hide()
            main_area.export_button.show()
            main_area.archives_section.show()
            main_area.current_download_progress_bar.hide()
            main_area.progress_bar.hide()

            # Show output directory button when export is finished
            main_area.output_dir_button.show()

            self.export_finished.emit()

    def check_for_resumable_downloads(self):
        """Check if there are any downloads that can be resumed."""
        if not self.timeline_main_area.output_dir or not self.export_manager:
            return False

        resume_dir = os.path.join(self.timeline_main_area.output_dir, ".archimmich_resume")
        if not os.path.exists(resume_dir):
            return False

        # Check for any .resume.json files
        import glob
        resume_files = glob.glob(os.path.join(resume_dir, "*.resume.json"))
        return len(resume_files) > 0

    def check_and_hide_resume_button_if_needed(self, main_area: QWidget):
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
                main_area.resume_button.hide()
                if self.logger:
                    self.logger.append("Note: Resume functionality disabled - server doesn't support Range headers.")

    def show_resumable_downloads_info(self):
        """Show information about resumable downloads."""
        if self.check_for_resumable_downloads() and self.logger:
            self.logger.append("Found resumable downloads. Individual files can be resumed automatically.")

