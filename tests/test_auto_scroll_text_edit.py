import pytest
from src.ui.components.auto_scroll_text_edit import AutoScrollTextEdit
from PyQt5.QtGui import QTextCursor
from unittest.mock import patch


@pytest.fixture
def auto_scroll_text_edit(qtbot):
    """Fixture to initialize AutoScrollTextEdit."""
    widget = AutoScrollTextEdit()
    qtbot.addWidget(widget)
    return widget


def test_initialization(auto_scroll_text_edit):
    """Test that AutoScrollTextEdit initializes correctly."""
    assert auto_scroll_text_edit.isReadOnly()
    assert auto_scroll_text_edit.placeholderText() == "Logs will appear here..."
    assert auto_scroll_text_edit.toPlainText() == ""


def test_append_text(auto_scroll_text_edit):
    """Test that text is appended correctly."""
    test_text = "Test log message"
    auto_scroll_text_edit.append(test_text)

    assert test_text in auto_scroll_text_edit.toPlainText()


def test_multiple_append(auto_scroll_text_edit):
    """Test appending multiple messages."""
    messages = ["First message", "Second message", "Third message"]

    for message in messages:
        auto_scroll_text_edit.append(message)

    content = auto_scroll_text_edit.toPlainText()
    for message in messages:
        assert message in content


def test_auto_scroll_behavior(auto_scroll_text_edit):
    """Test that the widget automatically scrolls to bottom."""
    # Show the widget to enable proper cursor operations
    auto_scroll_text_edit.show()

    with patch.object(auto_scroll_text_edit, 'moveCursor') as mock_move, \
         patch.object(auto_scroll_text_edit, 'ensureCursorVisible') as mock_ensure:

        auto_scroll_text_edit.append("Test message")

        mock_move.assert_called_once_with(QTextCursor.End)
        mock_ensure.assert_called_once()


def test_read_only_behavior(auto_scroll_text_edit):
    """Test that the widget is read-only."""
    # Try to set text directly (should not work in read-only mode)
    initial_text = auto_scroll_text_edit.toPlainText()

    # The widget should remain read-only
    assert auto_scroll_text_edit.isReadOnly()

    # Only append should work
    auto_scroll_text_edit.append("New message")
    assert "New message" in auto_scroll_text_edit.toPlainText()


def test_empty_append(auto_scroll_text_edit):
    """Test appending empty string."""
    initial_content = auto_scroll_text_edit.toPlainText()
    auto_scroll_text_edit.append("")

    # Should still work but may add newline
    # The important thing is it doesn't crash
    assert len(auto_scroll_text_edit.toPlainText()) >= len(initial_content)


def test_newline_handling(auto_scroll_text_edit):
    """Test that newlines are handled correctly."""
    multiline_text = "Line 1\nLine 2\nLine 3"
    auto_scroll_text_edit.append(multiline_text)

    content = auto_scroll_text_edit.toPlainText()
    assert "Line 1" in content
    assert "Line 2" in content
    assert "Line 3" in content


def test_large_text_append(auto_scroll_text_edit):
    """Test appending large amounts of text."""
    # Generate a large text string
    large_text = "Large text content " * 100

    auto_scroll_text_edit.append(large_text)

    assert large_text in auto_scroll_text_edit.toPlainText()


def test_unicode_text_append(auto_scroll_text_edit):
    """Test appending Unicode characters."""
    unicode_text = "Testing Unicode: 📁 🔄 ✅ ❌ 🌟"

    auto_scroll_text_edit.append(unicode_text)

    assert unicode_text in auto_scroll_text_edit.toPlainText()


def test_clear_and_append(auto_scroll_text_edit):
    """Test clearing content and appending new text."""
    # Add initial content
    auto_scroll_text_edit.append("Initial content")
    assert "Initial content" in auto_scroll_text_edit.toPlainText()

    # Clear content
    auto_scroll_text_edit.clear()
    assert auto_scroll_text_edit.toPlainText().strip() == ""

    # Add new content
    auto_scroll_text_edit.append("New content")
    assert "New content" in auto_scroll_text_edit.toPlainText()
    assert "Initial content" not in auto_scroll_text_edit.toPlainText()


def test_auto_scroll_control(auto_scroll_text_edit):
    """Test enabling and disabling auto-scroll functionality."""
    # Show the widget to enable proper cursor operations
    auto_scroll_text_edit.show()

    # Test initial state (should be enabled by default)
    assert auto_scroll_text_edit.auto_scroll_enabled == True

    # Test disabling auto-scroll
    with patch.object(auto_scroll_text_edit, 'moveCursor') as mock_move, \
         patch.object(auto_scroll_text_edit, 'ensureCursorVisible') as mock_ensure:

        auto_scroll_text_edit.set_auto_scroll(False)
        assert auto_scroll_text_edit.auto_scroll_enabled == False

        # Append text - should not trigger scroll
        auto_scroll_text_edit.append("Test message")
        mock_move.assert_not_called()
        mock_ensure.assert_not_called()

    # Test re-enabling auto-scroll
    with patch.object(auto_scroll_text_edit, 'moveCursor') as mock_move, \
         patch.object(auto_scroll_text_edit, 'ensureCursorVisible') as mock_ensure:

        auto_scroll_text_edit.set_auto_scroll(True)
        assert auto_scroll_text_edit.auto_scroll_enabled == True

        # Append text - should trigger scroll
        auto_scroll_text_edit.append("Test message")
        mock_move.assert_called_once_with(QTextCursor.End)
        mock_ensure.assert_called_once()