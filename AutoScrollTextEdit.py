from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCursor

class AutoScrollTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)  # Make it read-only by default for logs

    def append(self, text):
        """
        Override the append method to auto-scroll to the bottom after adding text.
        """
        super().append(text)  # Call the original append method
        self.moveCursor(QTextCursor.End)  # Move the cursor to the end
        self.ensureCursorVisible()  # Ensure the cursor is visible