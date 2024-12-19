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

    def append(self, text):
        """
        Append text to the text edit and scroll to the bottom.

        Args:
            text (str): The text to append.
        """
        super().append(text)
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()