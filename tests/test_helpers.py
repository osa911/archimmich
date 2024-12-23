import os
import json
from src.utils.helpers import (
    get_resource_path,
    save_settings,
    load_settings,
)
from unittest.mock import patch

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
def test_save_settings(tmp_path):
    """
    Test that save_settings correctly writes server_ip and api_key to the config file.
    """
    config_file = tmp_path / "archimich_config.json"

    # Mock the CONFIG_FILE path
    with patch("src.utils.helpers.CONFIG_FILE", str(config_file)):
        save_settings("http://localhost", "test_api_key")

        assert config_file.exists()

        with open(config_file, "r") as file:
            data = json.load(file)
            assert data["server_ip"] == "http://localhost"
            assert data["api_key"] == "test_api_key"

# Test for load_settings
def test_load_settings(tmp_path):
    """
    Test that load_settings correctly loads server_ip and api_key from the config file.
    """
    config_file = tmp_path / "archimich_config.json"

    valid_config = {
        "server_ip": "http://localhost",
        "api_key": "test_api_key"
    }

    # ✅ Test loading existing valid config
    with open(config_file, "w") as file:
        json.dump(valid_config, file)

    server_ip, api_key = load_settings(str(config_file))
    assert server_ip == "http://localhost"
    assert api_key == "test_api_key"

    # ✅ Test loading non-existing config
    os.remove(config_file)
    server_ip, api_key = load_settings(str(config_file))
    assert server_ip == ""
    assert api_key == ""

    # Test with invalid JSON config
    with open(config_file, "w") as file:
        file.write("{invalid_json}")

    server_ip, api_key = load_settings(str(config_file))
    assert server_ip == ""
    assert api_key == ""

    # Test fallback to default CONFIG_FILE
    default_config_file = tmp_path / "default_config.json"
    with patch("src.utils.helpers.CONFIG_FILE", str(default_config_file)):
        with open(default_config_file, "w") as file:
            json.dump(valid_config, file)

        server_ip, api_key = load_settings()
        assert server_ip == "http://localhost"
        assert api_key == "test_api_key"

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