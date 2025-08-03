"""
Additional methods for ExportComponent - separated to manage file size
This file contains the business logic methods for the export component
"""
from PyQt5.QtWidgets import QCheckBox, QFileDialog, QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtCore import Qt


class ExportMethods:
    """Mixin class containing export-related methods."""

    def reset_filters(self):
        """Reset all filter controls to default values."""
        self.is_archived_check.setChecked(False)
        self.with_partners_check.setChecked(False)
        self.with_stacked_check.setChecked(False)
        self.is_favorite_check.setChecked(False)
        self.is_trashed_check.setChecked(False)
        self.visibility_none.setChecked(True)
        self.timeline_main_area.order_button.setText("↓")
        self.download_per_bucket.setChecked(True)

    def hide_export_ui(self):
        """Hide timeline export-related UI elements."""
        self.bucket_list_label.hide()
        self.bucket_scroll_area.hide()
        self.timeline_main_area.order_label.hide()
        self.timeline_main_area.order_button.hide()

        for main_area in [self.timeline_main_area, self.albums_main_area]:
            main_area.export_button.hide()
            main_area.stop_button.hide()
            main_area.resume_button.hide()
            main_area.archives_section.hide()
            main_area.progress_bar.hide()

            main_area.archives_display.hide()
            main_area.current_download_progress_bar.hide()

            # Hide output directory elements
            main_area.output_dir_label.hide()
            main_area.output_dir_button.hide()

    def toggle_timeline_order(self):
        """Toggle sort order between ascending and descending."""
        if self.timeline_main_area.order_button.text() == "↓":
            self.timeline_main_area.order_button.setText("↑")
            self.timeline_main_area.order_button.setToolTip("Currently: ascending/oldest first (click to change)")
        else:
            self.timeline_main_area.order_button.setText("↓")
            self.timeline_main_area.order_button.setToolTip("Currently: descending/newest first (click to change)")

        # Refresh buckets if they are already fetched
        if hasattr(self, 'buckets') and self.buckets:
            self.fetch_buckets()

    def get_archive_size_in_bytes(self):
        """Get archive size in bytes from the input field."""
        size_in_gb = self.archive_size_field.text()
        if not size_in_gb.isdigit():
            if self.logger:
                self.logger.append("Invalid archive size input. Please enter a valid number in GB.")
            return None
        return int(size_in_gb) * 1024 ** 3

    def select_output_dir(self, main_area: QWidget):
        """Open dialog to select output directory."""
        main_area.output_dir = QFileDialog.getExistingDirectory(main_area, "Select Output Directory")
        if main_area.output_dir:
            if self.logger:
                self.logger.append(f"Selected Output Directory: {main_area.output_dir}")
            main_area.output_dir_label.setText(
                f"<span><span style='color: red;'>*</span> Output Directory: <b>{main_area.output_dir}</b></span>"
            )
            main_area.output_dir_label.setStyleSheet("")
        else:
            if self.logger:
                self.logger.append("No directory selected.")
            main_area.output_dir_label.setText("<span style='color: red;'>* Output Directory (required):</span>")

    def validate_fetch_inputs(self):
        """Validate inputs for fetching buckets (only archive size required)."""
        is_valid = True
        self.archive_size_label.setStyleSheet("")
        self.archive_size_field.setStyleSheet("")

        archive_size_bytes = self.get_archive_size_in_bytes()
        if archive_size_bytes is None:
            if self.logger:
                self.logger.append("Error: Archive size must be specified in GB.")
            self.archive_size_label.setStyleSheet("color: red; font-weight: bold;")
            self.archive_size_field.setStyleSheet("border: 2px solid red;")
            is_valid = False

        return is_valid

    def validate_export_inputs(self, main_area: QWidget):
        """Validate inputs for export (archive size and output directory required)."""
        is_valid = True
        if main_area.objectName() == "albums_main_area":
            return is_valid # No validation for albums for now

        self.archive_size_label.setStyleSheet("")
        self.archive_size_field.setStyleSheet("")
        main_area.output_dir_label.setStyleSheet("")

        archive_size_bytes = self.get_archive_size_in_bytes()
        if archive_size_bytes is None:
            if self.logger:
                self.logger.append("Error: Archive size must be specified in GB.")
            self.archive_size_label.setStyleSheet("color: red; font-weight: bold;")
            self.archive_size_field.setStyleSheet("border: 2px solid red;")
            is_valid = False

        if not main_area.output_dir:
            if self.logger:
                self.logger.append("Error: Output directory must be selected.")
            main_area.output_dir_label.setStyleSheet("color: red; font-weight: bold;")
            is_valid = False

        return is_valid

    def get_user_input_values(self):
        """Get current user input values for filters and settings."""
        return {
            "is_archived": self.is_archived_check.isChecked(),
            "with_partners": self.with_partners_check.isChecked(),
            "with_stacked": self.with_stacked_check.isChecked(),
            "is_favorite": self.is_favorite_check.isChecked(),
            "is_trashed": self.is_trashed_check.isChecked(),
            "visibility": self.get_visibility_value(),
            "order": "asc" if self.timeline_main_area.order_button.text() == "↑" else "desc"
        }

    def stop_flag(self):
        """Return current stop flag status."""
        return self.stop_requested

    def populate_bucket_list(self, buckets):
        """Populate the bucket list UI with fetched buckets."""
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
        """Toggle selection of all buckets."""
        for i in range(1, self.bucket_list_layout.count()):
            checkbox = self.bucket_list_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(state == Qt.Checked)

    def get_selected_buckets(self):
        """Get list of selected bucket IDs."""
        return [
            self.bucket_list_layout.itemAt(i).widget().objectName()
            for i in range(1, self.bucket_list_layout.count())
            if isinstance(self.bucket_list_layout.itemAt(i).widget(), QCheckBox) and
            self.bucket_list_layout.itemAt(i).widget().isChecked()
        ]

    def open_output_folder(self, main_area: QWidget):
        """Open the output directory in the file manager."""
        if main_area.output_dir:
            import webbrowser
            webbrowser.open(f"file://{main_area.output_dir}")
            if self.logger:
                self.logger.append(f"Opening output directory: {main_area.output_dir}")
        else:
            if self.logger:
                self.logger.append("No output directory set. Please choose an output directory first.")

    def stop_export(self, main_area: QWidget = None):
        """Stop the current export process."""
        if self.logger:
            self.logger.append("Stop requested. Stopping export process...")
        self.stop_requested = True
        all_main_areas = [main_area] if main_area else [self.timeline_main_area, self.albums_main_area]
        for _main_area in all_main_areas:
            _main_area.stop_button.hide()
            _main_area.export_button.show()

            # Show output directory button when export is stopped
            _main_area.output_dir_button.show()
            _main_area.progress_bar.hide()
            _main_area.current_download_progress_bar.hide()

        # Re-enable tab switching when export is stopped
        self.reset_export_state()

    def setup_progress_bar(self, main_area: QWidget, total):
        """Setup the main progress bar."""
        main_area.progress_bar.setRange(0, total)
        main_area.progress_bar.setValue(0)
        main_area.progress_bar.setTextVisible(True)
        main_area.progress_bar.setFormat("Overall Progress: 0%")
        main_area.progress_bar.show()

    def update_progress_bar(self, main_area: QWidget, current, total):
        """Update the progress bar with current progress."""
        main_area.progress_bar.setValue(current)
        percentage = int((current / total) * 100)
        main_area.progress_bar.setFormat(f"Overall Progress: {percentage}%")

    def finalize_export(self, main_area: QWidget):
        """Finalize the export process."""
        if self.logger:
            self.logger.append("Export completed successfully or stopped.")
        main_area.stop_button.hide()
        main_area.export_button.show()
        main_area.archives_section.show()

        # Show output directory button when export is finalized
        main_area.output_dir_button.show()

        # Re-enable tab switching
        self.export_in_progress = False
        self.tab_widget.setEnabled(True)

        self.export_finished.emit()

    def setup_album_tab(self):
        album_tab = QWidget()
        album_layout = QVBoxLayout()

        # Album list widget
        self.album_list = QListWidget()
        self.album_list.setSelectionMode(QListWidget.MultiSelection)
        album_layout.addWidget(self.album_list)

        # Refresh button
        fetch_button = QPushButton("Fetch Albums")
        fetch_button.clicked.connect(self.fetch_albums)
        album_layout.addWidget(fetch_button)

        album_tab.setLayout(album_layout)
        return album_tab

    def fetch_albums(self):
        self.album_list.clear()
        if not self.export_manager:
            return

        try:
            albums = self.export_manager.get_albums()
            for album in albums:
                item = QListWidgetItem()
                widget = self.create_album_item_widget(album)
                item.setSizeHint(widget.sizeHint())
                self.album_list.addItem(item)
                self.album_list.setItemWidget(item, widget)
        except Exception as e:
            if self.logger:
                self.logger.append(f"Failed to fetch albums: {str(e)}")

    def create_album_item_widget(self, album):
        widget = QWidget()
        layout = QHBoxLayout()

        # Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        layout.addWidget(checkbox)

        # Album info
        info_layout = QVBoxLayout()

        # Album name and count
        name_label = QLabel(f"{album['albumName']} ({album['assetCount']} assets)")
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_label)

        # Album dates if available
        if 'startDate' in album and 'endDate' in album:
            date_label = QLabel(f"From {album['startDate'][:10]} to {album['endDate'][:10]}")
            date_label.setStyleSheet("color: gray;")
            info_layout.addWidget(date_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Asset count
        count_label = QLabel(f"{album['assetCount']}")
        count_label.setStyleSheet("color: gray;")
        layout.addWidget(count_label)

        widget.setLayout(layout)
        return widget

    def get_selected_albums(self):
        selected_albums = []
        for i in range(self.album_list.count()):
            item = self.album_list.item(i)
            widget = self.album_list.itemWidget(item)
            checkbox = widget.layout().itemAt(0).widget()  # Get the checkbox
            if checkbox.isChecked():
                album_name = widget.layout().itemAt(1).itemAt(0).widget().text()  # Get the album name label
                album_name = album_name.split(" (")[0]  # Remove the asset count from the name
                selected_albums.append(album_name)
        return selected_albums