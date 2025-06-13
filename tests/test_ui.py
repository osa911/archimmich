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

    # Test new UI elements initialization
    assert main_window.is_favorite_check.text() == "Is Favorite?"
    assert not main_window.is_favorite_check.isChecked()
    assert main_window.is_trashed_check.text() == "Is Trashed?"
    assert not main_window.is_trashed_check.isChecked()

    # Test visibility combo initialization
    assert main_window.visibility_combo.count() == 5
    assert main_window.visibility_combo.itemText(0) == "Not specified"
    assert main_window.visibility_combo.itemText(1) == "Archive"
    assert main_window.visibility_combo.itemText(2) == "Timeline"
    assert main_window.visibility_combo.itemText(3) == "Hidden"
    assert main_window.visibility_combo.itemText(4) == "Locked"
    assert main_window.visibility_combo.currentText() == "Not specified"

    # Test order button initialization
    assert main_window.order_button.text() == "↓"  # Default is descending
    assert "descending" in main_window.order_button.toolTip().lower()

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

def test_server_version_display(main_window, qtbot):
    """Test if server version is displayed correctly after login."""
    # Mock the login manager and API manager
    with patch.object(main_window.login_manager, 'login') as mock_login, \
         patch.object(main_window.login_manager, 'getApiManager') as mock_get_api_manager:

        # Setup mock responses
        mock_login.return_value = {"name": "Test User", "email": "test@example.com"}
        mock_api = MagicMock()
        mock_api.get_server_info.return_value = {
            "version": "v1.134.0",
            "build": "15281783550"
        }
        mock_get_api_manager.return_value = mock_api

        # Fill in login fields
        main_window.server_ip_field.setText("http://localhost")
        main_window.api_key_field.setText("test-key")

        # Click login button
        login_button = main_window.login_widget.findChild(QPushButton, "login_button")
        qtbot.mouseClick(login_button, Qt.LeftButton)

        # Check if version is displayed
        assert main_window.server_version_label.text() == "Server version: v1.134.0"

def test_server_version_cleared_on_logout(main_window, qtbot):
    """Test if server version is cleared when logging out."""
    # First login
    with patch.object(main_window.login_manager, 'login') as mock_login, \
         patch.object(main_window.login_manager, 'getApiManager') as mock_get_api_manager:

        mock_login.return_value = {"name": "Test User", "email": "test@example.com"}
        mock_api = MagicMock()
        mock_api.get_server_info.return_value = {"version": "v1.134.0"}
        mock_get_api_manager.return_value = mock_api

        main_window.server_ip_field.setText("http://localhost")
        main_window.api_key_field.setText("test-key")
        login_button = main_window.login_widget.findChild(QPushButton, "login_button")
        qtbot.mouseClick(login_button, Qt.LeftButton)

        # Verify version is displayed
        assert main_window.server_version_label.text() == "Server version: v1.134.0"

        # Now logout
        main_window.logout()

        # Verify version is cleared
        assert main_window.server_version_label.text() == ""

def test_toggle_order_button(main_window, qtbot):
    """Test the order toggle button functionality."""
    # Initial state should be descending (↓)
    assert main_window.order_button.text() == "↓"

    # Click to change to ascending
    qtbot.mouseClick(main_window.order_button, Qt.LeftButton)
    assert main_window.order_button.text() == "↑"

    # Click again to change back to descending
    qtbot.mouseClick(main_window.order_button, Qt.LeftButton)
    assert main_window.order_button.text() == "↓"

def test_visibility_combo_selection(main_window):
    """Test visibility combo box selection."""
    # Test each visibility option
    test_cases = [
        ("Not specified", ""),
        ("Archive", "archive"),
        ("Timeline", "timeline"),
        ("Hidden", "hidden"),
        ("Locked", "locked")
    ]

    for display_text, value in test_cases:
        index = main_window.visibility_combo.findText(display_text)
        main_window.visibility_combo.setCurrentIndex(index)
        assert main_window.visibility_combo.currentText() == display_text
        assert main_window.visibility_combo.currentData() == value

def test_fetch_with_filters(main_window, qtbot):
    """Test that fetch operation includes all filter values."""
    with patch.object(main_window, 'fetch_buckets') as mock_fetch:
        # Setup filter values
        main_window.is_favorite_check.setChecked(True)
        main_window.is_trashed_check.setChecked(True)
        main_window.visibility_combo.setCurrentText("Archive")
        qtbot.mouseClick(main_window.order_button, Qt.LeftButton)  # Set to ascending

        # Trigger fetch
        main_window.fetch_button.click()

        # Get the values that were passed to fetch_buckets
        inputs = main_window.get_user_input_values()
        assert inputs["is_favorite"] is True
        assert inputs["is_trashed"] is True
        assert inputs["visibility"] == "archive"
        assert inputs["order"] == "asc"

def test_filter_state_after_logout(main_window):
    """Test that filters are reset after logout."""
    # Set some filter values
    main_window.is_favorite_check.setChecked(True)
    main_window.is_trashed_check.setChecked(True)
    main_window.visibility_combo.setCurrentText("Archive")
    main_window.order_button.setText("↑")  # Set to ascending

    # Logout
    main_window.logout()

    # Verify filters are reset
    assert not main_window.is_favorite_check.isChecked()
    assert not main_window.is_trashed_check.isChecked()
    assert main_window.visibility_combo.currentText() == "Not specified"
    assert main_window.order_button.text() == "↓"