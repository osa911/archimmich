import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_qapplication():
    """Mock QApplication."""
    with patch("src.main.QApplication") as mock_app:
        yield mock_app


@pytest.fixture
def mock_main_window():
    """Mock MainWindow."""
    with patch("src.main.MainWindow") as mock_window:
        mock_window_instance = MagicMock()
        mock_window.return_value = mock_window_instance
        yield mock_window_instance


@patch("src.main.create_app")
@patch("sys.exit")  # Mock sys.exit to prevent stopping the test suite
def test_main_initialization(mock_sys_exit, mock_create_app, mock_qapplication, mock_main_window):
    """Test that the main application initializes correctly."""
    from src.main import run_app

    # Mock create_app to return our mocked app and window
    mock_create_app.return_value = (mock_qapplication, mock_main_window)

    run_app()

    # Assertions
    mock_create_app.assert_called_once()
    mock_main_window.show.assert_called_once()
    mock_qapplication.exec_.assert_called_once()
    mock_sys_exit.assert_called_once()