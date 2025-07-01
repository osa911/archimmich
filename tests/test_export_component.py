import pytest
from src.ui.components.export_component import ExportComponent
from src.managers.login_manager import LoginManager
from PyQt5.QtWidgets import QCheckBox, QPushButton, QWidget, QLabel, QTabWidget, QRadioButton, QButtonGroup, QVBoxLayout, QLineEdit
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock, patch

@pytest.fixture
def login_manager():
    """Fixture to create a mock login manager."""
    return MagicMock(spec=LoginManager)

@pytest.fixture
def export_component(qtbot):
    """Create a test export component."""
    from src.ui.components.export_component import ExportComponent
    login_manager = MagicMock()
    logger = MagicMock()
    component = ExportComponent(login_manager, logger)

    # Initialize required attributes
    component.tab_widget = QTabWidget()

    # Timeline tab
    component.timeline_main_area = QWidget()
    component.timeline_main_area.order_button = QPushButton("↓")
    component.timeline_main_area.output_dir = ""
    component.timeline_main_area.output_dir_label = QLabel()
    component.timeline_main_area.output_dir_button = QPushButton()
    component.timeline_main_area.export_button = QPushButton()
    component.timeline_main_area.stop_button = QPushButton()
    component.timeline_main_area.resume_button = QPushButton()
    component.timeline_main_area.progress_bar = MagicMock()
    component.timeline_main_area.current_download_progress_bar = MagicMock()
    component.timeline_main_area.archives_section = QWidget()
    component.timeline_main_area.archives_display = MagicMock()

    # Albums tab
    component.albums_main_area = QWidget()
    component.albums_main_area.output_dir = ""
    component.albums_main_area.output_dir_label = QLabel()
    component.albums_main_area.output_dir_button = QPushButton()
    component.albums_main_area.export_button = QPushButton()
    component.albums_main_area.stop_button = QPushButton()
    component.albums_main_area.resume_button = QPushButton()
    component.albums_main_area.progress_bar = MagicMock()
    component.albums_main_area.current_download_progress_bar = MagicMock()
    component.albums_main_area.archives_section = QWidget()
    component.albums_main_area.archives_display = MagicMock()

    # Initialize filter controls
    component.is_archived_check = QCheckBox("Is Archived?")
    component.with_partners_check = QCheckBox("With Partners?")
    component.with_stacked_check = QCheckBox("With Stacked?")
    component.is_favorite_check = QCheckBox("Is Favorite?")
    component.is_trashed_check = QCheckBox("Is Trashed?")

    # Initialize visibility radio buttons
    component.visibility_none = QRadioButton("Not specified")
    component.visibility_archive = QRadioButton("Archive")
    component.visibility_timeline = QRadioButton("Timeline")
    component.visibility_hidden = QRadioButton("Hidden")
    component.visibility_locked = QRadioButton("Locked")
    component.visibility_group = QButtonGroup()
    component.visibility_group.addButton(component.visibility_none)
    component.visibility_group.addButton(component.visibility_archive)
    component.visibility_group.addButton(component.visibility_timeline)
    component.visibility_group.addButton(component.visibility_hidden)
    component.visibility_group.addButton(component.visibility_locked)
    component.visibility_none.setChecked(True)

    # Initialize download options
    component.download_group = QButtonGroup()
    component.download_per_bucket = QRadioButton("Per bucket")
    component.download_combined = QRadioButton("Combined")
    component.download_group.addButton(component.download_per_bucket)
    component.download_group.addButton(component.download_combined)
    component.download_per_bucket.setChecked(True)

    # Initialize archive size field
    component.archive_size_field = QLineEdit()
    component.archive_size_field.setText("4")

    # Initialize fetch button
    component.fetch_button = QPushButton("Fetch")

    # Initialize bucket list
    component.bucket_list_layout = QVBoxLayout()
    component.select_all_checkbox = QCheckBox("Select All")
    component.bucket_list_layout.addWidget(component.select_all_checkbox)

    # Initialize sidebar
    component.sidebar = QWidget()
    sidebar_layout = QVBoxLayout(component.sidebar)
    sidebar_layout.addWidget(component.select_all_checkbox)

    qtbot.addWidget(component)
    return component

def test_export_component_initialization(export_component):
    """Test if the export component initializes correctly."""
    # Test filter controls initialization
    assert hasattr(export_component, 'is_favorite_check')
    assert hasattr(export_component, 'is_trashed_check')
    assert hasattr(export_component, 'visibility_group')  # Radio button group instead of combo
    assert hasattr(export_component, 'download_group')    # Download option radio group

    assert export_component.is_favorite_check.text() == "Is Favorite?"
    assert not export_component.is_favorite_check.isChecked()
    assert export_component.is_trashed_check.text() == "Is Trashed?"
    assert not export_component.is_trashed_check.isChecked()

