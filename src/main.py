import sys
import os

# Add the project root to sys.path
project_root = os.path.abspath(os.path.dirname(__file__) + "/..")
sys.path.append(project_root)

from ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())