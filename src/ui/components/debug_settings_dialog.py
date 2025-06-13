import json
from PyQt5.QtWidgets import QDialog, QFormLayout, QCheckBox, QPushButton
from PyQt5.QtCore import Qt
from src.utils.helpers import get_path_in_app
from src.constants import CONFIG_FILE

class DebugSettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self.setWindowTitle("Debug Settings")
        self.setModal(True)

        layout = QFormLayout(self)

        # Create checkboxes for each debug setting
        self.verbose_logging = QCheckBox("Enable Verbose Logging")
        self.verbose_logging.setChecked(self.config.get('debug', {}).get('verbose_logging', False))

        self.log_api_requests = QCheckBox("Log API Requests")
        self.log_api_requests.setChecked(self.config.get('debug', {}).get('log_api_requests', False))

        self.log_api_responses = QCheckBox("Log API Responses")
        self.log_api_responses.setChecked(self.config.get('debug', {}).get('log_api_responses', False))

        self.log_request_bodies = QCheckBox("Log Request Bodies")
        self.log_request_bodies.setChecked(self.config.get('debug', {}).get('log_request_bodies', False))

        # Add checkboxes to layout
        layout.addRow("", self.verbose_logging)
        layout.addRow("", self.log_api_requests)
        layout.addRow("", self.log_api_responses)
        layout.addRow("", self.log_request_bodies)

        # Add save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        layout.addRow("", save_button)

    def save_settings(self):
        # Update config with new settings
        if 'debug' not in self.config:
            self.config['debug'] = {}

        self.config['debug'].update({
            'verbose_logging': self.verbose_logging.isChecked(),
            'log_api_requests': self.log_api_requests.isChecked(),
            'log_api_responses': self.log_api_responses.isChecked(),
            'log_request_bodies': self.log_request_bodies.isChecked()
        })

        # Save to file
        try:
            with open(get_path_in_app(CONFIG_FILE), 'w') as f:
                json.dump(self.config, f, indent=2)
            if hasattr(self.parent(), 'log'):
                self.parent().log("Debug settings saved successfully")
        except Exception as e:
            if hasattr(self.parent(), 'log'):
                self.parent().log(f"Error saving debug settings: {str(e)}")
            else:
                print(f"Error saving debug settings: {str(e)}")

        self.accept()