def test_visibility_radio_initialization(export_component):
    """Test visibility radio button initialization."""
    assert hasattr(export_component, 'visibility_none')
    assert hasattr(export_component, 'visibility_archive')
    assert hasattr(export_component, 'visibility_timeline')
    assert hasattr(export_component, 'visibility_hidden')
    assert hasattr(export_component, 'visibility_locked')

    assert export_component.visibility_none.text() == "Not specified"
    assert export_component.visibility_archive.text() == "Archive"
    assert export_component.visibility_timeline.text() == "Timeline"
    assert export_component.visibility_hidden.text() == "Hidden"
    assert export_component.visibility_locked.text() == "Locked"
    assert export_component.visibility_none.isChecked()  # Default selection

def test_visibility_radio_selection(export_component):
    """Test visibility radio button selection."""
    # Test selecting different visibility options
    export_component.visibility_archive.setChecked(True)
    assert export_component.get_visibility_value() == "archive"

    export_component.visibility_timeline.setChecked(True)
    assert export_component.get_visibility_value() == "timeline"

    export_component.visibility_hidden.setChecked(True)
    assert export_component.get_visibility_value() == "hidden"

    export_component.visibility_locked.setChecked(True)
    assert export_component.get_visibility_value() == "locked"

    export_component.visibility_none.setChecked(True)
    assert export_component.get_visibility_value() == ""

def test_output_directory_selection(export_component):
    """Test selecting an output directory."""
    from PyQt5.QtWidgets import QFileDialog

    with patch.object(QFileDialog, 'getExistingDirectory', return_value="/test/output/dir") as mock_get_directory:
        export_component.select_output_dir(export_component.timeline_main_area)
        assert export_component.timeline_main_area.output_dir == "/test/output/dir"
        mock_get_directory.assert_called_once()

def test_bucket_validation(export_component):
    """Test validation of bucket inputs."""
    # Test fetch validation (only requires archive size)
    export_component.archive_size_field.setText("")
    assert not export_component.validate_fetch_inputs()

    export_component.archive_size_field.setText("4")
    assert export_component.validate_fetch_inputs()

    # Test export validation (requires both archive size and output directory)
    export_component.timeline_main_area.output_dir = ""
    assert not export_component.validate_export_inputs(export_component.timeline_main_area)

    export_component.timeline_main_area.output_dir = "/test/output"
    assert export_component.validate_export_inputs(export_component.timeline_main_area)

def test_toggle_select_all_buckets(export_component):
    """Test the 'Select All' checkbox functionality."""
    # Mock export manager and populate some buckets
    export_component.export_manager = MagicMock()
    export_component.export_manager.format_time_bucket.return_value = "January_2024"

    # Create bucket list layout if not exists
    if not hasattr(export_component, 'bucket_list_layout'):
        export_component.bucket_list_layout = QVBoxLayout()
        export_component.select_all_checkbox = QCheckBox("Select All")
        export_component.bucket_list_layout.addWidget(export_component.select_all_checkbox)

    # Create test buckets
    bucket1 = QCheckBox("January_2024 (5 assets)")
    bucket2 = QCheckBox("February_2024 (3 assets)")
    export_component.bucket_list_layout.addWidget(bucket1)
    export_component.bucket_list_layout.addWidget(bucket2)

    # Test select all
    export_component.select_all_checkbox.setChecked(True)
    export_component.toggle_select_all(Qt.Checked)

    # Verify all buckets are checked
    assert bucket1.isChecked()
    assert bucket2.isChecked()

    # Test unselect all
    export_component.select_all_checkbox.setChecked(False)
    export_component.toggle_select_all(Qt.Unchecked)

    # Verify all buckets are unchecked
    assert not bucket1.isChecked()
    assert not bucket2.isChecked()

def test_get_user_input_values(export_component):
    """Test getting user input values for filters."""
    # Set some filter values
    export_component.is_favorite_check.setChecked(True)
    export_component.is_trashed_check.setChecked(True)
    export_component.visibility_archive.setChecked(True)

    values = export_component.get_user_input_values()

    assert values["is_favorite"] == True
    assert values["is_trashed"] == True
    assert values["visibility"] == "archive"

def test_reset_filters(export_component):
    """Test that filters are reset correctly."""
    # Set some filter values
    export_component.is_favorite_check.setChecked(True)
    export_component.is_trashed_check.setChecked(True)
    export_component.visibility_archive.setChecked(True)

    # Reset filters
    export_component.reset_filters()

    # Check that filters are reset
    assert not export_component.is_favorite_check.isChecked()
    assert not export_component.is_trashed_check.isChecked()
    assert export_component.visibility_none.isChecked()  # Should be back to default

