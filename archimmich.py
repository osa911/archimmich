import sys
import json
import requests
import os
import webbrowser
import time
import hashlib
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QScrollArea, QFrame,
    QComboBox, QPushButton, QFileDialog, QWidget, QProgressBar, QSpacerItem, QSizePolicy, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QIntValidator, QGuiApplication, QPixmap)
from avatar import display_avatar
from tqdm import tqdm
from AutoScrollTextEdit import AutoScrollTextEdit

class ExporterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.stop_requested = False  # Flag to indicate if export should stop

        self.setWindowTitle("ArchImmich")
        screen_geometry = QGuiApplication.primaryScreen().geometry()

        # Get the window's geometry
        window_width = 850
        window_height = 850

        # Calculate the x, y position for the window to be centered
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2

        # Set the window geometry
        self.setGeometry(x, y, window_width, window_height)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Add image to the top center
        self.image_label = QLabel()
        pixmap = QPixmap("./immich-logo.svg")  # Replace with your image path
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # Align center and top
        self.image_label.setScaledContents(True)  # Scale image if needed
        self.image_label.setFixedSize(132, 45)  # Set a fixed size for the image

        self.image_layout = QHBoxLayout()
        self.image_layout.addWidget(self.image_label)
        self.image_layout.setAlignment(Qt.AlignHCenter)  # Center horizontally
        # Add the horizontal layout to the main layout
        self.layout.addLayout(self.image_layout)

        # Add the image to the layout
        # self.layout.addWidget(self.image_label)

        # Input fields for login
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

        # Create a container for avatar and login status text
        self.avatar_text_container = QWidget()
        self.avatar_text_layout = QHBoxLayout(self.avatar_text_container)

        # Set the avatar QLabel
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(50, 50)  # Set size for the avatar
        self.avatar_label.hide()  # Initially hidden

        # Set the login status QLabel
        self.login_status = QLabel("")
        self.login_status.setStyleSheet("color: green; font-size: 14px;")  # Optional styling

        # Add the avatar and login status to the horizontal layout
        self.avatar_text_layout.addWidget(self.avatar_label)
        self.avatar_text_layout.addWidget(self.login_status)
        self.avatar_text_layout.setContentsMargins(0, 0, 0, 0)
        self.avatar_text_layout.setAlignment(Qt.AlignLeft)

        # Add the container to the main layout
        self.layout.addWidget(self.avatar_text_container)

        # Spacer for cleaner layout
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(spacer)

        # Config options (hidden by default)
        self.config_section = QWidget()
        self.config_section.hide()
        self.config_layout = QVBoxLayout(self.config_section)

        # Configuration Options
        self.is_archived_check = QCheckBox("Is Archived?")
        self.config_layout.addWidget(self.is_archived_check)

        self.with_partners_check = QCheckBox("With Partners?")
        self.config_layout.addWidget(self.with_partners_check)

        self.with_stacked_check = QCheckBox("With Stacked?")
        self.config_layout.addWidget(self.with_stacked_check)

        # Archive Size Input
        self.archive_size_label = QLabel("Archive Size (GB):")
        self.archive_size_field = QLineEdit()
        self.archive_size_field.setPlaceholderText("Enter size in GB")
        self.archive_size_field.setValidator(QIntValidator(1, 1024))  # Only allow integers between 1 and 1024
        self.archive_size_field.setText("4")  # Set default value to 4 GB
        self.config_layout.addWidget(self.archive_size_label)
        self.config_layout.addWidget(self.archive_size_field)

        # Size ComboBox
        self.size_combo_label = QLabel("Size:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["DAY", "MONTH"])
        self.size_combo.setCurrentText("MONTH")
        self.size_combo.currentIndexChanged.connect(self.update_download_by_combo)
        self.config_layout.addWidget(self.size_combo_label)
        self.config_layout.addWidget(self.size_combo)

        # Download Archives By ComboBox
        self.download_by_label = QLabel("Download Archives:")
        self.download_by_combo = QComboBox()
        self.download_by_combo.addItems([f"Per {self.size_combo.currentText().capitalize()}", "Single Archive"])
        self.config_layout.addWidget(self.download_by_label)
        self.config_layout.addWidget(self.download_by_combo)

        self.layout.addWidget(self.config_section)

        # Output Directory Selector
        self.output_dir_label = QLabel("<span><span style='color: red;'>*</span> Output Directory:</span>")
        self.output_dir_button = QPushButton("Choose Directory")
        self.output_dir_button.clicked.connect(self.select_output_dir)

        self.config_layout.addWidget(self.output_dir_label)
        self.config_layout.addWidget(self.output_dir_button)

        # Fetch buckets button (hidden by default)
        self.fetch_button = QPushButton("Fetch Buckets")
        self.fetch_button.clicked.connect(self.fetch_buckets)
        self.fetch_button.hide()
        self.layout.addWidget(self.fetch_button)

        # Horizontal Divider
        self.divider1 = QFrame(self)
        self.divider1.setFrameShape(QFrame.HLine)  # Set shape to horizontal line
        self.divider1.setFrameShadow(QFrame.Sunken)  # Add subtle 3D effect
        self.divider1.setStyleSheet("background-color: lightgray;")  # Optional: Color the divider
        self.divider1.hide()
        self.layout.addWidget(self.divider1)

        # Bucket Selection Section
        self.bucket_list_label = QLabel("Available Buckets:")
        self.layout.addWidget(self.bucket_list_label)
        self.bucket_list_label.hide()

        # Scrollable area for bucket checkboxes
        self.bucket_scroll_area = QScrollArea()
        self.bucket_scroll_area.setWidgetResizable(True)
        self.bucket_scroll_area.setMinimumHeight(160)

        # Widget to hold the checkboxes
        self.bucket_list_widget = QWidget()
        self.bucket_list_layout = QVBoxLayout(self.bucket_list_widget)

        # Add "Select All" checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        self.bucket_list_layout.addWidget(self.select_all_checkbox)

        self.bucket_scroll_area.setWidget(self.bucket_list_widget)
        self.layout.addWidget(self.bucket_scroll_area)
        self.bucket_scroll_area.hide()

        # Export Button
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.start_export)
        self.export_button.hide()  # Initially hidden
        self.layout.addWidget(self.export_button)

        # Progress bar for the current download
        self.current_download_progress_bar = QProgressBar(self)
        self.current_download_progress_bar.setRange(0, 100)  # Percentage-based
        self.current_download_progress_bar.setFormat("Current Download: 0%")  # Label
        self.current_download_progress_bar.setValue(0)  # Start at 0
        self.current_download_progress_bar.setTextVisible(True)  # Ensure progress bar text is visible
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
        self.current_download_progress_bar.hide()  # Initially hidden
        self.layout.addWidget(self.current_download_progress_bar)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        # Archives Section (Simplified)
        self.archives_section = QWidget()
        self.archives_layout = QHBoxLayout(self.archives_section)

        self.archives_label = QLabel("Downloaded Archives:")
        self.archives_layout.addWidget(self.archives_label)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_output_folder)
        self.archives_layout.addWidget(self.open_folder_button)

        self.archives_display = AutoScrollTextEdit()
        self.archives_display.setReadOnly(True)  # Make it read-only
        self.archives_display.setPlaceholderText("Downloaded archives will appear here...")
        self.archives_display.hide()
        self.layout.addWidget(self.archives_display)

        self.layout.addWidget(self.archives_section)
        self.archives_section.hide()  # Initially hidden

        self.stop_button = QPushButton("Stop Export")
        self.stop_button.setStyleSheet("background-color: '#f44336'; color: white;")
        self.stop_button.clicked.connect(self.stop_export)
        self.stop_button.hide()  # Initially hidden
        self.layout.addWidget(self.stop_button)

        # Horizontal Divider
        self.divider2 = QFrame(self)
        self.divider2.setFrameShape(QFrame.HLine)  # Set shape to horizontal line
        self.divider2.setFrameShadow(QFrame.Sunken)  # Add subtle 3D effect
        self.divider2.setStyleSheet("background-color: '#ededed';")  # Optional: Color the divider
        self.divider2.hide()
        self.layout.addWidget(self.divider2)

        # Logs and progress bar
        self.logs = AutoScrollTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMinimumHeight(200)
        self.logs.setPlaceholderText("Logs will appear here. Start by logging in.")
        self.layout.addWidget(self.logs)

        # Logout Button
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.hide()  # Initially hidden
        self.layout.addWidget(self.logout_button)

        # Initialize placeholders
        self.buckets = []
        self.output_dir = ""

    def stop_export(self):
        """
        Handle the stop export request by setting the stop flag.
        """
        self.logs.append("Stop requested. Stopping export process...")
        self.stop_requested = True

    def update_download_by_combo(self):
        """
        Update the items in the download_by_combo based on the size_combo selection.
        """
        self.download_by_combo.clear()  # Clear existing items
        self.download_by_combo.addItems([f"Per {self.size_combo.currentText().capitalize()}", "Single Archive"])

    def logout(self):
      """
      Handle the logout process by resetting the UI and application state.
      """
      self.logs.append("Logging out...")

      # Reset UI Elements
      self.login_status.setText("")  # Clear login status
      self.login_status.setStyleSheet("color: red;")
      self.api_key_field.setText("")  # Clear API key input
      self.server_ip_field.setText("")  # Clear server IP input

      # Reset configurations and hide sections
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

      # Clear logs and state
      self.logs.append("You have been logged out.")
      self.buckets = []
      self.output_dir = ""
      # self.archives_container_layout = QVBoxLayout(self.archives_container)  # Clear archives list

      # Show login inputs and hide logout button
      self.api_key_label.show()
      self.api_key_field.show()
      self.server_ip_label.show()
      self.server_ip_field.show()
      self.login_button.show()
      self.logout_button.hide()

    def get_archive_size_in_bytes(self):
        """
        Convert the archive size input from GB to bytes.
        Returns:
            int: The archive size in bytes or None if the input is invalid or empty.
        """
        size_in_gb = self.archive_size_field.text()
        if not size_in_gb.isdigit():
            self.logs.append("Invalid archive size input. Please enter a valid number in GB.")
            return None
        return int(size_in_gb) * 1024 ** 3  # Convert GB to bytes

    def select_output_dir(self):
        self.output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if self.output_dir:
            self.logs.append(f"Selected Output Directory: {self.output_dir}")
            # Update the label with the selected directory
            self.output_dir_label.setText(
                f"<span><span style='color: red;'>*</span> Output Directory: <b>{self.output_dir}</b></span>"
            )
            self.output_dir_label.setStyleSheet("")  # Reset style
        else:
            self.logs.append("No directory selected.")
            self.output_dir_label.setText("<span style='color: red;'>Output Directory * (required):</span>")  # Reset label

    def getAPIHost(self):
        """
        Retrieve the server host URL.
        Appends '/api' to the server IP if it's not already included.
        Returns:
            str: The server host URL.
        """
        server_ip = self.server_ip_field.text()
        # Append '/api' if it's not already present
        return server_ip if server_ip.endswith('/api') else f"{server_ip}/api"

    def getAPIKey(self):
        return self.api_key_field.text()

    def getHeaders(self):
        return {
            "x-api-key": f"{self.getAPIKey()}",
            "Content-Type": "application/json"
        }

    def perform_login(self):
        """
        Perform the login API request.
        Returns:
            requests.Response: The response from the login API.
        Raises:
            requests.exceptions.RequestException: If the request fails.
        """

        response = requests.get(f"{self.getAPIHost()}/users/me", headers=self.getHeaders())
        response.raise_for_status()  # Raises HTTPError for bad responses
        self.logs.append(f"Login request sent.")
        self.user = response.json()
        return response

    def login(self):
      """
      Handle the login process, including calling the login API and handling responses.
      Logs success or failure and displays the user's avatar upon success.
      """
      self.logs.append("Attempting to login...")

      # Validate login inputs
      if not self.validate_login_inputs():
          # Stop further execution if validation fails
          return

      try:
          self.perform_login()
          # Login success
          user_name = self.user.get('name', 'Unknown User')
          user_email = self.user.get('email', 'Unknown Email')
          self.login_status.setText(
              f"<p>Logged in successfully.</p>"
              f"<p>User: <b>{user_name}</b></p>"
              f"<p>Email: <b>{user_email}</b></p>"
          )
          self.login_status.setStyleSheet("color: green; font-size: 14px;")
          self.logs.append("Login successful!")
          self.logs.append(f"User: {user_name} | Email: {user_email}")

          # Display user avatar
          if "profileImagePath" in self.user:
              avatar_url = f"{self.getAPIHost()}/users/{self.user['id']}/profile-image"
              display_avatar(self, avatar_url)

          # Show the avatar and login status container
          self.avatar_label.show()
          self.avatar_text_container.show()

          # Hide login inputs and show config section
          self.api_key_label.hide()
          self.api_key_field.hide()
          self.server_ip_label.hide()
          self.server_ip_field.hide()
          self.login_button.hide()

          self.config_section.show()
          self.fetch_button.show()
          self.logout_button.show()  # Show logout button
          self.archives_display.show()

      except requests.exceptions.RequestException as e:
          # Handle login failure
          self.logs.append(f"Login failed: {str(e)}")
          self.login_status.setText("Login failed. Please check your API key or server.")
          self.login_status.setStyleSheet("color: red; font-size: 14px;")

    def get_user_input_values(self):
        """
        Fetch user input values from the UI.
        Returns:
            dict: A dictionary containing input values for isArchived, size, withPartners, and withStacked.
        """
        return {
            "isArchived": "true" if self.is_archived_check.isChecked() else "false",
            "size": self.size_combo.currentText(),
            "withPartners": "true" if self.with_partners_check.isChecked() else "false",
            "withStacked": "true" if self.with_stacked_check.isChecked() else "false",
        }

    def generate_timeline_buckets_url(self):
        """
        Generate the URL for the timeline bucket API using user input values.
        Returns:
            str: The constructed URL.
        """
        inputs = self.get_user_input_values()
        url = (
            f"{self.getAPIHost()}/timeline/buckets"
            f"?isArchived={inputs['isArchived']}"
            f"&size={inputs['size']}"
            f"&withPartners={inputs['withPartners']}"
            f"&withStacked={inputs['withStacked']}"
        )
        return url


    def generate_timeline_bucket_url(self, timeBucket):
        """
        Generate the URL for the timeline bucket API using user input values.
        Returns:
            str: The constructed URL.
        """
        inputs = self.get_user_input_values()
        url = (
            f"{self.getAPIHost()}/timeline/bucket"
            f"?isArchived={inputs['isArchived']}"
            f"&size={inputs['size']}"
            f"&withPartners={inputs['withPartners']}"
            f"&withStacked={inputs['withStacked']}"
            f"&timeBucket={timeBucket}"
        )
        return url

    def validate_login_inputs(self):
        """
        Validate the login inputs (API key and server IP).
        Highlights invalid fields and logs errors if validation fails.
        Returns:
            bool: True if all validations pass, False otherwise.
        """
        is_valid = True  # Track overall validation status

        # Reset styles for login inputs
        self.api_key_field.setStyleSheet("")  # Reset API key highlight
        self.server_ip_field.setStyleSheet("")  # Reset server IP highlight

        # Validate API key
        if not self.api_key_field.text().strip():
            self.logs.append("Error: API key cannot be empty.")
            self.api_key_field.setStyleSheet("border: 2px solid red;")  # Highlight invalid field
            is_valid = False

        # Validate server IP
        if not self.server_ip_field.text().strip():
            self.logs.append("Error: Server IP cannot be empty.")
            self.server_ip_field.setStyleSheet("border: 2px solid red;")  # Highlight invalid field
            is_valid = False

        return is_valid

    def validate_bucket_inputs(self):
        """
        Validate archive size and output directory fields.
        Highlights invalid fields and logs errors if validation fails.
        Returns:
            bool: True if all validations pass, False otherwise.
        """
        is_valid = True  # Track overall validation status

        # Reset styles for inputs
        self.archive_size_label.setStyleSheet("")  # Reset archive size highlight
        self.archive_size_field.setStyleSheet("")  # Reset archive size highlight
        self.output_dir_label.setText("<span><span style='color: red;'>*</span> Output Directory: </span>")  # Reset label

        # Validate archive size
        archive_size_bytes = self.get_archive_size_in_bytes()
        if archive_size_bytes is None:
            self.logs.append("Error: Archive size must be specified in GB.")
            self.archive_size_label.setStyleSheet("color: red; font-weight: bold;")  # Highlight invalid field
            self.archive_size_field.setStyleSheet("border: 2px solid red;")  # Highlight invalid field
            is_valid = False

        # Validate output directory
        if not self.output_dir:
            self.logs.append("Error: Output directory must be selected.")
            self.output_dir_label.setStyleSheet("color: red; font-weight: bold;")  # Highlight invalid field
            is_valid = False

        return is_valid

    def format_time_bucket(self, time_bucket):
        """Converts timeBucket to 'Month Year' format."""
        date_obj = datetime.fromisoformat(time_bucket.replace("Z", "+00:00"))  # Convert to datetime
        return date_obj.strftime("%B_%Y")  # Format to 'Month Year'

    def populate_bucket_list(self, buckets):
        """
        Populate the scrollable list of buckets with checkboxes.
        Args:
            buckets (list): List of bucket objects from the server.
        """
        # Clear existing checkboxes
        for i in reversed(range(self.bucket_list_layout.count())):
            widget = self.bucket_list_layout.itemAt(i).widget()
            if widget and widget != self.select_all_checkbox:
                widget.deleteLater()

        # Add checkboxes for each bucket
        for bucket in buckets:
            bucket_name = self.format_time_bucket(bucket['timeBucket'])
            asset_count = bucket['count']
            asset_text = "asset" if asset_count == 1 else "assets"
            checkbox = QCheckBox(f"{bucket_name} | ({asset_count} {asset_text})")  # Display bucket name with singular/plural asset count
            checkbox.setObjectName(bucket['timeBucket'])  # Use the time bucket as the object name
            self.bucket_list_layout.addWidget(checkbox)

    def toggle_select_all(self, state):
        """
        Toggle all checkboxes in the bucket list based on the "Select All" checkbox state.
        Args:
            state (int): The state of the "Select All" checkbox (0 = unchecked, 2 = checked).
        """
        for i in range(1, self.bucket_list_layout.count()):  # Skip the "Select All" checkbox
            checkbox = self.bucket_list_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(state == Qt.Checked)

    def fetch_buckets(self):
        """
        Fetch timeline buckets from the server using user-provided inputs.
        Validates archive size and output directory before proceeding.
        Logs the results or any errors encountered during the request.
        """
        if not self.validate_bucket_inputs():
            # Stop further execution if validation fails
            return

        self.logs.append("Fetching buckets...")

        url = self.generate_timeline_buckets_url()

        try:
            response = requests.get(url, headers=self.getHeaders())
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

            self.buckets = response.json()
            self.logs.append(f"Buckets fetched successfully: {len(self.buckets)} buckets found.")

            # Populate the bucket list with checkboxes
            self.populate_bucket_list(self.buckets)
            self.bucket_scroll_area.show()
            self.export_button.show()
            self.divider1.show()
            self.divider2.show()

        except requests.exceptions.RequestException as e:
            # Log the error and inform the user
            self.logs.append(f"Failed to fetch buckets: {str(e)}")
            self.logs.append("Please check your server connection, API key, or server availability.")

    def fetch_images_by_period(self, period):
      """Fetches images for a specific month."""
      self.logs.append(f"Fetching images for period: {self.format_time_bucket(period)}...")
      url = self.generate_timeline_bucket_url(period)
      if self.stop_requested:
        self.logs.append("Fetch canceled by user.")
        return []

      try:
          response = requests.get(url, headers=self.getHeaders())
          response.raise_for_status()
          assets = response.json()

          # Check stop_requested before returning assets
          if self.stop_requested:
            self.logs.append("Fetch stopped by user.")
            return []

          # Extract asset IDs
          asset_ids = [asset['id'] for asset in assets]
          self.logs.append(f"Fetched {len(asset_ids)} assets for period {period}.")
          return asset_ids

      except requests.exceptions.RequestException as e:
          self.logs.append(f"Failed to fetch images for period {period}: {str(e)}")
          return []

    def prepare_archive(self, asset_ids):
        """
        Prepares the archive for download by sending asset IDs to the server.
        Args:
            asset_ids (list): List of asset IDs to include in the archive.
        Returns:
            dict: Response data from the server, containing archive information.
        """
        url = f"{self.getAPIHost()}/download/info"
        payload = {
            "assetIds": asset_ids,
            "archiveSize": self.get_archive_size_in_bytes()  # The desired maximum archive size in bytes
        }

        try:
            response = requests.post(url, headers=self.getHeaders(), data=json.dumps(payload))
            response.raise_for_status()  # Raise an error for HTTP 4xx/5xx
            archive_info = response.json()

            # Log total size of the prepared archive
            total_size = archive_info.get('totalSize', 0)
            self.logs.append(f"Archive prepared: Total size = {self.format_size(total_size)}")

            return archive_info

        except requests.exceptions.RequestException as e:
            self.logs.append(f"Failed to prepare archive: {str(e)}")
            return {}

    def format_size(self, bytes_size):
        """Formats size in bytes to GB and MB."""
        gb_size = bytes_size / (1024 ** 3)  # Convert to GB
        mb_size = bytes_size / (1024 ** 2)  # Convert to MB
        return f"{gb_size:.2f} GB ({mb_size:.2f} MB)"

    def calculate_file_checksum(file_path):
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def download_archive(self, asset_ids, bucket_name, total_size):
        """
        Downloads the archive containing the specified assets with real-time progress.
        Args:
            asset_ids (list): List of asset IDs to include in the archive.
            bucket_name (str): Name of the bucket for the archive (used for file naming).
        """
        archive_path = os.path.join(self.output_dir, f"{bucket_name}.zip")
        os.makedirs(self.output_dir, exist_ok=True)

        # Check for existing file with tolerance
        if os.path.exists(archive_path):
            existing_size = os.path.getsize(archive_path)
            if abs(existing_size - total_size) <= 1024:  # Allow 1KB tolerance
                self.logs.append(f"Archive '{bucket_name}.zip' exists. Skipping download.")
                self.add_archive_to_section(f"Skipping {bucket_name}.zip - already exists.")
                return

        self.logs.append(f"Downloading archive: {bucket_name}.zip")
        url = f"{self.getAPIHost()}/download/archive"
        payload = {"assetIds": asset_ids}

        response = requests.post(url, headers=self.getHeaders(), data=json.dumps(payload), stream=True)
        response.raise_for_status()

        # Show current download progress bar
        self.current_download_progress_bar.setValue(0)
        self.current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - 0%")
        self.current_download_progress_bar.show()

        downloaded_size = 0
        start_time = time.time()

        with open(archive_path, "wb") as archive_file:
          for chunk in response.iter_content(chunk_size=8192):
              if self.stop_requested:
                  self.logs.append("Download stopped by user.")
                  break

              if chunk:  # Write chunk to file
                  archive_file.write(chunk)
                  downloaded_size += len(chunk)

                  if total_size:
                    progress = int((downloaded_size / total_size) * 100)
                    self.current_download_progress_bar.setValue(progress)
                    self.current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - {progress}%")

                  # Log and update UI
                  elapsed_time = time.time() - start_time
                  if elapsed_time > 0:
                      speed_mb = (downloaded_size / elapsed_time) / (1024 ** 2)
                      self.logs.append(f"Downloaded: {self.format_size(downloaded_size)}, Speed: {speed_mb:.2f} MB/s")
                  QApplication.processEvents()  # Refresh UI

        if not self.stop_requested:
          # Finalize current download progress bar
          self.current_download_progress_bar.setValue(100)
          self.current_download_progress_bar.setFormat(f"Current Download: {bucket_name} - 100%")
          self.logs.append(f"Archive downloaded: {bucket_name}.zip")
          self.add_archive_to_section(f"{bucket_name}.zip")

    def add_archive_to_section(self, text):
      self.archives_display.append(text)

    def open_output_folder(self):
        """
        Open the output directory where archives are stored.
        """
        if self.output_dir:
            webbrowser.open(f"file://{self.output_dir}")
            self.logs.append(f"Opening output directory: {self.output_dir}")
        else:
            self.logs.append("No output directory set. Please choose an output directory first.")

    def start_export(self):
      """
      Start the export process for all selected buckets, updating the progress bar dynamically with percentages.
      """
      self.logs.append("Starting export process...")
      self.stop_requested = False  # Reset stop flag

      # Show stop button and progress bar
      self.stop_button.show()

      # Get selected buckets
      selected_buckets = [
          self.bucket_list_layout.itemAt(i).widget().objectName()
          for i in range(1, self.bucket_list_layout.count())  # Skip "Select All"
          if isinstance(self.bucket_list_layout.itemAt(i).widget(), QCheckBox) and
          self.bucket_list_layout.itemAt(i).widget().isChecked()
      ]

      if not selected_buckets:
          self.logs.append("Error: No buckets selected for export.")
          self.stop_button.hide()
          return

      total_buckets = len(selected_buckets)

      # Configure the progress bar
      self.progress_bar.setRange(0, total_buckets)  # Set range for total buckets
      self.progress_bar.setValue(0)  # Start at 0
      self.progress_bar.setTextVisible(True)  # Ensure progress bar text is visible
      self.progress_bar.setFormat("Overall Progress: 0%")  # Set initial format
      self.progress_bar.setStyleSheet("""
          QProgressBar {
              text-align: center;
              color: white;
              background-color: #333333;
              border: 1px solid #555555;
          }
          QProgressBar::chunk {
              background-color: #3daee9;
          }
      """)
      self.progress_bar.show()

      self.logs.append(f"Total buckets to process: {total_buckets}")

      # Start processing each bucket
      for i, time_bucket in enumerate(selected_buckets, start=1):
          if self.stop_requested:
            self.logs.append("Export stopped by user.")
            break

          bucket_name = self.format_time_bucket(time_bucket)
          self.logs.append(f"Processing bucket {i}/{total_buckets}: {bucket_name}")

          # Simulate asset fetching for the bucket
          asset_ids = self.fetch_images_by_period(time_bucket)
          if self.stop_requested:
            self.logs.append("Export stopped by user during image fetch.")
            break

          asset_count = len(asset_ids)
          if asset_count == 0:
              self.logs.append(f"No images found for bucket: {bucket_name}")
              self.progress_bar.setValue(i)  # Update progress
              self.progress_bar.setFormat(f"Overall Progress: {int((i / total_buckets) * 100)}%")
              QApplication.processEvents()
              continue

          archive_info = self.prepare_archive(asset_ids)
          if self.stop_requested:
            self.logs.append("Export stopped by user during archive preparation.")
            break

          total_size = archive_info["totalSize"]
          self.logs.append(
              f"Preparing archive: Total size = {self.format_size(total_size)} ({asset_count} assets)"
          )

          self.download_archive(asset_ids, bucket_name, total_size)
          if self.stop_requested:
            self.logs.append("Export stopped by user during archive download.")
            break

          # Update progress bar after completing each bucket
          self.progress_bar.setValue(i)
          percentage = int((i / total_buckets) * 100)
          self.progress_bar.setFormat(f"Overall Progress: {percentage}%")
          QApplication.processEvents()

      # Finalize export
      self.logs.append("Export completed successfully or stopped.")
      self.stop_button.hide()  # Hide stop button
      self.archives_section.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExporterApp()
    window.show()
    sys.exit(app.exec_())