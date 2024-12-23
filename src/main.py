import sys
import os

# Add the project root to sys.path
project_root = os.path.abspath(os.path.dirname(__file__) + "/..")
sys.path.append(project_root)

from ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication


def create_app():
    """Create and return the QApplication and MainWindow instances."""
    app = QApplication(sys.argv)
    window = MainWindow()
    return app, window


def run_app():
    """Start the application."""
    app, window = create_app()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()