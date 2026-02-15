import sys
import traceback
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def exception_hook(exctype, value, tb):
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)

def main():
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
