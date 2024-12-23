import pytest
from PyQt5.QtWidgets import QApplication
import sys

# Create a QApplication instance for PyQt5 tests
@pytest.fixture(scope="session")
def app():
    app = QApplication(sys.argv)
    yield app
    app.quit()