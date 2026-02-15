from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
import sys

def show_error(parent, title: str, message: str):
    """
    Displays an error message box where text can be selected and copied.
    Also prints to stderr.
    """
    print(f"[ERROR] {title}: {message}", file=sys.stderr)
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    # Enable text selection
    msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
    msg_box.exec()

def show_info(parent, title: str, message: str):
    """
    Displays an info message box where text can be selected.
    Also prints to stdout.
    """
    print(f"[INFO] {title}: {message}")
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
    msg_box.exec()
