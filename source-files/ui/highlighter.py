from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class LogHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        # Error / Failed / Exception -> Red & Bold
        err_fmt = QTextCharFormat()
        err_fmt.setForeground(QColor("red"))
        err_fmt.setFontWeight(QFont.Bold)
        self.rules.append((QRegularExpression(r"(?i)\b(error|failed|failure|exception|critical|fatal)\b"), err_fmt))

        # Warning -> Orange / Dark Yellow
        warn_fmt = QTextCharFormat()
        warn_fmt.setForeground(QColor("#FF8C00")) # DarkOrange
        warn_fmt.setFontWeight(QFont.Bold)
        self.rules.append((QRegularExpression(r"(?i)\b(warn|warning)\b"), warn_fmt))

        # Info -> Green
        info_fmt = QTextCharFormat()
        info_fmt.setForeground(QColor("#008000")) # Green
        self.rules.append((QRegularExpression(r"(?i)\b(info|success)\b"), info_fmt))

        # Debug -> Gray
        debug_fmt = QTextCharFormat()
        debug_fmt.setForeground(QColor("gray"))
        self.rules.append((QRegularExpression(r"(?i)\b(debug)\b"), debug_fmt))

        # IP Address -> Cyan / Blue
        ip_fmt = QTextCharFormat()
        ip_fmt.setForeground(QColor("#00FFFF"))
        self.rules.append((QRegularExpression(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), ip_fmt))

        # Date/Time (Start of line usually) -> Dark Magenta
        date_fmt = QTextCharFormat()
        date_fmt.setForeground(QColor("darkmagenta"))
        self.rules.append((QRegularExpression(r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}"), date_fmt))
        self.rules.append((QRegularExpression(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"), date_fmt))

    def highlightBlock(self, text: str):
        for pattern, fmt in self.rules:
            match_iter = pattern.globalMatch(text)
            while match_iter.hasNext():
                match = match_iter.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
