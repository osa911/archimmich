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

        # Create timeline main area
        self.timeline_main_area = QWidget()
        self.timeline_main_area.order_button = QPushButton("↓")
        self.timeline_main_area.output_dir = ""
        self.timeline_main_area.output_dir_label = QLabel()
        self.timeline_main_area.output_dir_button = QPushButton()
        self.timeline_main_area.export_button = QPushButton()
        self.timeline_main_area.stop_button = QPushButton()
        self.timeline_main_area.resume_button = QPushButton()
        self.timeline_main_area.progress_bar = MagicMock()
        self.timeline_main_area.current_download_progress_bar = MagicMock()
        self.timeline_main_area.archives_section = QWidget()
        self.timeline_main_area.archives_display = MagicMock()

        # Create albums main area
        self.albums_main_area = QWidget()
        self.albums_main_area.output_dir = ""
        self.albums_main_area.output_dir_label = QLabel()
        self.albums_main_area.output_dir_button = QPushButton()
        self.albums_main_area.export_button = QPushButton()
        self.albums_main_area.stop_button = QPushButton()
        self.albums_main_area.resume_button = QPushButton()
        self.albums_main_area.progress_bar = MagicMock()
        self.albums_main_area.current_download_progress_bar = MagicMock()
        self.albums_main_area.archives_section = QWidget()
        self.albums_main_area.archives_display = MagicMock()

        # Create filter controls
        self.is_archived_check = QCheckBox()
        self.with_partners_check = QCheckBox()
        self.with_stacked_check = QCheckBox()
        self.is_favorite_check = QCheckBox()
        self.is_trashed_check = QCheckBox()
        self.visibility_none = QCheckBox()
        self.download_per_bucket = QCheckBox()
        self.archive_size_field = QLineEdit()
        self.archive_size_field.setText("4")

        # Create visibility radio buttons
        self.visibility_none = QRadioButton("Not specified")
        self.visibility_archive = QRadioButton("Archive")
        self.visibility_timeline = QRadioButton("Timeline")
        self.visibility_hidden = QRadioButton("Hidden")
        self.visibility_locked = QRadioButton("Locked")
        self.visibility_group = QButtonGroup()
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

        # Archive size field
        self.archive_size_label = QLabel("Archive Size (GB):")

        # Output directory
        self.output_dir = ""
        self.output_dir_label = QLabel("Output Directory:")
        self.output_dir_button = QPushButton("Choose Directory")

        # Export controls
        self.bucket_list_label = QLabel("Buckets:")
        self.bucket_scroll_area = QWidget()
        self.current_download_progress_bar = QWidget()

        # For testing get_selected_buckets
        from PyQt5.QtWidgets import QVBoxLayout
        self.bucket_list_layout = QVBoxLayout()

        # Mock stop button
        self.stop_button = QPushButton("Stop")

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
def export_methods_widget():
    """Create a mock widget with ExportMethods."""
    return MockExportMethodsWidget()


def test_reset_filters(export_methods_widget):
    """Test that reset_filters sets all controls to default values."""
    # Set some non-default values
    export_methods_widget.is_archived_check.setChecked(True)
    export_methods_widget.with_partners_check.setChecked(True)
    export_methods_widget.is_favorite_check.setChecked(True)
    export_methods_widget.visibility_archive.setChecked(True)
    export_methods_widget.timeline_main_area.order_button.setText("↑")

    # Reset filters
    export_methods_widget.reset_filters()

    # Verify all controls are reset to default values
    assert not export_methods_widget.is_archived_check.isChecked()
    assert not export_methods_widget.with_partners_check.isChecked()
    assert not export_methods_widget.is_favorite_check.isChecked()
    assert export_methods_widget.visibility_none.isChecked()
    assert export_methods_widget.timeline_main_area.order_button.text() == "↓"


def test_toggle_timeline_order(export_methods_widget):
    """Test order toggle functionality."""
    # Initial state should be descending
    assert export_methods_widget.timeline_main_area.order_button.text() == "↓"

    # Toggle to ascending
    export_methods_widget.toggle_timeline_order()
    assert export_methods_widget.timeline_main_area.order_button.text() == "↑"

    # Toggle back to descending
    export_methods_widget.toggle_timeline_order()
    assert export_methods_widget.timeline_main_area.order_button.text() == "↓"


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

    # Test timeline tab
    export_methods_widget.timeline_main_area.output_dir = "/test/output"
    assert export_methods_widget.validate_export_inputs(export_methods_widget.timeline_main_area)

    # Test albums tab
    export_methods_widget.albums_main_area.output_dir = "/test/output"
    assert export_methods_widget.validate_export_inputs(export_methods_widget.albums_main_area)


