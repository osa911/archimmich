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

    # Mock empty existing config (file doesn't exist or is empty)
    with patch('builtins.open', mock_open(read_data='')) as mock_file, \
         patch('os.makedirs'), \
         patch('os.path.exists', return_value=True):
        save_settings("http://test.com", "test-api-key")

        # Should be called twice: once for reading, once for writing
        assert mock_file.call_count == 2
        mock_file.assert_any_call("/app/config.json", "r")
        mock_file.assert_any_call("/app/config.json", "w")

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
    """Test that logger.append writes to both file and widget with line numbers."""
    with patch('src.utils.helpers.os.path.dirname', return_value="/app"), \
         patch('src.utils.helpers.os.path.abspath', return_value="/app/src/utils/helpers.py"), \
         patch('src.utils.helpers.os.path.join', return_value=str(temp_log_dir)), \
         patch('src.utils.helpers.os.makedirs'), \
         patch('logging.FileHandler'), \
         patch('logging.Logger.log') as mock_log:

        logger = Logger(mock_logs_widget, test_mode=True)
        test_message = "Test log message"
        logger.append(test_message)

        # Check widget received message with line number
        mock_logs_widget.append.assert_called_once_with("[0001] Test log message")

        mock_log.assert_not_called()

def test_logger_line_numbering(temp_log_dir, mock_logs_widget):
    """Test that logger line numbers increment correctly."""
    with patch('src.utils.helpers.os.path.dirname', return_value="/app"), \
         patch('src.utils.helpers.os.path.abspath', return_value="/app/src/utils/helpers.py"), \
         patch('src.utils.helpers.os.path.join', return_value=str(temp_log_dir)), \
         patch('src.utils.helpers.os.makedirs'), \
         patch('logging.FileHandler'), \
         patch('logging.Logger.log'):

        logger = Logger(mock_logs_widget, test_mode=True)

        # Add multiple messages
        logger.append("First message")
        logger.append("Second message")
        logger.append("Third message")

        # Check that line numbers increment correctly
        expected_calls = [
            (("[0001] First message",),),
            (("[0002] Second message",),),
            (("[0003] Third message",),)
        ]
        assert mock_logs_widget.append.call_args_list == expected_calls

def test_logger_reset_line_numbers(temp_log_dir, mock_logs_widget):
    """Test that logger line numbers can be reset."""
    with patch('src.utils.helpers.os.path.dirname', return_value="/app"), \
         patch('src.utils.helpers.os.path.abspath', return_value="/app/src/utils/helpers.py"), \
         patch('src.utils.helpers.os.path.join', return_value=str(temp_log_dir)), \
         patch('src.utils.helpers.os.makedirs'), \
         patch('logging.FileHandler'), \
         patch('logging.Logger.log'):

        logger = Logger(mock_logs_widget, test_mode=True)

        # Add some messages
        logger.append("First message")
        logger.append("Second message")

        # Reset line numbers
        logger.reset_line_numbers()

        # Add more messages after reset
        logger.append("After reset message")

        # Check that line numbers reset correctly
        expected_calls = [
            (("[0001] First message",),),
            (("[0002] Second message",),),
            (("[0001] After reset message",),)
        ]
        assert mock_logs_widget.append.call_args_list == expected_calls

def test_logger_dynamic_width_formatting(temp_log_dir, mock_logs_widget):
    """Test that logger line number width adjusts dynamically."""
    with patch('src.utils.helpers.os.path.dirname', return_value="/app"), \
         patch('src.utils.helpers.os.path.abspath', return_value="/app/src/utils/helpers.py"), \
         patch('src.utils.helpers.os.path.join', return_value=str(temp_log_dir)), \
         patch('src.utils.helpers.os.makedirs'), \
         patch('logging.FileHandler'), \
         patch('logging.Logger.log'):

        logger = Logger(mock_logs_widget, test_mode=True)

        # Test 4-digit formatting (standard)
        logger.append("Message 1")

        # Test 5-digit formatting by setting line number high
        logger.line_number = 9999
        logger.append("Message at 10000")

        # Test 6-digit formatting
        logger.line_number = 99999
        logger.append("Message at 100000")

        # Check that width adjusts correctly
        expected_calls = [
            (("[0001] Message 1",),),
            (("[10000] Message at 10000",),),
            (("[100000] Message at 100000",),)
        ]
        assert mock_logs_widget.append.call_args_list == expected_calls

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