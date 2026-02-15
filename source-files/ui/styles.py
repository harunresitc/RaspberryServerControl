
DARK_THEME_QSS = """
/* Global Styles */
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}

/* Tooltips */
QToolTip {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
}

/* Push Button */
QPushButton {
    background-color: #3c3f41;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 15px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #484b4d;
    border: 1px solid #666666;
}

QPushButton:pressed {
    background-color: #2b2b2b;
    border: 1px solid #007acc;
}

QPushButton:disabled {
    background-color: #333333;
    color: #777777;
    border: 1px solid #444444;
}

/* Line Edit & Combo Box & Spin Box */
QLineEdit, QComboBox, QSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #444444;
    border-radius: 3px;
    padding: 3px;
    color: #e0e0e0;
    selection-background-color: #264f78;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #007acc;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}

QComboBox::down-arrow {
    image: url("data:image/svg+xml;charset=utf-8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'><path d='M0,0 L10,0 L5,10 Z' fill='white'/></svg>");
    width: 10px;
    height: 10px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #444444;
    background-color: #2b2b2b;
    top: -1px; 
}

QTabBar::tab {
    background-color: #3c3f41;
    border: 1px solid #444444;
    border-bottom-color: #444444;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 12px;
    margin-right: 2px;
    color: #cccccc;
}

QTabBar::tab:selected {
    background-color: #2b2b2b;
    border-color: #444444;
    border-bottom-color: #2b2b2b; /* Same as pane color to blend */
    color: #ffffff;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #484b4d;
}

/* Text Edit */
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #dcdcdc;
    border: 1px solid #444444;
    selection-background-color: #264f78;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10pt;
}

/* Table Widget */
QTableWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    gridline-color: #333333;
    border: 1px solid #444444;
}

QHeaderView::section {
    background-color: #3c3f41;
    color: #e0e0e0;
    padding: 4px;
    border: 1px solid #444444;
}

QTableWidget::item:selected {
    background-color: #264f78;
    color: #ffffff;
}

/* Group Box */
QGroupBox {
    border: 1px solid #444444;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
    color: #007acc; 
}

/* Status Bar */
QStatusBar {
    background-color: #3c3f41;
    color: #e0e0e0;
    border-top: 1px solid #444444;
}

QStatusBar QLabel {
    color: #ffffff;
}

/* ScrollBar (Simple dark style) */
QScrollBar:vertical {
    border: none;
    background: #2b2b2b;
    width: 12px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #888888;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #aaaaaa;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #2b2b2b;
    height: 12px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #888888;
    min-width: 20px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
    background: #aaaaaa;
}
"""