def test_validate_export_inputs_no_output_dir(export_methods_widget):
    """Test export input validation with no output directory."""
    export_methods_widget.archive_size_field.setText("4")

    # Test timeline tab
    export_methods_widget.timeline_main_area.output_dir = ""
    assert not export_methods_widget.validate_export_inputs(export_methods_widget.timeline_main_area)

    # Test albums tab
    export_methods_widget.albums_main_area.output_dir = ""
    assert not export_methods_widget.validate_export_inputs(export_methods_widget.albums_main_area)


def test_validate_export_inputs_invalid_size(export_methods_widget):
    """Test export input validation with invalid archive size."""
    export_methods_widget.archive_size_field.setText("invalid")
    export_methods_widget.timeline_main_area.output_dir = "/test/output"
    assert not export_methods_widget.validate_export_inputs(export_methods_widget.timeline_main_area)


def test_get_user_input_values(export_methods_widget):
    """Test getting user input values."""
    # Set some values
    export_methods_widget.is_archived_check.setChecked(True)
    export_methods_widget.is_favorite_check.setChecked(True)
    export_methods_widget.visibility_archive.setChecked(True)
    export_methods_widget.timeline_main_area.order_button.setText("↑")

    values = export_methods_widget.get_user_input_values()
    assert values["is_archived"] is True
    assert values["is_favorite"] is True
    assert values["visibility"] == "archive"
    assert values["order"] == "asc"


def test_select_output_dir_success(export_methods_widget):
    """Test successful output directory selection."""
    with patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory', return_value="/test/output"):
        export_methods_widget.select_output_dir(export_methods_widget.timeline_main_area)
        assert export_methods_widget.timeline_main_area.output_dir == "/test/output"


def test_select_output_dir_cancelled(export_methods_widget):
    """Test cancelled output directory selection."""
    initial_dir = export_methods_widget.timeline_main_area.output_dir

    with patch('PyQt5.QtWidgets.QFileDialog.getExistingDirectory', return_value=""):
        export_methods_widget.select_output_dir(export_methods_widget.timeline_main_area)
        assert export_methods_widget.timeline_main_area.output_dir == initial_dir


def test_open_output_folder_with_directory(export_methods_widget):
    """Test opening output folder when directory is set."""
    export_methods_widget.timeline_main_area.output_dir = "/test/output"

    with patch('webbrowser.open') as mock_open:
        export_methods_widget.open_output_folder(export_methods_widget.timeline_main_area)
        mock_open.assert_called_once_with("file:///test/output")


def test_open_output_folder_no_directory(export_methods_widget):
    """Test opening output folder when no directory is set."""
    export_methods_widget.timeline_main_area.output_dir = ""

    with patch('webbrowser.open') as mock_open:
        export_methods_widget.open_output_folder(export_methods_widget.timeline_main_area)
        mock_open.assert_not_called()


def test_stop_export(export_methods_widget):
    """Test stop export functionality."""
    export_methods_widget.stop_requested = False
    export_methods_widget.stop_export(export_methods_widget.timeline_main_area)
    assert export_methods_widget.stop_requested is True


def test_setup_progress_bar(export_methods_widget):
    """Test progress bar setup."""
    # Mock progress bar with necessary methods
    export_methods_widget.timeline_main_area.progress_bar = MagicMock()

    # Test setup
    total = 100
    export_methods_widget.setup_progress_bar(export_methods_widget.timeline_main_area, total)
    export_methods_widget.timeline_main_area.progress_bar.setRange.assert_called_once_with(0, total)
    export_methods_widget.timeline_main_area.progress_bar.show.assert_called_once()


def test_update_progress_bar(export_methods_widget):
    """Test progress bar updates."""
    # Mock progress bar with necessary methods
    export_methods_widget.timeline_main_area.progress_bar = MagicMock()

    # Test update
    current = 50
    total = 100
    export_methods_widget.update_progress_bar(export_methods_widget.timeline_main_area, current, total)
    export_methods_widget.timeline_main_area.progress_bar.setValue.assert_called_once_with(current)


def test_finalize_export(export_methods_widget):
    """Test export finalization."""
    # Add export_finished signal to mock widget
    export_methods_widget.export_finished = MagicMock()

    # Mock UI components
    export_methods_widget.timeline_main_area.stop_button = MagicMock()
    export_methods_widget.timeline_main_area.export_button = MagicMock()
    export_methods_widget.timeline_main_area.archives_section = MagicMock()
    export_methods_widget.timeline_main_area.output_dir_button = MagicMock()

    # Test finalization
    export_methods_widget.finalize_export(export_methods_widget.timeline_main_area)

    # Verify UI state changes
    export_methods_widget.timeline_main_area.stop_button.hide.assert_called_once()
    export_methods_widget.timeline_main_area.export_button.show.assert_called_once()
    export_methods_widget.timeline_main_area.archives_section.show.assert_called_once()
    export_methods_widget.timeline_main_area.output_dir_button.show.assert_called_once()
    export_methods_widget.export_finished.emit.assert_called_once()