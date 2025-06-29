from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCursor


class AutoScrollTextEdit(QTextEdit):
    """
    A QTextEdit widget that automatically scrolls to the bottom when new text is added.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Logs will appear here...")
        self.auto_scroll_enabled = True  # Default to auto-scroll enabled

    def append(self, text):
        """
        Append text to the text edit and scroll to the bottom if auto-scroll is enabled.

        Args:
            text (str): The text to append.
        """
        super().append(text)
        if self.auto_scroll_enabled:
            self.moveCursor(QTextCursor.End)
            self.ensureCursorVisible()

    def set_auto_scroll(self, enabled: bool):
        """Enable or disable auto-scrolling."""
        self.auto_scroll_enabled = enabled