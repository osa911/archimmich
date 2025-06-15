import pytest
from src.ui.components.export_component import ExportComponent
from src.managers.login_manager import LoginManager
from PyQt5.QtWidgets import QCheckBox, QPushButton
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock, patch

@pytest.fixture
def login_manager():
    """Fixture to create a mock login manager."""
    return MagicMock(spec=LoginManager)

@pytest.fixture
def export_component(qtbot, login_manager):
    """Fixture to initialize the ExportComponent."""
    component = ExportComponent(login_manager)
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
        export_component.select_output_dir()

        # Assert that QFileDialog.getExistingDirectory was called
        mock_get_directory.assert_called_once()

        # Assert that the output_dir was set correctly
        assert export_component.output_dir == "/test/output/dir"

        # Verify the label was updated correctly
        assert "Output Directory: <b>/test/output/dir</b>" in export_component.output_dir_label.text()

def test_bucket_validation(export_component):
    """Test validation of bucket inputs."""
    # Test fetch validation (only requires archive size)
    export_component.archive_size_field.setText("")
    assert not export_component.validate_fetch_inputs()

    export_component.archive_size_field.setText("4")
    assert export_component.validate_fetch_inputs()

    # Test export validation (requires both archive size and output directory)
    export_component.output_dir = ""
    assert not export_component.validate_export_inputs()

    export_component.output_dir = "/test/output/dir"
    assert export_component.validate_export_inputs()

def test_toggle_select_all_buckets(export_component):
    """Test the 'Select All' checkbox functionality."""
    # Mock export manager and populate some buckets
    export_component.export_manager = MagicMock()
    export_component.export_manager.format_time_bucket.return_value = "January_2024"

    export_component.populate_bucket_list([
        {'timeBucket': '2024-01', 'count': 5},
        {'timeBucket': '2024-02', 'count': 3}
    ])

    # Test select all
    export_component.select_all_checkbox.setChecked(True)
    for i in range(1, export_component.bucket_list_layout.count()):
        checkbox = export_component.bucket_list_layout.itemAt(i).widget()
        if isinstance(checkbox, QCheckBox):
            assert checkbox.isChecked()

    # Test deselect all
    export_component.select_all_checkbox.setChecked(False)
    for i in range(1, export_component.bucket_list_layout.count()):
        checkbox = export_component.bucket_list_layout.itemAt(i).widget()
        if isinstance(checkbox, QCheckBox):
            assert not checkbox.isChecked()

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

    # In the current implementation, sidebar is always visible
    # but the export elements like archives display are initially hidden
    assert export_component.sidebar.isVisible()  # Sidebar is always visible

    # Initially archives display should be hidden
    assert export_component.archives_display.isHidden()

    # Show export UI (this mainly shows buckets when fetched)
    export_component.show_export_ui()
    # Archives display still hidden until buckets are fetched
    assert export_component.archives_display.isHidden()

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

    # Mock the ExportManager
    with patch('src.ui.components.export_component.ExportManager') as mock_export_manager_class:
        mock_export_manager = MagicMock()
        mock_export_manager.get_timeline_buckets.return_value = [
            {'timeBucket': '2024-01', 'count': 5},
            {'timeBucket': '2024-02', 'count': 3}
        ]
        mock_export_manager_class.return_value = mock_export_manager

        # Trigger fetch by clicking the button
        qtbot.mouseClick(export_component.fetch_button, Qt.LeftButton)

        # Verify that the export manager was created and get_timeline_buckets was called
        mock_export_manager_class.assert_called_once()
        mock_export_manager.get_timeline_buckets.assert_called_once_with(
            is_archived=False,  # Default value
            with_partners=False,  # Default value
            with_stacked=False,  # Default value
            visibility="archive",  # We set this
            is_favorite=True,  # We set this
            is_trashed=True,  # We set this
            order="desc"  # Default order
        )

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
    export_component.output_dir = "/test/output"

    with patch('webbrowser.open') as mock_open:
        export_component.open_output_folder()
        mock_open.assert_called_once_with("file:///test/output")

def test_two_column_layout(export_component):
    """Test that the two-column layout is properly set up."""
    # Test that main layout is horizontal
    assert export_component.main_layout is not None

    # Test that sidebar and main area exist
    assert hasattr(export_component, 'sidebar')
    assert hasattr(export_component, 'main_area')

    # Test that sidebar has expected controls
    assert hasattr(export_component, 'is_archived_check')
    assert hasattr(export_component, 'with_partners_check')
    assert hasattr(export_component, 'archive_size_field')

    # Test that main area has expected controls
    assert hasattr(export_component, 'fetch_button')
    assert hasattr(export_component, 'bucket_list_label')

def test_divider_creation(export_component):
    """Test that the divider components are properly created."""
    # The export component should have dividers imported
    from src.ui.components.divider_factory import HorizontalDivider, VerticalDivider

    # Test that we can create dividers (this tests the import structure)
    h_divider = HorizontalDivider()
    v_divider = VerticalDivider()

    assert h_divider is not None
    assert v_divider is not None

def test_order_toggle_functionality(export_component):
    """Test that order toggle button works correctly."""
    # Test initial state
    assert export_component.order_button.text() == "↓"

    # Test toggle
    export_component.toggle_order()
    assert export_component.order_button.text() == "↑"

    # Test toggle back
    export_component.toggle_order()
    assert export_component.order_button.text() == "↓"