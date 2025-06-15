import pytest
from src.ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from unittest.mock import MagicMock, patch

@pytest.fixture
def main_window(qtbot):
    """Fixture to initialize the MainWindow."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_main_window_initialization(main_window):
    """Test if the main window initializes correctly."""
    assert main_window.windowTitle() == "ArchImmich"
    assert hasattr(main_window, 'login_component')
    assert hasattr(main_window, 'export_component')
    assert hasattr(main_window, 'logger')
    assert hasattr(main_window, 'login_manager')

def test_main_window_layout(main_window):
    """Test the main window layout structure."""
    # Show the main window to ensure proper visibility
    main_window.show()

    # Check that header is initially hidden
    assert main_window.header_widget.isHidden()

    # Check that login container is visible initially
    assert main_window.login_container.isVisible()

    # Check that export component is hidden initially
    assert main_window.export_component.isHidden()

def test_login_successful_flow(main_window):
    """Test the UI changes when login is successful."""
    # Show the main window to ensure proper visibility
    main_window.show()

    # Mock user data
    user_data = {
        'user': {'name': 'Test User', 'email': 'test@example.com'},
        'server_version': 'v1.134.0',
        'avatar_fetcher': None
    }

    # Trigger login successful
    main_window.on_login_successful(user_data)

    # Check UI state changes
    assert main_window.header_widget.isVisible()
    assert main_window.login_container.isHidden()
    assert main_window.export_component.isVisible()
    assert "Test User" in main_window.login_status.text()
    assert "Server: v1.134.0" in main_window.server_version_label.text()

def test_logout_flow(main_window):
    """Test the UI changes when logout occurs."""
    # Show the main window to ensure proper visibility
    main_window.show()

    # First simulate login
    user_data = {
        'user': {'name': 'Test User', 'email': 'test@example.com'},
        'server_version': '1.134.0',
        'avatar_fetcher': None
    }
    main_window.on_login_successful(user_data)

    # Now logout
    main_window.logout()

    # Check UI state changes
    assert main_window.header_widget.isHidden()
    assert main_window.login_container.isVisible()
    assert main_window.export_component.isHidden()
    assert main_window.login_status.text() == ""
    assert main_window.server_version_label.text() == ""

def test_debug_settings_dialog(main_window):
    """Test that debug settings dialog can be opened."""
    with patch('src.ui.main_window.DebugSettingsDialog') as mock_dialog:
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value = mock_dialog_instance

        main_window.show_debug_settings()

        mock_dialog.assert_called_once_with(main_window.config, main_window)
        mock_dialog_instance.exec_.assert_called_once()

def test_logger_integration(main_window):
    """Test that logger is properly integrated."""
    test_message = "Test log message"
    main_window.log(test_message)

    # Check that message appears in logs widget
    logs_content = main_window.logs.toPlainText()
    assert test_message in logs_content

def test_load_saved_settings(main_window):
    """Test loading saved settings."""
    with patch('src.ui.main_window.load_settings') as mock_load:
        mock_load.return_value = ("192.168.1.1", "test_api_key")

        # Mock the login component's load_saved_settings method
        main_window.login_component.load_saved_settings = MagicMock()

        main_window.load_saved_settings()

        # Verify load_settings was called
        mock_load.assert_called_once()

        # Verify login component's load_saved_settings was called with correct parameters
        main_window.login_component.load_saved_settings.assert_called_once_with("192.168.1.1", "test_api_key")

def test_about_dialog(main_window):
    """Test that About dialog can be opened."""
    from src.ui.components.about_dialog import AboutDialog

    # Mock the AboutDialog
    with patch.object(AboutDialog, 'exec_') as mock_exec:
        # Call the show_about method
        main_window.show_about()

        # Verify that exec_ was called (dialog was shown)
        mock_exec.assert_called_once()

def test_menu_bar_has_about_menu(main_window):
    """Test that the Settings menu contains the About action."""
    menubar = main_window.menuBar()

    # Get all menu actions
    menus = [action.text() for action in menubar.actions()]

    # Verify Settings menu exists
    assert "Settings" in menus

    # Get the Settings menu
    settings_menu = None
    for action in menubar.actions():
        if action.text() == "Settings":
            settings_menu = action.menu()
            break

    assert settings_menu is not None

    # Get all actions in Settings menu
    settings_actions = [action.text() for action in settings_menu.actions() if not action.isSeparator()]

    # Verify both Debug Settings and About ArchImmich are in Settings menu
    assert "Debug Settings" in settings_actions
    assert "About ArchImmich" in settings_actions