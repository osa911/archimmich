import os
import sys
import pytest

# Add the project root directory to Python's path
# This allows imports from 'src' to work correctly in tests
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for all tests."""
    # Set environment variable to indicate we're in test mode
    monkeypatch.setenv("ARCHIMMICH_TEST_MODE", "1")

    # Patch the Logger class to use test_mode=True by default
    # This is done by monkeypatching the __init__ method
    from src.utils.helpers import Logger
    original_init = Logger.__init__

    def patched_init(self, logs_widget=None, test_mode=False):
        # Always use test_mode=True in tests
        original_init(self, logs_widget, test_mode=True)

    monkeypatch.setattr(Logger, "__init__", patched_init)

    yield

    # Clean up any test log files if they were created
    test_log = os.path.join(os.path.dirname(__file__), "test_log.log")
    if os.path.exists(test_log):
        try:
            os.remove(test_log)
        except:
            pass