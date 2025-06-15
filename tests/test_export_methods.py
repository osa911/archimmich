import pytest
from src.ui.components.export_methods import ExportMethods
from PyQt5.QtWidgets import QWidget, QCheckBox, QLineEdit, QLabel, QPushButton, QRadioButton, QButtonGroup
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock, patch


class MockExportMethodsWidget(QWidget, ExportMethods):
    """Mock widget that includes ExportMethods mixin for testing."""

    def __init__(self):
        super().__init__()
        self.logger = MagicMock()
        self.setup_test_controls()

    def setup_test_controls(self):
        """Setup minimal controls needed for testing ExportMethods."""
        # Filter checkboxes
        self.is_archived_check = QCheckBox("Is Archived?")
        self.with_partners_check = QCheckBox("With Partners?")
        self.with_stacked_check = QCheckBox("With Stacked?")
        self.is_favorite_check = QCheckBox("Is Favorite?")
        self.is_trashed_check = QCheckBox("Is Trashed?")

        # Visibility radio buttons
        self.visibility_group = QButtonGroup()
        self.visibility_none = QRadioButton("Not specified")
        self.visibility_archive = QRadioButton("Archive")
        self.visibility_timeline = QRadioButton("Timeline")
        self.visibility_hidden = QRadioButton("Hidden")
        self.visibility_locked = QRadioButton("Locked")

        self.visibility_group.addButton(self.visibility_none)
        self.visibility_group.addButton(self.visibility_archive)
        self.visibility_group.addButton(self.visibility_timeline)
        self.visibility_group.addButton(self.visibility_hidden)
        self.visibility_group.addButton(self.visibility_locked)

        self.visibility_none.setChecked(True)

        # Download option radio buttons
        self.download_group = QButtonGroup()
        self.download_per_bucket = QRadioButton("Per bucket")
        self.download_combined = QRadioButton("Combined")

        self.download_group.addButton(self.download_per_bucket)
        self.download_group.addButton(self.download_combined)
        self.download_per_bucket.setChecked(True)

        # Order button
        self.order_button = QPushButton("↓")

        # Archive size field
        self.archive_size_field = QLineEdit()
        self.archive_size_field.setText("4")
        self.archive_size_label = QLabel("Archive Size (GB):")

        # Output directory
        self.output_dir = ""
        self.output_dir_label = QLabel("Output Directory:")
        self.output_dir_button = QPushButton("Choose Directory")

        # Export controls
        self.export_button = QPushButton("Export")
        self.archives_section = QWidget()
        self.progress_bar = QWidget()
        self.bucket_list_label = QLabel("Buckets:")
        self.bucket_scroll_area = QWidget()
        self.archives_display = QWidget()
        self.current_download_progress_bar = QWidget()

        # For testing get_selected_buckets
        from PyQt5.QtWidgets import QVBoxLayout
        self.bucket_list_layout = QVBoxLayout()

        # Mock stop button
        self.stop_button = QPushButton("Stop")

    def get_visibility_value(self):
        """Get visibility value from radio buttons."""
        if self.visibility_archive.isChecked():
            return "archive"
        elif self.visibility_timeline.isChecked():
            return "timeline"
        elif self.visibility_hidden.isChecked():
            return "hidden"
        elif self.visibility_locked.isChecked():
            return "locked"
        else:
            return ""  # none/not specified


@pytest.fixture
def export_methods_widget(qtbot):
    """Fixture to create test widget with ExportMethods."""
    widget = MockExportMethodsWidget()
    qtbot.addWidget(widget)
    return widget


def test_reset_filters(export_methods_widget):
    """Test that reset_filters sets all controls to default values."""
    # Set some non-default values
    export_methods_widget.is_archived_check.setChecked(True)
    export_methods_widget.with_partners_check.setChecked(True)
    export_methods_widget.is_favorite_check.setChecked(True)
    export_methods_widget.visibility_archive.setChecked(True)
    export_methods_widget.order_button.setText("↑")
    export_methods_widget.download_combined.setChecked(True)

    # Reset filters
    export_methods_widget.reset_filters()

    # Check all are reset to defaults
    assert not export_methods_widget.is_archived_check.isChecked()
    assert not export_methods_widget.with_partners_check.isChecked()
    assert not export_methods_widget.is_favorite_check.isChecked()
    assert export_methods_widget.visibility_none.isChecked()
    assert export_methods_widget.order_button.text() == "↓"
    assert export_methods_widget.download_per_bucket.isChecked()


def test_toggle_order(export_methods_widget):
    """Test order toggle functionality."""
    # Initial state should be descending
    assert export_methods_widget.order_button.text() == "↓"

    # Toggle to ascending
    export_methods_widget.toggle_order()
    assert export_methods_widget.order_button.text() == "↑"

    # Toggle back to descending
    export_methods_widget.toggle_order()
    assert export_methods_widget.order_button.text() == "↓"


def test_get_archive_size_in_bytes_valid(export_methods_widget):
    """Test getting archive size with valid input."""
    export_methods_widget.archive_size_field.setText("4")
    size_bytes = export_methods_widget.get_archive_size_in_bytes()
    expected = 4 * 1024 ** 3  # 4 GB in bytes
    assert size_bytes == expected


