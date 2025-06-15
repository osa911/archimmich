import pytest
from src.ui.components.login_component import LoginComponent
from src.managers.login_manager import LoginManager
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock, patch

@pytest.fixture
def login_manager():
    """Fixture to create a mock login manager."""
    return MagicMock(spec=LoginManager)

@pytest.fixture
def login_component(qtbot, login_manager):
    """Fixture to initialize the LoginComponent."""
    component = LoginComponent(login_manager)
    qtbot.addWidget(component)
    return component

def test_login_component_initialization(login_component):
    """Test if the login component initializes correctly."""
    assert hasattr(login_component, 'server_ip_field')
    assert hasattr(login_component, 'api_key_field')
    assert hasattr(login_component, 'is_remember_me_checkbox')
    assert login_component.server_ip_field.placeholderText() == "Enter server IP (e.g., http://192.168.1.1:2283)"
    assert login_component.api_key_field.placeholderText() == "Enter API key"
    assert login_component.is_remember_me_checkbox.text() == "Remember me"

def test_clear_buttons_functionality(login_component):
    """Test that individual clear buttons work correctly."""
    # Show the component to ensure visibility updates work
    login_component.show()

    # Test server IP clear button
    login_component.server_ip_field.setText("http://test.com")
    login_component.update_clear_buttons_visibility()  # Manually trigger update
    assert login_component.server_ip_clear_button.isVisible()

    login_component.server_ip_clear_button.click()
    assert login_component.server_ip_field.text() == ""
    assert not login_component.server_ip_clear_button.isVisible()

    # Test API key clear button
    login_component.api_key_field.setText("test-key")
    login_component.update_clear_buttons_visibility()  # Manually trigger update
    assert login_component.api_key_clear_button.isVisible()

    login_component.api_key_clear_button.click()
    assert login_component.api_key_field.text() == ""
    assert not login_component.api_key_clear_button.isVisible()

def test_clear_buttons_visibility_on_text_change(login_component):
    """Test that clear buttons show/hide based on text content."""
    # Show the component to ensure visibility updates work
    login_component.show()

    # Initially both buttons should be hidden
    assert not login_component.server_ip_clear_button.isVisible()
    assert not login_component.api_key_clear_button.isVisible()

    # Add text to server IP field (textChanged signal should trigger update)
    login_component.server_ip_field.setText("http://test.com")
    assert login_component.server_ip_clear_button.isVisible()
    assert not login_component.api_key_clear_button.isVisible()

    # Add text to API key field
    login_component.api_key_field.setText("test-key")
    assert login_component.server_ip_clear_button.isVisible()
    assert login_component.api_key_clear_button.isVisible()

    # Clear server IP field
    login_component.server_ip_field.clear()
    assert not login_component.server_ip_clear_button.isVisible()
    assert login_component.api_key_clear_button.isVisible()

def test_login_validation(login_component):
    """Test validation of login inputs."""
    # Empty API key should fail validation
    login_component.api_key_field.setText("")
    login_component.server_ip_field.setText("http://localhost")
    assert not login_component.validate_inputs()

    # Empty server IP should fail validation
    login_component.api_key_field.setText("test_api_key")
    login_component.server_ip_field.setText("")
    assert not login_component.validate_inputs()

    # Valid inputs should pass validation
    login_component.api_key_field.setText("test_api_key")
    login_component.server_ip_field.setText("http://localhost")
    assert login_component.validate_inputs()

def test_login_button_click(login_component, qtbot):
    """Test if the login button triggers the login method."""
    login_button = login_component.findChild(QPushButton, "login_button")
    assert login_button is not None

    # Fill in valid credentials to pass validation
    login_component.server_ip_field.setText("http://localhost")
    login_component.api_key_field.setText("test-key")

    # Mock the login manager methods that would be called
    with patch.object(login_component.login_manager, 'set_credentials'), \
         patch.object(login_component.login_manager, 'login', return_value={"name": "Test"}), \
         patch.object(login_component.login_manager, 'getApiManager') as mock_get_api, \
         patch.object(login_component.login_manager, 'get_avatar_fetcher', return_value=None), \
         patch('src.utils.helpers.save_settings'):

        # Mock the API manager
        mock_api = MagicMock()
        mock_api.get_server_info.return_value = {"version": "1.0.0"}
        mock_get_api.return_value = mock_api

        qtbot.mouseClick(login_button, Qt.LeftButton)

        # Verify login manager methods were called
        login_component.login_manager.set_credentials.assert_called_once()
        login_component.login_manager.login.assert_called_once()

