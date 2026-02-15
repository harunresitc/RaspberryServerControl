import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit, QMessageBox, QHeaderView, QFileDialog, QStyle
)
from backend.local import VAR_LOG_DIR
from .highlighter import LogHighlighter
from .utils import show_error, show_info
from backend.lang_manager import trans

class VarLogTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        layout = QVBoxLayout(self)

        bar = QHBoxLayout()
        self.varlog_refresh_btn = QPushButton(trans("refresh"))
        self.varlog_refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        
        self.varlog_view_btn = QPushButton(trans("varlog_view"))
        self.varlog_view_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        
        self.varlog_download_btn = QPushButton(trans("varlog_download"))
        self.varlog_download_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        
        self.varlog_search_edit = QLineEdit()
        self.varlog_search_edit.setPlaceholderText(trans("filter_placeholder"))
        self.varlog_search_btn = QPushButton(trans("filter_btn"))
        self.varlog_search_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        self.varlog_lines_spin = QSpinBox()
        self.varlog_lines_spin.setRange(10, 20000)
        self.varlog_lines_spin.setValue(200)

        bar.addWidget(self.varlog_refresh_btn)
        bar.addWidget(QLabel(trans("lines")))
        bar.addWidget(self.varlog_lines_spin)
        bar.addWidget(self.varlog_view_btn)
        bar.addWidget(self.varlog_download_btn)
        
        self.varlog_clear_btn = QPushButton(trans("varlog_clear"))
        self.varlog_clear_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.varlog_clear_btn.setStyleSheet("color: red;")
        self.varlog_clear_btn.clicked.connect(self.clear_selected_file)
        bar.addWidget(self.varlog_clear_btn)
        
        bar.addStretch(1)
        bar.addWidget(self.varlog_search_edit, 1)
        bar.addWidget(self.varlog_search_btn)
        layout.addLayout(bar)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([trans("col_file"), trans("col_size"), trans("col_date")])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.varlog_text = QTextEdit()
        self.varlog_text.setReadOnly(True)
        self.varlog_text.setFont(QFont("Consolas", 10))
        # Highlight
        self.highlighter = LogHighlighter(self.varlog_text.document())
        layout.addWidget(self.varlog_text, 1)

        self.varlog_refresh_btn.clicked.connect(self.refresh_varlog)
        self.varlog_view_btn.clicked.connect(self.view_selected_varlog_file)
        self.varlog_download_btn.clicked.connect(self.download_selected_varlog_file)
        self.varlog_search_btn.clicked.connect(self.search_selected_varlog_file)
        self.table.doubleClicked.connect(lambda: self.view_selected_varlog_file())

    def refresh_varlog(self):
        try:
            items = self.main_window.get_valid_backend().list_var_log()
            self.table.setRowCount(0)
            for name, size_b, mtime in items:
                r = self.table.rowCount()
                self.table.insertRow(r)

                it_name = QTableWidgetItem(name)
                # Force forward slashes for Linux paths, even if running on Windows
                full_path = f"{VAR_LOG_DIR}/{name}"
                it_name.setData(Qt.UserRole, full_path)

                it_size = QTableWidgetItem(f"{size_b / 1024:.2f}")
                it_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                it_time = QTableWidgetItem(str(mtime))

                self.table.setItem(r, 0, it_name)
                self.table.setItem(r, 1, it_size)
                self.table.setItem(r, 2, it_time)

            self.varlog_text.setPlainText(trans("msg_files_listed").format(path=VAR_LOG_DIR, count=len(items)))
        except Exception as e:
            show_error(self, trans("error"), str(e))

    def _selected_varlog_path(self) -> str | None:
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return None
        row = sel[0].row()
        item = self.table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def view_selected_varlog_file(self):
        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        path = self._selected_varlog_path()
        if not path:
            show_info(self, trans("info"), trans("select_file"))
            return
        lines = int(self.varlog_lines_spin.value())
        try:
            out = backend.tail(path, lines)
            sz = backend.size_bytes(path)
            header = f"{trans('info_file')} {path}\n{trans('info_size')} {sz/1024:.2f} KB\n--- {trans('info_last_lines').format(lines=lines)} ---\n\n"
            self.varlog_text.setPlainText(header + out)
            self.varlog_text.moveCursor(QTextCursor.End)
        except Exception as e:
            show_error(self, trans("error"), str(e))

    def search_selected_varlog_file(self):
        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        path = self._selected_varlog_path()
        if not path:
            show_info(self, trans("info"), trans("select_file"))
            return
        pattern = self.varlog_search_edit.text().strip()
        if not pattern:
            show_info(self, trans("info"), trans("enter_keyword"))
            return
        try:
            out = backend.search(path, pattern, tail_lines=8000, max_hits=400)
            if not out.strip():
                out = trans("no_match")
            sz = backend.size_bytes(path)
            header = f"{trans('info_search')} {pattern}\n{trans('info_file')} {path}\n{trans('info_size')} {sz/1024:.2f} KB\n--- {trans('info_matches')} ---\n\n"
            self.varlog_text.setPlainText(header + out)
        except Exception as e:
            show_error(self, trans("error"), str(e))

    def download_selected_varlog_file(self):
        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        path = self._selected_varlog_path()
        if not path:
            show_info(self, trans("info"), trans("select_file"))
            return
            
        filename = os.path.basename(path)
        save_path, _ = QFileDialog.getSaveFileName(self, trans("download_open"), filename)
        if not save_path:
            return
            
        try:
            msg = backend.download_file(path, save_path)
            
            box = QMessageBox()
            box.setText(f"{msg}\n{trans('open_file_ask')}")
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if box.exec() == QMessageBox.Yes:
                os.startfile(save_path)
            
        except Exception as e:
            show_error(self, trans("error"), str(e))

    def clear_selected_file(self):
        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        path = self._selected_varlog_path()
        if not path:
            return

        confirm = QMessageBox.question(self, trans("confirmation"), trans("msg_confirm_clear").format(path=path))
        if confirm != QMessageBox.Yes:
            return

        try:
            msg = backend.truncate(path)
            show_info(self, trans("success"), msg)
            self.view_selected_varlog_file() # Refresh view
            self.refresh_varlog() # Refresh list to update size
        except Exception as e:
            show_error(self, trans("error"), str(e))
