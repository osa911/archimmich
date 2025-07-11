"""
Additional methods for ExportComponent - separated to manage file size
This file contains the business logic methods for the export component
"""
from PyQt5.QtWidgets import QApplication, QCheckBox, QFileDialog
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
        self.order_button.setText("↓")
        self.download_per_bucket.setChecked(True)

    def hide_export_ui(self):
        """Hide export-related UI elements."""
        self.export_button.hide()
        self.resume_button.hide()
        self.archives_section.hide()
        self.progress_bar.hide()
        self.bucket_list_label.hide()
        self.bucket_scroll_area.hide()
        self.archives_display.hide()
        self.current_download_progress_bar.hide()

        # Hide order controls
        self.order_label.hide()
        self.order_button.hide()

        # Hide output directory elements
        self.output_dir_label.hide()
        self.output_dir_button.hide()

    def show_export_ui(self):
        """Show export-related UI elements."""
        pass  # Archives display is now shown when buckets are fetched

    def toggle_order(self):
        """Toggle sort order between ascending and descending."""
        if self.order_button.text() == "↓":
            self.order_button.setText("↑")
            self.order_button.setToolTip("Currently: ascending/oldest first (click to change)")
        else:
            self.order_button.setText("↓")
            self.order_button.setToolTip("Currently: descending/newest first (click to change)")

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

    def select_output_dir(self):
        """Open dialog to select output directory."""
        self.output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if self.output_dir:
            if self.logger:
                self.logger.append(f"Selected Output Directory: {self.output_dir}")
            self.output_dir_label.setText(
                f"<span><span style='color: red;'>*</span> Output Directory: <b>{self.output_dir}</b></span>"
            )
            self.output_dir_label.setStyleSheet("")
        else:
            if self.logger:
                self.logger.append("No directory selected.")
            self.output_dir_label.setText("<span style='color: red;'>* Output Directory (required):</span>")

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

    def validate_export_inputs(self):
        """Validate inputs for export (archive size and output directory required)."""
        is_valid = True
        self.archive_size_label.setStyleSheet("")
        self.archive_size_field.setStyleSheet("")
        self.output_dir_label.setStyleSheet("")

        archive_size_bytes = self.get_archive_size_in_bytes()
        if archive_size_bytes is None:
            if self.logger:
                self.logger.append("Error: Archive size must be specified in GB.")
            self.archive_size_label.setStyleSheet("color: red; font-weight: bold;")
            self.archive_size_field.setStyleSheet("border: 2px solid red;")
            is_valid = False

        if not self.output_dir:
            if self.logger:
                self.logger.append("Error: Output directory must be selected.")
            self.output_dir_label.setStyleSheet("color: red; font-weight: bold;")
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
            "order": "asc" if self.order_button.text() == "↑" else "desc"
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

    def open_output_folder(self):
        """Open the output directory in the file manager."""
        if self.output_dir:
            import webbrowser
            webbrowser.open(f"file://{self.output_dir}")
            if self.logger:
                self.logger.append(f"Opening output directory: {self.output_dir}")
        else:
            if self.logger:
                self.logger.append("No output directory set. Please choose an output directory first.")

    def stop_export(self):
        """Stop the current export process."""
        if self.logger:
            self.logger.append("Stop requested. Stopping export process...")
        self.stop_requested = True
        self.stop_button.hide()
        self.export_button.show()

        # Show output directory button when export is stopped
        self.output_dir_button.show()

    def setup_progress_bar(self, total):
        """Setup the main progress bar."""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Overall Progress: 0%")
        self.progress_bar.show()

    def update_progress_bar(self, current, total):
        """Update the progress bar with current progress."""
        self.progress_bar.setValue(current)
        percentage = int((current / total) * 100)
        self.progress_bar.setFormat(f"Overall Progress: {percentage}%")

    def finalize_export(self):
        """Finalize the export process."""
        if self.logger:
            self.logger.append("Export completed successfully or stopped.")
        self.stop_button.hide()
        self.export_button.show()
        self.archives_section.show()

        # Show output directory button when export is finalized
        self.output_dir_button.show()

        self.export_finished.emit()

    def validate_inputs(self):
        """Legacy method - redirects to validate_export_inputs for backward compatibility."""
        return self.validate_export_inputs()