def test_theme_change_handling(login_component):
    """Test that theme changes are handled correctly."""
    # This tests the changeEvent method for palette changes
    from PyQt5.QtCore import QEvent

    # Test that the required methods exist
    assert hasattr(login_component, 'changeEvent')
    assert hasattr(login_component, 'update_theme_containers')

    # Test that the changeEvent method can be called without errors
    # We won't test specific event handling since that's implementation detail
    event = QEvent(QEvent.FontChange)

    # This should not raise an exception
    try:
        login_component.changeEvent(event)
        # If we get here, the test passes
        assert True
    except Exception as e:
        assert False, f"changeEvent raised an exception: {e}"

def test_reset_fields(login_component):
    """Test that reset_fields clears all inputs."""
    # Set up some data
    login_component.server_ip_field.setText("http://test.com")
    login_component.api_key_field.setText("test-key")
    login_component.is_remember_me_checkbox.setChecked(True)

    # Reset
    login_component.reset_fields()

    # Verify everything is cleared
    assert login_component.server_ip_field.text() == ""
    assert login_component.api_key_field.text() == ""
    assert not login_component.is_remember_me_checkbox.isChecked()

def test_error_display(login_component):
    """Test that error display works correctly."""
    # Show the component to ensure visibility works
    login_component.show()

    # Show an error
    error_message = "Test error message"
    login_component.error_label.setText(error_message)
    login_component.error_label.show()

    assert login_component.error_label.text() == error_message
    assert login_component.error_label.isVisible()

    # Clear errors
    login_component.clear_field_errors()
    assert not login_component.error_label.isVisible()

def test_load_saved_settings(login_component):
    """Test loading saved settings."""
    # Show the component to ensure visibility updates work
    login_component.show()

    server_ip = "http://test.com"
    api_key = "test-key"

    login_component.load_saved_settings(server_ip, api_key)

    assert login_component.server_ip_field.text() == server_ip
    assert login_component.api_key_field.text() == api_key
    assert login_component.is_remember_me_checkbox.isChecked()
    # Clear buttons should be visible after loading text
    assert login_component.server_ip_clear_button.isVisible()
    assert login_component.api_key_clear_button.isVisible()

def test_successful_login_signal(login_component, qtbot):
    """Test that successful login emits the correct signal."""
    # Mock successful login
    mock_user = {"name": "Test User", "email": "test@example.com"}
    mock_server_info = {"version": "1.134.0"}

    login_component.server_ip_field.setText("http://localhost")
    login_component.api_key_field.setText("test-key")

    with patch.object(login_component.login_manager, 'set_credentials'), \
         patch.object(login_component.login_manager, 'login', return_value=mock_user), \
         patch.object(login_component.login_manager, 'getApiManager') as mock_get_api, \
         patch.object(login_component.login_manager, 'get_avatar_fetcher', return_value=None), \
         patch('src.utils.helpers.save_settings'):

        mock_api = MagicMock()
        mock_api.get_server_info.return_value = mock_server_info
        mock_get_api.return_value = mock_api

        with qtbot.waitSignal(login_component.login_successful, timeout=1000) as blocker:
            login_component.login()

        # Check signal data
        signal_data = blocker.args[0]
        assert signal_data['user'] == mock_user
        assert signal_data['server_version'] == "1.134.0"

def test_failed_login_signal(login_component, qtbot):
    """Test that failed login emits the correct signal."""
    login_component.server_ip_field.setText("http://localhost")
    login_component.api_key_field.setText("invalid-key")

    with patch.object(login_component.login_manager, 'set_credentials'), \
         patch.object(login_component.login_manager, 'login', side_effect=Exception("Invalid credentials")):

        with qtbot.waitSignal(login_component.login_failed, timeout=1000) as blocker:
            login_component.login()

        # Check signal data
        error_message = blocker.args[0]
        assert "Invalid credentials" in error_message