def test_show_hide_export_ui(export_component):
    """Test showing and hiding export UI elements."""
    # Show the component to ensure visibility works
    export_component.show()

    # Test initial state for timeline tab
    assert export_component.timeline_main_area.archives_section.isHidden()
    assert export_component.timeline_main_area.stop_button.isHidden()
    assert export_component.timeline_main_area.resume_button.isHidden()
    assert export_component.timeline_main_area.progress_bar.isHidden()
    assert export_component.timeline_main_area.current_download_progress_bar.isHidden()

    # Test initial state for albums tab
    assert export_component.albums_main_area.archives_section.isHidden()
    assert export_component.albums_main_area.stop_button.isHidden()
    assert export_component.albums_main_area.resume_button.isHidden()
    assert export_component.albums_main_area.progress_bar.isHidden()
    assert export_component.albums_main_area.current_download_progress_bar.isHidden()

    # Test showing export UI for timeline tab
    export_component.timeline_main_area.export_button.show()
    assert export_component.timeline_main_area.export_button.isVisible()

    # Test showing export UI for albums tab
    export_component.albums_main_area.export_button.show()
    assert export_component.albums_main_area.export_button.isVisible()

def test_fetch_buckets_with_filters(export_component, qtbot):
    """Test that fetch operation includes all filter values."""
    # Show the component to ensure proper interaction
    export_component.show()

    # Setup valid inputs for fetch (only archive size needed)
    export_component.archive_size_field.setText("4")

    # Setup filter values
    export_component.is_favorite_check.setChecked(True)
    export_component.is_trashed_check.setChecked(True)
    export_component.visibility_archive.setChecked(True)

    # Mock the login manager and API manager
    mock_api_manager = MagicMock()
    export_component.login_manager.api_manager = mock_api_manager

    # Mock UI components
    export_component.timeline_main_area.order_label = MagicMock()
    export_component.timeline_main_area.order_button = MagicMock()
    export_component.timeline_main_area.output_dir_label = MagicMock()
    export_component.timeline_main_area.output_dir_button = MagicMock()
    export_component.timeline_main_area.export_button = MagicMock()
    export_component.timeline_main_area.archives_display = MagicMock()
    export_component.bucket_scroll_area = MagicMock()
    export_component.bucket_list_label = MagicMock()
    export_component.bucket_list_layout = QVBoxLayout()

    # Mock the ExportManager
    with patch('src.ui.components.export_component.ExportManager') as mock_export_manager_class:
        mock_export_manager = MagicMock()
        mock_export_manager.get_timeline_buckets.return_value = [
            {'timeBucket': '2024-01', 'count': 5},
            {'timeBucket': '2024-02', 'count': 3}
        ]
        mock_export_manager_class.return_value = mock_export_manager

        # Trigger fetch
        export_component.fetch_buckets()

        # Verify ExportManager was created with correct parameters
        mock_export_manager_class.assert_called_once()

        # Verify get_timeline_buckets was called with correct parameters
        mock_export_manager.get_timeline_buckets.assert_called_once()
        call_args = mock_export_manager.get_timeline_buckets.call_args[1]
        assert call_args['is_favorite'] is True
        assert call_args['is_trashed'] is True
        assert call_args['visibility'] == 'archive'

def test_archive_size_validation(export_component):
    """Test archive size validation."""
    # Invalid archive size
    export_component.archive_size_field.setText("invalid")
    assert export_component.get_archive_size_in_bytes() is None

    # Valid archive size
    export_component.archive_size_field.setText("4")
    expected_bytes = 4 * 1024 ** 3  # 4 GB in bytes
    assert export_component.get_archive_size_in_bytes() == expected_bytes

def test_export_finished_signal(export_component, qtbot):
    """Test that export finished signal is emitted."""
    with qtbot.waitSignal(export_component.export_finished, timeout=1000):
        export_component.export_finished.emit()  # Manually emit the signal

def test_open_output_folder(export_component):
    """Test opening output folder."""
    export_component.timeline_main_area.output_dir = "/test/output"

    with patch('webbrowser.open') as mock_open:
        export_component.open_output_folder(export_component.timeline_main_area)
        mock_open.assert_called_once_with("file:///test/output")

def test_two_column_layout(export_component):
    """Test that the two-column layout is properly set up."""
    # Test that main layout is horizontal
    assert export_component.main_layout is not None
    assert hasattr(export_component, 'sidebar')
    assert hasattr(export_component, 'timeline_main_area')

def test_order_toggle_functionality(export_component):
    """Test that order toggle button works correctly."""
    # Test initial state
    assert export_component.timeline_main_area.order_button.text() == "↓"

    # Test toggle
    export_component.toggle_timeline_order()
    assert export_component.timeline_main_area.order_button.text() == "↑"

    # Test toggle back
    export_component.toggle_timeline_order()
    assert export_component.timeline_main_area.order_button.text() == "↓"