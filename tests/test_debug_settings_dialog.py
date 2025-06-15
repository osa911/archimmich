import pytest
from src.ui.components.debug_settings_dialog import DebugSettingsDialog
from PyQt5.QtWidgets import QCheckBox, QPushButton
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock, patch

@pytest.fixture
def config():
    """Fixture to create a test config."""
    return {
        'debug': {
            'log_api_requests': False,
            'log_api_responses': False,
            'verbose_logging': False,
            'log_request_bodies': False
        }
    }

@pytest.fixture
def parent_window(qtbot):
    """Fixture to create a real parent window."""
    from PyQt5.QtWidgets import QWidget
    parent = QWidget()
    parent.config = {}
    qtbot.addWidget(parent)
    return parent

@pytest.fixture
def debug_dialog(qtbot, config, parent_window):
    """Fixture to initialize the DebugSettingsDialog."""
    dialog = DebugSettingsDialog(config, parent_window)
    qtbot.addWidget(dialog)
    return dialog

def test_debug_dialog_initialization(debug_dialog):
    """Test if the debug settings dialog initializes correctly."""
    assert debug_dialog.windowTitle() == "Debug Settings"
    assert hasattr(debug_dialog, 'log_api_requests')
    assert hasattr(debug_dialog, 'log_api_responses')
    assert hasattr(debug_dialog, 'verbose_logging')
    assert hasattr(debug_dialog, 'log_request_bodies')

def test_load_existing_settings(debug_dialog):
    """Test loading existing debug settings."""
    # Settings should be loaded from config
    assert not debug_dialog.log_api_requests.isChecked()
    assert not debug_dialog.log_api_responses.isChecked()
    assert not debug_dialog.verbose_logging.isChecked()
    assert not debug_dialog.log_request_bodies.isChecked()

def test_load_existing_settings_with_values(qtbot):
    """Test loading existing debug settings with values."""
    from PyQt5.QtWidgets import QWidget
    config_with_values = {
        'debug': {
            'log_api_requests': True,
            'log_api_responses': True,
            'verbose_logging': True,
            'log_request_bodies': False
        }
    }
    parent = QWidget()
    parent.config = {}
    qtbot.addWidget(parent)

    dialog = DebugSettingsDialog(config_with_values, parent)
    qtbot.addWidget(dialog)

    assert dialog.log_api_requests.isChecked()
    assert dialog.log_api_responses.isChecked()
    assert dialog.verbose_logging.isChecked()
    assert not dialog.log_request_bodies.isChecked()

def test_save_settings(debug_dialog):
    """Test saving debug settings."""
    # Change some settings
    debug_dialog.log_api_requests.setChecked(True)
    debug_dialog.log_api_responses.setChecked(True)
    debug_dialog.verbose_logging.setChecked(False)

    with patch('builtins.open'), patch('json.dump') as mock_dump:
        debug_dialog.save_settings()

        # Check that config was updated correctly
        assert debug_dialog.config['debug']['log_api_requests'] == True
        assert debug_dialog.config['debug']['log_api_responses'] == True
        assert debug_dialog.config['debug']['verbose_logging'] == False

def test_save_button_saves_and_closes(debug_dialog, qtbot):
    """Test that Save button saves settings and closes dialog."""
    # Change some settings
    debug_dialog.log_api_requests.setChecked(True)

    save_button = debug_dialog.findChild(QPushButton)
    assert save_button is not None
    assert save_button.text() == "Save"

    with patch('builtins.open'), \
         patch('json.dump'), \
         patch.object(debug_dialog, 'accept') as mock_accept:

        qtbot.mouseClick(save_button, Qt.LeftButton)
        mock_accept.assert_called_once()

def test_parent_config_update(debug_dialog):
    """Test that parent config is updated when settings are saved."""
    # Change some settings
    debug_dialog.log_api_requests.setChecked(True)
    debug_dialog.log_api_responses.setChecked(False)

    with patch('builtins.open'), patch('json.dump'):
        debug_dialog.save_settings()

        # Check that config was updated
        assert debug_dialog.config['debug']['log_api_requests'] == True
        assert debug_dialog.config['debug']['log_api_responses'] == False

def test_dialog_modal_behavior(debug_dialog):
    """Test that dialog is modal."""
    assert debug_dialog.isModal()

def test_checkbox_state_changes(debug_dialog, qtbot):
    """Test that checkbox states can be changed."""
    # Show the dialog to ensure proper interaction
    debug_dialog.show()

    # Initially unchecked
    assert not debug_dialog.log_api_requests.isChecked()
    assert not debug_dialog.log_api_responses.isChecked()

    # Check the checkboxes programmatically (more reliable than mouse clicks for checkboxes)
    debug_dialog.log_api_requests.setChecked(True)
    debug_dialog.log_api_responses.setChecked(True)

    # Should now be checked
    assert debug_dialog.log_api_requests.isChecked()
    assert debug_dialog.log_api_responses.isChecked()

    # Test unchecking
    debug_dialog.log_api_requests.setChecked(False)
    debug_dialog.log_api_responses.setChecked(False)

    # Should now be unchecked
    assert not debug_dialog.log_api_requests.isChecked()
    assert not debug_dialog.log_api_responses.isChecked()

def test_config_file_operations(debug_dialog):
    """Test that config file operations work correctly."""
    # Test with file operations mocked
    debug_dialog.verbose_logging.setChecked(True)
    debug_dialog.log_request_bodies.setChecked(True)

    with patch('builtins.open'), \
         patch('json.dump') as mock_dump, \
         patch.object(debug_dialog, 'accept'):

        debug_dialog.save_settings()

        # Verify json.dump was called
        mock_dump.assert_called_once()
        # Verify the config structure
        config_arg = mock_dump.call_args[0][0]
        assert 'debug' in config_arg
        assert config_arg['debug']['verbose_logging'] == True
        assert config_arg['debug']['log_request_bodies'] == True