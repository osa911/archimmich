"""
Additional methods for ExportComponent - separated to manage file size
This file contains the business logic methods for the export component
"""
from PyQt5.QtWidgets import QCheckBox, QFileDialog, QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
import time


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
        self.albums_search_input.hide()  # Hide albums search input

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
        """Validate inputs for export (archive size and output directory/cloud config required)."""
        is_valid = True
        main_area.output_dir_label.setStyleSheet("")

        # Check export destination
        export_destination = self.get_export_destination()

        if export_destination == "local":
            # Validate output directory for local export
            if not main_area.output_dir:
                if self.logger:
                    self.logger.append("Error: Output directory must be selected for local export.")
                main_area.output_dir_label.setStyleSheet("color: red; font-weight: bold;")
                is_valid = False
        elif export_destination == "cloud":
            # Validate cloud configuration
            cloud_config = self.get_cloud_configuration()
            if not cloud_config:
                if self.logger:
                    self.logger.append("Error: Cloud storage configuration must be selected.")
                self.cloud_status_label.setStyleSheet("color: red; font-weight: bold;")
                is_valid = False
            else:
                self.cloud_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

            # Ensure proper UI state for cloud export - keep cloud message visible, hide directory button
            main_area.output_dir_label.setText("Cloud storage will be used for export")
            main_area.output_dir_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            main_area.output_dir_label.show()
            main_area.output_dir_button.hide()

        # Archive size validation only for timeline tab
        if main_area.objectName() == "timeline_main_area":
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

        # Stop cloud upload if running
        if hasattr(self.export_manager, 'stop_cloud_upload'):
            if self.export_manager.stop_cloud_upload():
                if self.logger:
                    self.logger.append("Cloud upload stopped.")

        all_main_areas = [main_area] if main_area else [self.timeline_main_area, self.albums_main_area]
        for _main_area in all_main_areas:
            _main_area.stop_button.hide()
            _main_area.export_button.show()

            # Show output directory button when export is stopped
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

        # Check if this is cloud or local export based on the main component's radio buttons
        is_cloud_export = (hasattr(self, 'destination_cloud') and
                          self.destination_cloud.isChecked())

        if is_cloud_export:
            # For cloud export, keep cloud message visible but hide directory selection and archives
            main_area.output_dir_label.setText("Cloud storage will be used for export")
            main_area.output_dir_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            main_area.output_dir_label.show()
            main_area.output_dir_button.hide()
            # Hide archives section for cloud exports (not applicable)
            if hasattr(main_area, 'archives_section'):
                main_area.archives_section.hide()
            if hasattr(main_area, 'archives_display'):
                main_area.archives_display.hide()
        else:
            # For local export, show directory button and archives section
            main_area.archives_section.show()
            main_area.output_dir_button.show()
            # Restore the selected directory path display
            if hasattr(main_area, 'output_dir') and main_area.output_dir:
                main_area.output_dir_label.setText(
                    f"<span><span style='color: red;'>*</span> Output Directory: <b>{main_area.output_dir}</b></span>"
                )
                main_area.output_dir_label.setStyleSheet("")
                main_area.output_dir_label.show()

        # Re-enable tab switching
        self.export_in_progress = False
        self.tab_widget.tabBar().setEnabled(True)

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

    def load_cloud_configurations(self):
        """Load existing cloud storage configurations."""
        try:
            configurations = self.cloud_storage_settings.list_configurations()

            # Update the cloud provider combo (it's in the sidebar, not main area)
            if hasattr(self, 'cloud_provider_combo'):
                self.cloud_provider_combo.clear()

                if configurations:
                    for config in configurations:
                        self.cloud_provider_combo.addItem(config['display_name'], config['name'])
                    self.cloud_provider_combo.setCurrentIndex(0)

                    # Enable edit and delete buttons since we have presets
                    if hasattr(self, 'edit_preset_button'):
                        self.edit_preset_button.setEnabled(True)
                    if hasattr(self, 'delete_preset_button'):
                        self.delete_preset_button.setEnabled(True)
                else:
                    self.cloud_provider_combo.addItem("No presets available")
                    self.cloud_provider_combo.setEnabled(True)  # Keep enabled for configuration

                    # Disable edit and delete buttons since no presets
                    if hasattr(self, 'edit_preset_button'):
                        self.edit_preset_button.setEnabled(False)
                    if hasattr(self, 'delete_preset_button'):
                        self.delete_preset_button.setEnabled(False)

            # Update status
            self.update_cloud_status()

        except Exception as e:
            if self.logger:
                self.logger.append(f"Error loading cloud configurations: {str(e)}")

    def on_destination_changed(self, button):
        """Handle destination selection change."""
        is_cloud = button == self.destination_cloud
        self.cloud_config_layout.parent().setVisible(is_cloud)

        # Update output directory visibility and archives section
        for main_area in [self.timeline_main_area, self.albums_main_area]:
            if is_cloud:
                main_area.output_dir_label.setText("Cloud storage will be used for export")
                main_area.output_dir_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                main_area.output_dir_button.hide()
                # Hide archives section for cloud exports (not applicable)
                if hasattr(main_area, 'archives_section'):
                    main_area.archives_section.hide()
                if hasattr(main_area, 'archives_display'):
                    main_area.archives_display.hide()
            else:
                # Only show directory selection if data has been fetched
                data_fetched = (hasattr(main_area, 'buckets_fetched') and main_area.buckets_fetched) or \
                              (hasattr(main_area, 'albums_fetched') and main_area.albums_fetched)

                if data_fetched:
                    main_area.output_dir_label.setText("<span><span style='color: red;'>*</span> Select output directory:</span>")
                    main_area.output_dir_label.setStyleSheet("")
                    main_area.output_dir_button.show()
                    # Show archives section for local exports when data is fetched
                    if hasattr(main_area, 'archives_section'):
                        main_area.archives_section.show()
                    if hasattr(main_area, 'archives_display'):
                        main_area.archives_display.show()
                else:
                    # Hide directory selection until data is fetched
                    main_area.output_dir_label.hide()
                    main_area.output_dir_button.hide()
                    # Also hide archives section until data is fetched
                    if hasattr(main_area, 'archives_section'):
                        main_area.archives_section.hide()
                    if hasattr(main_area, 'archives_display'):
                        main_area.archives_display.hide()

    def on_cloud_provider_changed(self, text):
        """Handle cloud provider selection change."""
        self.update_cloud_status()

        # Enable/disable edit and delete buttons based on selection
        has_selection = bool(text and text != "No presets available")

        # Update buttons (they're in the sidebar)
        if hasattr(self, 'edit_preset_button'):
            self.edit_preset_button.setEnabled(has_selection)
        if hasattr(self, 'delete_preset_button'):
            self.delete_preset_button.setEnabled(has_selection)

    def update_cloud_status(self):
        """Update cloud storage status display."""
        # Update status (cloud status label is in the sidebar)
        if hasattr(self, 'cloud_provider_combo') and hasattr(self, 'cloud_status_label'):
            current_text = self.cloud_provider_combo.currentText()
            if current_text and current_text != "No presets available":
                # Get the configuration to show provider type
                current_name = self.cloud_provider_combo.currentData()
                if current_name:
                    try:
                        config = self.cloud_storage_settings.load_configuration(current_name)
                        if config:
                            provider_type = config.get('type', 'unknown').upper()
                            if provider_type == 'WEBDAV':
                                provider_type = 'WebDAV'
                            elif provider_type == 'S3':
                                provider_type = 'S3'

                            self.cloud_status_label.setText(f"✓ Using: {current_text} ({provider_type})")
                            self.cloud_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                        else:
                            self.cloud_status_label.setText(f"✓ Using: {current_text}")
                            self.cloud_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                    except:
                        self.cloud_status_label.setText(f"✓ Using: {current_text}")
                        self.cloud_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                else:
                    self.cloud_status_label.setText(f"✓ Using: {current_text}")
                    self.cloud_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.cloud_status_label.setText("No cloud storage configured")
                self.cloud_status_label.setStyleSheet("color: #666; font-style: italic;")

    def add_new_preset(self):
        """Add a new cloud storage preset."""
        try:
            # Import here to avoid circular imports
            from src.ui.components.cloud_storage_dialog import CloudStorageDialog

            # Open configuration dialog with no existing config
            dialog = CloudStorageDialog(self, None)
            dialog.configuration_saved.connect(self.on_cloud_configuration_saved)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open cloud storage configuration: {str(e)}")

    def edit_selected_preset(self):
        """Edit the currently selected preset."""
        try:
            # Import here to avoid circular imports
            from src.ui.components.cloud_storage_dialog import CloudStorageDialog

            # Get current selection
            current_name = self.cloud_provider_combo.currentData()
            if not current_name or current_name == "No presets available":
                QMessageBox.warning(self, "No Selection", "Please select a preset to edit.")
                return

            current_config = self.cloud_storage_settings.load_configuration(current_name)
            if not current_config:
                QMessageBox.warning(self, "Error", "Selected preset not found.")
                return

            # Open configuration dialog with existing config
            dialog = CloudStorageDialog(self, current_config)
            dialog.configuration_saved.connect(lambda config: self.on_cloud_configuration_saved(config, current_name))
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open cloud storage configuration: {str(e)}")

    def delete_selected_preset(self):
        """Delete the currently selected preset."""
        try:
            current_name = self.cloud_provider_combo.currentData()
            if not current_name or current_name == "No presets available":
                QMessageBox.warning(self, "No Selection", "Please select a preset to delete.")
                return

            current_text = self.cloud_provider_combo.currentText()

            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete the preset '{current_text}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Delete the configuration
                if self.cloud_storage_settings.delete_configuration(current_name):
                    # Reload configurations
                    self.load_cloud_configurations()
                    if self.logger:
                        self.logger.append(f"Cloud storage preset deleted: {current_text}")
                else:
                    QMessageBox.warning(self, "Delete Failed", "Failed to delete the preset.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete preset: {str(e)}")

    def configure_cloud_storage(self):
        """Open cloud storage configuration dialog (legacy method for compatibility)."""
        # This method is kept for compatibility but now redirects to edit_selected_preset
        self.edit_selected_preset()

    def on_cloud_configuration_saved(self, config, original_name=None):
        """Handle cloud configuration save."""
        try:
            if original_name:
                # Editing existing preset - always update the existing configuration
                config_name = original_name

                # Get original display name for logging
                original_config = self.cloud_storage_settings.load_configuration(original_name)
                original_display_name = original_config.get('display_name', '') if original_config else ''
                new_display_name = config.get('display_name', '')

                # Save the updated configuration
                if not self.cloud_storage_settings.save_configuration(config_name, config):
                    QMessageBox.warning(self, "Save Failed", "Failed to save cloud storage configuration.")
                    return

                # Log appropriate message
                if self.logger:
                    if new_display_name != original_display_name:
                        self.logger.append(f"Cloud storage configuration renamed from '{original_display_name}' to '{new_display_name}'")
                    else:
                        self.logger.append(f"Cloud storage configuration updated: {new_display_name}")
            else:
                # Creating new preset
                config_name = self._generate_config_name(config)

                # Save the configuration
                if not self.cloud_storage_settings.save_configuration(config_name, config):
                    QMessageBox.warning(self, "Save Failed", "Failed to save cloud storage configuration.")
                    return

                if self.logger:
                    self.logger.append(f"Cloud storage configuration created: {config.get('display_name', 'Unknown')}")

            # Reload configurations
            self.load_cloud_configurations()

            # Select the newly created/updated configuration
            for i in range(self.cloud_provider_combo.count()):
                if self.cloud_provider_combo.itemData(i) == config_name:
                    self.cloud_provider_combo.setCurrentIndex(i)
                    break

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save cloud storage configuration: {str(e)}")

    def _generate_config_name(self, config):
        """Generate a unique name for the configuration."""
        if config.get('type') == 'webdav':
            username = config.get('username', 'user')
            url = config.get('url', '')
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                return f"webdav_{username}_{domain}"
            except:
                return f"webdav_{username}"
        elif config.get('type') == 's3':
            bucket = config.get('bucket_name', 'bucket')
            endpoint = config.get('endpoint_url', '')
            try:
                from urllib.parse import urlparse
                domain = urlparse(endpoint).netloc
                return f"s3_{bucket}_{domain}"
            except:
                return f"s3_{bucket}"
        else:
            return f"config_{int(time.time())}"

    def get_export_destination(self):
        """Get the current export destination type."""
        return "cloud" if self.destination_cloud.isChecked() else "local"

    def get_cloud_configuration(self):
        """Get the selected cloud storage configuration."""
        if not self.destination_cloud.isChecked():
            return None

        current_name = self.cloud_provider_combo.currentData()
        if not current_name or current_name == "No presets available":
            return None

        return self.cloud_storage_settings.load_configuration(current_name)

    def reset_ui_state_on_error(self, main_area: QWidget):
        """Reset UI state when an error occurs during export."""
        # Show export button, hide stop button
        main_area.export_button.show()
        main_area.stop_button.hide()

        # Check if this is cloud or local export based on the main component's radio buttons
        is_cloud_export = (hasattr(self, 'destination_cloud') and
                          self.destination_cloud.isChecked())

        # Show/hide output directory elements based on export type
        if hasattr(main_area, 'output_dir_button') and hasattr(main_area, 'output_dir_label'):
            if is_cloud_export:
                # For cloud export, keep cloud message visible but hide directory selection and archives
                main_area.output_dir_button.hide()
                main_area.output_dir_label.setText("Cloud storage will be used for export")
                main_area.output_dir_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                main_area.output_dir_label.show()
                # Hide archives section for cloud exports (not applicable)
                if hasattr(main_area, 'archives_section'):
                    main_area.archives_section.hide()
                if hasattr(main_area, 'archives_display'):
                    main_area.archives_display.hide()
            else:
                # For local export, show directory button if data has been fetched
                data_fetched = (hasattr(main_area, 'buckets_fetched') and main_area.buckets_fetched) or \
                              (hasattr(main_area, 'albums_fetched') and main_area.albums_fetched)
                if data_fetched:
                    # Check if a directory has already been selected
                    if hasattr(main_area, 'output_dir') and main_area.output_dir:
                        # Directory already selected, show the selected path
                        main_area.output_dir_label.setText(
                            f"<span><span style='color: red;'>*</span> Output Directory: <b>{main_area.output_dir}</b></span>"
                        )
                    else:
                        # No directory selected yet, show selection prompt
                        main_area.output_dir_label.setText("<span><span style='color: red;'>*</span> Select output directory:</span>")
                    main_area.output_dir_label.setStyleSheet("")
                    main_area.output_dir_label.show()
                    main_area.output_dir_button.show()
                    # Show archives section for local exports
                    if hasattr(main_area, 'archives_section'):
                        main_area.archives_section.show()
                    if hasattr(main_area, 'archives_display'):
                        main_area.archives_display.show()
                else:
                    main_area.output_dir_label.hide()
                    main_area.output_dir_button.hide()
                    # Hide archives section until data is fetched
                    if hasattr(main_area, 'archives_section'):
                        main_area.archives_section.hide()
                    if hasattr(main_area, 'archives_display'):
                        main_area.archives_display.hide()

        # Hide progress bars
        if hasattr(main_area, 'progress_bar'):
            main_area.progress_bar.hide()
        if hasattr(main_area, 'current_download_progress_bar'):
            main_area.current_download_progress_bar.hide()

        # Re-enable tab switching
        self.export_in_progress = False
        if hasattr(self, 'tab_widget'):
            self.tab_widget.tabBar().setEnabled(True)