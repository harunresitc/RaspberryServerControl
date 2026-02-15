from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QGroupBox, QStyle
)
from PySide6.QtCore import Qt
from backend.base import Backend
from backend.lang_manager import trans

class PHPTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        
        # 1. Info Group
        info_group = QGroupBox(trans("info"))
        info_layout = QHBoxLayout(info_group)
        
        self.lbl_version = QLabel(trans("lbl_version_init"))
        self.lbl_fpm = QLabel(trans("lbl_fpm_init"))
        
        # Style labels
        self.lbl_version.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_fpm.setStyleSheet("font-weight: bold; font-size: 14px;")

        info_layout.addWidget(self.lbl_version)
        info_layout.addWidget(self.lbl_fpm)
        info_layout.addStretch()
        
        self.btn_refresh_info = QPushButton(trans("refresh"))
        self.btn_refresh_info.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_refresh_info.clicked.connect(self.refresh_info)
        info_layout.addWidget(self.btn_refresh_info)
        
        self.layout.addWidget(info_group)
        
        # 2. Controls Group
        ctrl_group = QGroupBox("Kontroller")
        ctrl_layout = QHBoxLayout(ctrl_group)
        
        self.btn_list_web = QPushButton(trans("list_web_root"))
        self.btn_list_web.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        
        self.btn_check_errors = QPushButton(trans("check_php_errors"))
        self.btn_check_errors.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxCritical))
        
        self.btn_list_web.clicked.connect(self.list_web_root)
        self.btn_check_errors.clicked.connect(self.check_php_errors)
        
        self.btn_clear_logs = QPushButton(trans("clear_php_logs"))
        self.btn_clear_logs.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.btn_clear_logs.setStyleSheet("color: red;")
        self.btn_clear_logs.clicked.connect(self.clear_php_logs)

        ctrl_layout.addWidget(self.btn_list_web)
        ctrl_layout.addWidget(self.btn_check_errors)
        ctrl_layout.addWidget(self.btn_clear_logs)
        
        self.layout.addWidget(ctrl_group)
        
        # 3. Output Area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText(trans("ph_output"))
        self.layout.addWidget(self.output_text)
        
    def get_backend(self) -> Backend:
        return self.main_window.get_valid_backend()
        
    def refresh_info(self):
        try:
            backend = self.get_backend()
        except Exception as e:
            self.lbl_version.setText("Ver: -")
            self.lbl_fpm.setText("FPM: -")
            self.log_error(f"{trans('error')}: {e}")
            return

        try:
            # 1. Get Version
            ver_raw = backend.get_php_version()
            # "PHP 8.2.7 (cli)..." -> "PHP 8.2.7"
            ver_short = ver_raw.split('(')[0].strip() if '(' in ver_raw else ver_raw
            self.lbl_version.setText(trans("php_version").format(version=ver_short))
            
            # 2. Get FPM Status
            # We need full version string for backend to parse "PHP 8.2..."
            status = backend.get_php_fpm_status(ver_raw)
            
            color = "orange"
            if "active" in status.lower() and "inactive" not in status.lower():
                color = "green"
                status_dsl = trans("active")
            elif "inactive" in status.lower() or "failed" in status.lower():
                color = "red"
                status_dsl = trans("inactive")
            else:
                status_dsl = status
                
            status_html = f"<span style='color:{color}'>{status_dsl}</span>"
            self.lbl_fpm.setText(trans("php_fpm_status").format(status=status_html))
            
            self.log(f"{trans('info')}: {ver_raw}\nSTATUS: {status}")
            
        except Exception as e:
            self.lbl_version.setText("Sürüm: Hata")
            self.lbl_fpm.setText("FPM: Hata")
            self.log_error(f"{trans('error')}: {e}")

    def list_web_root(self):
        self.log(trans("list_web_root") + "...")
        try:
            out = self.get_backend().list_web_root()
            self.log(out)
        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")

    def check_php_errors(self):
        self.log(trans("check_php_errors") + "...")
        try:
            out = self.get_backend().check_php_errors()
            if not out.strip():
                self.log(trans("info") + ": Empty")
            else:
                self.log(out)
        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")

    def clear_php_logs(self):
        from PySide6.QtWidgets import QMessageBox
        confirm = QMessageBox.question(self, trans("confirmation"), trans("msg_confirm_clear_php"))
        if confirm != QMessageBox.Yes:
            return
            
        try:
            msg = self.get_backend().truncate_php_logs()
            self.log(msg)
        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")

    def log(self, msg: str):
        self.output_text.append(f"INFO: {msg}\n" + "-"*40)
        # Scroll to bottom
        sb = self.output_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def log_error(self, msg: str):
        self.output_text.append(f"<span style='color:red'>ERROR: {msg}</span>\n" + "-"*40)
        sb = self.output_text.verticalScrollBar()
        sb.setValue(sb.maximum())
