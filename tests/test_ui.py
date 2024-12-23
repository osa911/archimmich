import pytest
from src.ui.main_window import MainWindow
from PyQt5.QtWidgets import (QApplication, QFileDialog, QCheckBox, QPushButton)
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt

@pytest.fixture
def main_window(qtbot):
    """Fixture to initialize the MainWindow."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


def test_ui_initialization(main_window):
    """Test if the main window initializes correctly."""
    assert main_window.windowTitle() == "ArchImmich"
    assert main_window.server_ip_field.placeholderText() == "Enter server IP (e.g., http://192.168.1.1:2283)"
    assert main_window.api_key_field.placeholderText() == "Enter API key"
    assert main_window.is_remember_me_checkbox.text() == "Remember me"

def test_login_button_click(main_window, qtbot):
    """Test if the login button triggers the login method."""
    # Ensure login button exists by object name
    login_button = main_window.login_widget.findChild(QPushButton, "login_button")
    assert login_button is not None, "Login button not found in the login widget."

    # Simulate a button click
    with qtbot.waitSignal(main_window.login_status.windowTitleChanged, timeout=1000, raising=False):
        qtbot.mouseClick(login_button, Qt.LeftButton)

def test_output_directory_selection(main_window):
    """Test selecting an output directory."""
    with patch.object(QFileDialog, 'getExistingDirectory', return_value="/test/output/dir") as mock_get_directory:
        main_window.select_output_dir()

        # Assert that QFileDialog.getExistingDirectory was called
        mock_get_directory.assert_called_once()

        # Assert that the output_dir was set correctly
        assert main_window.output_dir == "/test/output/dir"

        # Verify the label was updated correctly
        assert "Output Directory: <b>/test/output/dir</b>" in main_window.output_dir_label.text()


def test_toggle_select_all_buckets(main_window):
    """Test the 'Select All' checkbox functionality."""
    main_window.export_manager = MagicMock()
    main_window.export_manager.format_time_bucket.return_value = "January_2024"

    main_window.populate_bucket_list([
        {'timeBucket': '2024-01', 'count': 5},
        {'timeBucket': '2024-02', 'count': 3}
    ])

    main_window.select_all_checkbox.setChecked(True)
    for i in range(1, main_window.bucket_list_layout.count()):
        checkbox = main_window.bucket_list_layout.itemAt(i).widget()
        if isinstance(checkbox, QCheckBox):
            assert checkbox.isChecked()

    main_window.select_all_checkbox.setChecked(False)
    for i in range(1, main_window.bucket_list_layout.count()):
        checkbox = main_window.bucket_list_layout.itemAt(i).widget()
        if isinstance(checkbox, QCheckBox):
            assert not checkbox.isChecked()

def test_validate_login_inputs(main_window):
    """Test validation of login inputs."""
    main_window.api_key_field.setText("")
    main_window.server_ip_field.setText("")
    assert not main_window.validate_login_inputs()

    main_window.api_key_field.setText("test_api_key")
    main_window.server_ip_field.setText("http://localhost")
    assert main_window.validate_login_inputs()


def test_validate_bucket_inputs(main_window):
    """Test validation of bucket inputs."""
    main_window.archive_size_field.setText("")
    main_window.output_dir = ""
    assert not main_window.validate_bucket_inputs()

    main_window.archive_size_field.setText("4")
    main_window.output_dir = "/test/output/dir"
    assert main_window.validate_bucket_inputs()