def test_get_archive_size_in_bytes_invalid(export_methods_widget):
    """Test getting archive size with invalid input."""
    export_methods_widget.archive_size_field.setText("invalid")
    size_bytes = export_methods_widget.get_archive_size_in_bytes()
    assert size_bytes is None


def test_get_archive_size_in_bytes_empty(export_methods_widget):
    """Test getting archive size with empty input."""
    export_methods_widget.archive_size_field.setText("")
    size_bytes = export_methods_widget.get_archive_size_in_bytes()
    assert size_bytes is None


def test_validate_fetch_inputs_valid(export_methods_widget):
    """Test fetch input validation with valid inputs."""
    export_methods_widget.archive_size_field.setText("4")
    assert export_methods_widget.validate_fetch_inputs()


def test_validate_fetch_inputs_invalid_size(export_methods_widget):
    """Test fetch input validation with invalid archive size."""
    export_methods_widget.archive_size_field.setText("invalid")
    assert not export_methods_widget.validate_fetch_inputs()


def test_validate_export_inputs_valid(export_methods_widget):
    """Test export input validation with valid inputs."""
    export_methods_widget.archive_size_field.setText("4")
    export_methods_widget.output_dir = "/test/output"
    assert export_methods_widget.validate_export_inputs()


def test_validate_export_inputs_no_output_dir(export_methods_widget):
    """Test export input validation without output directory."""
    export_methods_widget.archive_size_field.setText("4")
    export_methods_widget.output_dir = ""
    assert not export_methods_widget.validate_export_inputs()


def test_validate_export_inputs_invalid_size(export_methods_widget):
    """Test export input validation with invalid archive size."""
    export_methods_widget.archive_size_field.setText("invalid")
    export_methods_widget.output_dir = "/test/output"
    assert not export_methods_widget.validate_export_inputs()


def test_get_user_input_values(export_methods_widget):
    """Test getting user input values."""
    # Set some values
    export_methods_widget.is_archived_check.setChecked(True)
    export_methods_widget.is_favorite_check.setChecked(True)
    export_methods_widget.visibility_archive.setChecked(True)
    export_methods_widget.order_button.setText("↑")

    values = export_methods_widget.get_user_input_values()

    assert values["is_archived"] == True
    assert values["is_favorite"] == True
    assert values["visibility"] == "archive"
    assert values["order"] == "asc"


def test_select_output_dir_success(export_methods_widget):
    """Test successful output directory selection."""
    with patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory', return_value="/test/output"):
        export_methods_widget.select_output_dir()

        assert export_methods_widget.output_dir == "/test/output"
        assert "Output Directory: <b>/test/output</b>" in export_methods_widget.output_dir_label.text()


def test_select_output_dir_cancelled(export_methods_widget):
    """Test cancelled output directory selection."""
    initial_dir = export_methods_widget.output_dir

    with patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory', return_value=""):
        export_methods_widget.select_output_dir()

        assert export_methods_widget.output_dir == initial_dir
        assert "required" in export_methods_widget.output_dir_label.text().lower()


def test_open_output_folder_with_directory(export_methods_widget):
    """Test opening output folder when directory is set."""
    export_methods_widget.output_dir = "/test/output"

    with patch('webbrowser.open') as mock_open:
        export_methods_widget.open_output_folder()
        mock_open.assert_called_once_with("file:///test/output")


def test_open_output_folder_no_directory(export_methods_widget):
    """Test opening output folder when no directory is set."""
    export_methods_widget.output_dir = ""

    with patch('webbrowser.open') as mock_open:
        export_methods_widget.open_output_folder()
        mock_open.assert_not_called()


def test_stop_export(export_methods_widget):
    """Test stop export functionality."""
    export_methods_widget.stop_requested = False
    export_methods_widget.stop_export()

    assert export_methods_widget.stop_requested == True


def test_setup_progress_bar(export_methods_widget):
    """Test progress bar setup."""
    # Mock progress bar with necessary methods
    export_methods_widget.progress_bar = MagicMock()

    export_methods_widget.setup_progress_bar(100)

    export_methods_widget.progress_bar.setRange.assert_called_once_with(0, 100)
    export_methods_widget.progress_bar.setValue.assert_called_once_with(0)


def test_update_progress_bar(export_methods_widget):
    """Test progress bar updates."""
    # Mock progress bar with necessary methods
    export_methods_widget.progress_bar = MagicMock()

    export_methods_widget.update_progress_bar(50, 100)

    export_methods_widget.progress_bar.setValue.assert_called_once_with(50)
    export_methods_widget.progress_bar.setFormat.assert_called_once_with("Overall Progress: 50%")


def test_finalize_export(export_methods_widget):
    """Test export finalization."""
    # Mock the export_finished signal
    export_methods_widget.export_finished = MagicMock()

    export_methods_widget.finalize_export()

    export_methods_widget.export_finished.emit.assert_called_once()