import os
import shlex
from PySide6.QtCore import QProcess
from PySide6.QtGui import QFont, QColor
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, 
    QPushButton, QLineEdit, QTextEdit, QMessageBox, QFileDialog, QStyle
)
from backend.local import NGINX_ERROR, NGINX_ACCESS
from .highlighter import LogHighlighter
from .utils import show_error, show_info
from backend.lang_manager import trans

class NginxTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        # ... existing init ...
        self.main_window = main_window
        self.live_process: QProcess | None = None
        
        layout = QVBoxLayout(self)

        # Top Bar
        top = QHBoxLayout()
        self.lines_spin = QSpinBox()
        self.lines_spin.setRange(10, 20000)
        self.lines_spin.setValue(200)
        top.addWidget(QLabel(trans("lines_label")))
        top.addWidget(self.lines_spin)

        self.which_combo = QComboBox()
        self.which_combo.addItems(["nginx error.log", "nginx access.log"])
        top.addWidget(self.which_combo)

        self.refresh_btn = QPushButton(trans("show"))
        self.refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        
        # Use Unicode for dynamic color (white in dark mode, black in light mode)
        self.live_btn = QPushButton("▶ " + trans("start_live"))
        self.live_btn.setStyleSheet("font-weight: bold;")
        
        self.stop_live_btn = QPushButton("■ " + trans("stop_live"))
        self.stop_live_btn.setStyleSheet("font-weight: bold;")
        self.stop_live_btn.setEnabled(False)
        
        self.download_btn = QPushButton(trans("download_open")) 
        self.download_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        
        self.clear_btn = QPushButton(trans("clear_log"))
        self.clear_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.clear_btn.setStyleSheet("background-color: darkred; color: white;") 

        self.clear_all_btn = QPushButton(trans("clear_all_nginx"))
        self.clear_all_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.clear_all_btn.setStyleSheet("background-color: #800000; color: white; font-weight: bold;")

        self.test_conf_btn = QPushButton(trans("test_config"))
        self.test_conf_btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))

        top.addWidget(self.refresh_btn)
        top.addWidget(self.live_btn)
        top.addWidget(self.stop_live_btn)
        top.addWidget(self.download_btn)
        top.addWidget(self.test_conf_btn) 
        top.addStretch(1)
        top.addWidget(self.clear_btn)
        top.addWidget(self.clear_all_btn)

        layout.addLayout(top)

        # Search & Filter Bar
        search_bar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(trans("filter_placeholder"))
        self.search_btn = QPushButton(trans("filter_btn"))
        self.search_limit_spin = QSpinBox()
        self.search_limit_spin.setRange(100, 50000)
        self.search_limit_spin.setValue(5000)
        
        # Quick Filters
        self.filter_error_btn = QPushButton(trans("filter_error_btn"))
        self.filter_error_btn.setStyleSheet("color: red; font-weight: bold;")
        self.filter_warn_btn = QPushButton(trans("filter_warn_btn"))
        self.filter_warn_btn.setStyleSheet("color: darkorange; font-weight: bold;")
        
        search_bar.addWidget(QLabel(trans("search_label")))
        search_bar.addWidget(self.search_edit, 1)
        search_bar.addWidget(self.filter_error_btn)
        search_bar.addWidget(self.filter_warn_btn)
        search_bar.addWidget(QLabel(trans("last_lines_label")))
        search_bar.addWidget(self.search_limit_spin)
        search_bar.addWidget(self.search_btn)
        layout.addLayout(search_bar)

        # Info
        info = QHBoxLayout()
        self.size_label = QLabel(trans("log_size_label"))
        info.addWidget(self.size_label)
        info.addStretch(1)
        layout.addLayout(info)

        # Text Area
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Consolas", 10))
        # Highlight
        self.highlighter = LogHighlighter(self.text.document())
        layout.addWidget(self.text, 1)

        # signals
        self.refresh_btn.clicked.connect(self.show_selected_log)
        self.clear_btn.clicked.connect(self.clear_selected_log)
        self.clear_all_btn.clicked.connect(self.clear_all_logs)
        self.search_btn.clicked.connect(self.search_in_selected_log)
        self.live_btn.clicked.connect(self.start_live)
        self.stop_live_btn.clicked.connect(self.stop_live)
        
        # New buttons
        self.download_btn.clicked.connect(self.download_log)
        self.test_conf_btn.clicked.connect(self.test_nginx_config)
        self.filter_error_btn.clicked.connect(lambda: self.quick_filter("error"))
        self.filter_warn_btn.clicked.connect(lambda: self.quick_filter("warn"))

    def selected_path(self) -> str:
        if self.which_combo.currentIndex() == 0:
            return NGINX_ERROR
        return NGINX_ACCESS

    def set_text(self, s: str):
        self.text.setPlainText(s)
        self.text.moveCursor(QTextCursor.End)

    def show_size_for(self, path: str):
        try:
            sz = self.main_window.get_valid_backend().size_bytes(path)
            self.size_label.setText(f"Log Size: {sz / 1024:.2f} KB")
        except Exception as e:
            self.size_label.setText(f"Log Size: ?")

    def show_selected_log(self):
        path = self.selected_path()
        lines = int(self.lines_spin.value())
        try:
            out = self.main_window.get_valid_backend().tail(path, lines)
            self.set_text(out)
            self.show_size_for(path)
        except Exception as e:
            show_error(self, trans("error"), str(e))

    def clear_selected_log(self):
        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        path = self.selected_path()
        confirm = QMessageBox.question(self, trans("confirmation"), trans("msg_confirm_clear").format(path=path))
        if confirm != QMessageBox.Yes:
            return
        try:
            msg = backend.truncate(path)
            self.set_text(msg)
            self.show_size_for(path)
        except Exception as e:
            show_error(self, trans("error"), str(e))

    def clear_all_logs(self):
        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        confirm = QMessageBox.question(self, trans("confirmation"), trans("msg_confirm_clear_all_nginx"))
        if confirm != QMessageBox.Yes:
            return
            
        try:
            msg = backend.truncate_all_nginx_logs()
            show_info(self, trans("success"), msg)
            self.show_selected_log() # Refresh current view
        except Exception as e:
            show_error(self, trans("error"), str(e))

    def search_in_selected_log(self):
        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        path = self.selected_path()
        pattern = self.search_edit.text().strip()
        if not pattern:
            show_info(self, trans("info"), trans("filter_placeholder")) # Using placeholder as "Enter keyword" msg
            return
        tail_lines = int(self.search_limit_spin.value())
        try:
            out = backend.search(path, pattern, tail_lines=tail_lines)
            if not out.strip():
                out = trans("no_match")
            self.set_text(out)
            self.show_size_for(path)
        except Exception as e:
            QMessageBox.critical(self, trans("error"), str(e))
            
    def quick_filter(self, keyword):
        self.search_edit.setText(keyword)
        self.search_in_selected_log()

    def start_live(self):
        if self.live_process is not None:
            return

        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        path = self.selected_path()
        self.text.clear()
        self.stop_live_btn.setEnabled(True)
        self.live_btn.setEnabled(False)

        cfg = backend.cfg
        
        if cfg.mode == "local":
            self.live_process = QProcess(self)
            self.live_process.setProcessChannelMode(QProcess.MergedChannels)
            self.live_process.readyReadStandardOutput.connect(self._on_live_output)
            self.live_process.finished.connect(self._on_live_finished)
            self.live_process.start("tail", ["-f", path])
        else:
            # SSH mode: Use SSHLogThread with paramiko
            from backend.ssh_thread import SSHLogThread
            # If backend is generic Backend type, we assume it's SSHBackend for ssh mode
            self.live_process = SSHLogThread(backend, path)
            self.live_process.log_output.connect(self._on_thread_output)
            self.live_process.error_occurred.connect(self._on_thread_error)
            self.live_process.finished.connect(self._on_live_finished)
            self.live_process.start()

        self.show_size_for(path)

    def _on_live_output(self):
        # For QProcess (Local)
        if not self.live_process or not isinstance(self.live_process, QProcess):
            return
        data = bytes(self.live_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.text.moveCursor(QTextCursor.End)
        self.text.insertPlainText(data)
        self.text.moveCursor(QTextCursor.End)

    def _on_thread_output(self, line: str):
        # For SSHLogThread
        self.text.moveCursor(QTextCursor.End)
        self.text.insertPlainText(line)
        self.text.moveCursor(QTextCursor.End)

    def _on_thread_error(self, err: str):
        self.text.moveCursor(QTextCursor.End)
        self.text.insertPlainText(f"\n[HATA] {err}\n")
        self.text.moveCursor(QTextCursor.End)

    def _on_live_finished(self):
        self.live_process = None
        self.stop_live_btn.setEnabled(False)
        self.live_btn.setEnabled(True)

    def stop_live(self):
        if self.live_process:
            if isinstance(self.live_process, QProcess):
                self.live_process.kill()
            else:
                # SSHLogThread
                self.live_process.stop()
            self.live_process = None
        self.stop_live_btn.setEnabled(False)
        self.live_btn.setEnabled(True)
        
    def download_log(self):
        try:
            backend = self.main_window.get_valid_backend()
        except Exception as e:
            show_error(self, trans("error"), str(e))
            return

        path = self.selected_path()
        # Suggest filename based on log name + timestamp or just log name
        filename = os.path.basename(path)
        save_path, _ = QFileDialog.getSaveFileName(self, trans("download_open"), filename)
        if not save_path:
            return
            
        try:
            msg = backend.download_file(path, save_path)
            
            # Ask to open
            box = QMessageBox()
            box.setText(f"{msg}\n{trans('open_file_ask')}")
            box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if box.exec() == QMessageBox.Yes:
                # Open file with default OS editor
                os.startfile(save_path) # Windows only? For cross platform `os.startfile` is windows specific.
        except Exception as e:
            show_error(self, trans("error"), str(e))

    def test_nginx_config(self):
        try:
            out = self.main_window.get_valid_backend().check_nginx_config()
            # Show result
            if "syntax is ok" in out and "test is successful" in out:
                show_info(self, trans("success"), out)
            else:
                if "test is successful" in out:
                     show_info(self, trans("info"), out)
                else:
                     show_error(self, trans("error"), out)
        except Exception as e:
            show_error(self, trans("error"), str(e))
