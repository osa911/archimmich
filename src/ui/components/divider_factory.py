from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout

class DividerFactory:
    """Factory class for creating consistent dividers across the application."""

    @staticmethod
    def create_horizontal_divider(color="#ddd", parent=None):
        """Create a horizontal divider with consistent styling."""
        divider = QFrame(parent)
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet(f"color: {color};")
        return divider

    @staticmethod
    def create_vertical_divider(color="#ddd", parent=None):
        """Create a vertical divider with consistent styling."""
        divider = QFrame(parent)
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet(f"color: {color};")
        return divider


# Convenience functions with margin support
def HorizontalDivider(color="#ddd", parent=None, margins=None):
    """
    Create horizontal divider.

    Args:
        color: Divider color
        parent: Parent widget
        margins: Dict with 'top', 'bottom', 'left', 'right' keys or tuple (top, right, bottom, left)
    """
    divider = DividerFactory.create_horizontal_divider(color, parent)

    if margins:
        if isinstance(margins, dict):
            top = margins.get('top', 0)
            right = margins.get('right', 0)
            bottom = margins.get('bottom', 0)
            left = margins.get('left', 0)
            divider.setContentsMargins(left, top, right, bottom)
        elif isinstance(margins, (tuple, list)) and len(margins) == 4:
            divider.setContentsMargins(*margins)

    return divider


def VerticalDivider(color="#ddd", parent=None, margins=None, with_container=False):
    """
    Create vertical divider.

    Args:
        color: Divider color
        parent: Parent widget
        margins: Dict with 'top', 'bottom', 'left', 'right' keys or tuple (top, right, bottom, left)
        with_container: If True, wraps divider in a container widget for better margin control
    """
    if with_container and margins:
        # Create container for better margin control
        container = QWidget(parent)
        layout = QHBoxLayout(container)

        if isinstance(margins, dict):
            top = margins.get('top', 0)
            right = margins.get('right', 0)
            bottom = margins.get('bottom', 0)
            left = margins.get('left', 0)
            layout.setContentsMargins(left, top, right, bottom)
        elif isinstance(margins, (tuple, list)) and len(margins) == 4:
            layout.setContentsMargins(*margins)

        divider = DividerFactory.create_vertical_divider(color)
        layout.addWidget(divider)
        return container
    else:
        # Simple divider
        divider = DividerFactory.create_vertical_divider(color, parent)

        if margins:
            if isinstance(margins, dict):
                top = margins.get('top', 0)
                right = margins.get('right', 0)
                bottom = margins.get('bottom', 0)
                left = margins.get('left', 0)
                divider.setContentsMargins(left, top, right, bottom)
            elif isinstance(margins, (tuple, list)) and len(margins) == 4:
                divider.setContentsMargins(*margins)

        return divider