import sys
import os
import json

# Add the project root to sys.path
project_root = os.path.abspath(os.path.dirname(__file__) + "/..")
sys.path.append(project_root)

from src.ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from src.utils.helpers import get_path_in_app, migrate_config_if_needed
from src.constants import CONFIG_FILE


def load_config():
    """Load configuration from config.json."""
    # Migrate config from old location if needed
    migrate_config_if_needed()

    try:
        with open(get_path_in_app(CONFIG_FILE), 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def create_app():
    """Create and return the QApplication and MainWindow instances."""
    app = QApplication(sys.argv)
    config = load_config()
    window = MainWindow(config)
    return app, window


def run_app():
    """Start the application."""
    app, window = create_app()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()