import os
import json
import pytest
from unittest.mock import patch, Mock, mock_open
from src.utils.helpers import (
    get_resource_path,
    save_settings,
    load_settings,
    Logger
)

# Test for get_resource_path
def test_get_resource_path():
    """
    Test get_resource_path with PyInstaller (_MEIPASS) and regular execution.
    """
    # Simulate PyInstaller environment
    with patch.dict('sys.__dict__', {"_MEIPASS": "/fake_path"}):
        assert get_resource_path("test_file.txt") == "/fake_path/test_file.txt"

    # Simulate normal execution environment
    with patch("os.path.abspath", return_value="/current_dir"):
        assert get_resource_path("test_file.txt") == "/current_dir/test_file.txt"

# Test for save_settings
def test_save_settings(monkeypatch):
    """Test saving settings to a file."""
    monkeypatch.setattr('src.utils.helpers.CONFIG_FILE', '/app/config.json')

    with patch('builtins.open', mock_open()) as mock_file, \
         patch('os.makedirs'):
        save_settings("http://test.com", "test-api-key")
        mock_file.assert_called_once_with("/app/config.json", "w")
        handle = mock_file()
        assert handle.write.called

# Test for load_settings
def test_load_settings(monkeypatch):
    """Test loading settings from a file."""
    monkeypatch.setattr('src.utils.helpers.CONFIG_FILE', '/app/config.json')
    mock_data = '{"server_ip": "http://test.com", "api_key": "test-api-key"}'

    # Test when file exists
    with patch('builtins.open', mock_open(read_data=mock_data)), \
         patch('os.path.exists', return_value=True):
        result = load_settings()
        assert result == ("http://test.com", "test-api-key")

    # Test when file doesn't exist
    with patch('os.path.exists', return_value=False):
        result = load_settings()
        assert result == ("", "")

# Test for render_default_avatar
@patch("src.utils.helpers.QPainter")
@patch("src.utils.helpers.QPixmap")
def test_render_default_avatar(mock_pixmap, mock_painter):
    from src.utils.helpers import render_default_avatar

    class MockAppWindow:
        def __init__(self):
            self.avatar_label = mock_pixmap()
            self.logs = []

    app_window = MockAppWindow()

    # Mock width and height
    app_window.avatar_label.width.return_value = 100
    app_window.avatar_label.height.return_value = 100

    render_default_avatar(app_window)

    mock_painter.return_value.setRenderHint.assert_called()
    app_window.avatar_label.setPixmap.assert_called()
    assert "Default avatar displayed." in app_window.logs

@pytest.fixture
def mock_logs_widget():
    return Mock()

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for log files."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir()
    return log_dir

def test_logger_initialization(temp_log_dir, mock_logs_widget):
    """Test Logger initialization and log directory creation."""
    log_dir_str = str(temp_log_dir)
    with patch('src.utils.helpers.os.path.dirname', return_value="/app"), \
         patch('src.utils.helpers.os.path.abspath', return_value="/app/src/utils/helpers.py"), \
         patch('src.utils.helpers.os.path.join', return_value=log_dir_str), \
         patch('src.utils.helpers.os.makedirs') as mock_makedirs, \
         patch('logging.FileHandler') as mock_file_handler, \
         patch('logging.NullHandler') as mock_null_handler:

        logger = Logger(mock_logs_widget, test_mode=True)
        mock_makedirs.assert_not_called()
        assert logger.logs_widget == mock_logs_widget
        assert logger.test_mode == True

def test_logger_append(temp_log_dir, mock_logs_widget):
    """Test that logger.append writes to both file and widget."""
    with patch('src.utils.helpers.os.path.dirname', return_value="/app"), \
         patch('src.utils.helpers.os.path.abspath', return_value="/app/src/utils/helpers.py"), \
         patch('src.utils.helpers.os.path.join', return_value=str(temp_log_dir)), \
         patch('src.utils.helpers.os.makedirs'), \
         patch('logging.FileHandler'), \
         patch('logging.Logger.log') as mock_log:

        logger = Logger(mock_logs_widget, test_mode=True)
        test_message = "Test log message"
        logger.append(test_message)

        # Check widget received message
        mock_logs_widget.append.assert_called_once_with(test_message)

        mock_log.assert_not_called()

def test_logger_without_widget(temp_log_dir):
    """Test that logger works without a widget."""
    with patch('src.utils.helpers.os.path.dirname', return_value="/app"), \
         patch('src.utils.helpers.os.path.abspath', return_value="/app/src/utils/helpers.py"), \
         patch('src.utils.helpers.os.path.join', return_value=str(temp_log_dir)), \
         patch('src.utils.helpers.os.makedirs'), \
         patch('logging.FileHandler'), \
         patch('logging.Logger.log') as mock_log:

        logger = Logger(None, test_mode=True)
        test_message = "Test log message"
        logger.append(test_message)

        mock_log.assert_not_called()