from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QGroupBox, QStyle, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from backend.base import Backend
from backend.lang_manager import trans

class MySQLTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Main Layout
        main_layout = QVBoxLayout(self)
        
        # Scroll Area for controls if window is small
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        
        # 1. Info Group
        info_group = QGroupBox(trans("info"))
        info_layout = QHBoxLayout(info_group)
        
        self.lbl_version = QLabel(trans("lbl_version_init"))
        self.lbl_port = QLabel(f"{trans('lbl_port')} -")
        self.lbl_socket = QLabel(trans("lbl_socket_init"))
        
        # Style
        for lbl in [self.lbl_version, self.lbl_port, self.lbl_socket]:
            lbl.setStyleSheet("font-weight: bold;")
            
        info_layout.addWidget(self.lbl_version)
        info_layout.addWidget(self.lbl_port)
        info_layout.addWidget(self.lbl_socket)
        info_layout.addStretch()
        
        self.btn_refresh = QPushButton(trans("refresh"))
        self.btn_refresh.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_refresh.clicked.connect(self.refresh_info)
        info_layout.addWidget(self.btn_refresh)
        
        self.layout.addWidget(info_group)

        # 2. Config Group
        conf_group = QGroupBox(trans("configuration"))
        conf_layout = QHBoxLayout(conf_group)
        self.lbl_bind = QLabel(trans("lbl_bind_init"))
        conf_layout.addWidget(self.lbl_bind)
        conf_layout.addStretch()
        self.layout.addWidget(conf_group)
        
        # 3. Service Status Group
        status_group = QGroupBox(trans("mysql_service").format(status=""))
        status_layout = QVBoxLayout(status_group)
        self.lbl_service_status = QLabel(trans("status_output"))
        self.lbl_service_status.setWordWrap(True)
        self.lbl_service_status.setStyleSheet("color: #cccccc;")
        status_layout.addWidget(self.lbl_service_status)
        self.layout.addWidget(status_group)

        # 4. Logs & Errors Group
        log_group = QGroupBox(trans("tab_nginx")) # reusing "Nginx Log & Kontrol" maybe not best, used translation key
        log_group.setTitle(trans("log_error_scan"))
        log_layout = QHBoxLayout(log_group)
        
        self.btn_error_log = QPushButton(trans("show_error_log"))
        self.btn_nginx_db_err = QPushButton(trans("search_db_nginx"))
        self.btn_sys_db_err = QPushButton(trans("search_db_sys"))
        
        for btn in [self.btn_error_log, self.btn_nginx_db_err, self.btn_sys_db_err]:
            btn.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxWarning))
            
        self.btn_error_log.clicked.connect(self.get_error_log)
        self.btn_nginx_db_err.clicked.connect(self.search_nginx_db_errors)
        self.btn_sys_db_err.clicked.connect(self.search_sys_db_errors)
        
        self.btn_clear_logs = QPushButton(trans("clear_mysql_logs"))
        self.btn_clear_logs.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.btn_clear_logs.setStyleSheet("color: red;")
        self.btn_clear_logs.clicked.connect(self.clear_mysql_logs)
        
        log_layout.addWidget(self.btn_error_log)
        log_layout.addWidget(self.btn_nginx_db_err)
        log_layout.addWidget(self.btn_sys_db_err)
        log_layout.addWidget(self.btn_clear_logs)
        self.layout.addWidget(log_group)

        # Output Area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText(trans("ph_output"))
        self.layout.addWidget(self.output_text, 1) # Give it stretch

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def get_backend(self) -> Backend:
        return self.main_window.get_valid_backend()

    def refresh_info(self):
        try:
            backend = self.get_backend()
        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")
            return
            
        self.log(trans("refresh") + "...")
        try:
            # Version
            ver = backend.get_mysql_version()
            self.lbl_version.setText(trans("mysql_version").format(version=ver))
            
            # Port
            port_out = backend.check_mysql_port()
            if "3306" in port_out:
                status_txt = "<span style='color:green'>" + trans("active") + "</span>"
            else:
                status_txt = "<span style='color:red'>" + trans("inactive") + "</span>"
            self.lbl_port.setText(trans("mysql_port").format(status=status_txt))

            # Socket
            sock = backend.check_mysql_socket()
            if "mysqld.sock" in sock:
                 status_txt = "<span style='color:green'>" + trans("success") + "</span>"
            else:
                 status_txt = "<span style='color:red'>" + trans("error") + "</span>"
            self.lbl_socket.setText(trans("mysql_socket").format(path=status_txt))

            # Bind Address
            bind = backend.check_mysql_bind_address()
            if bind:
                 self.lbl_bind.setText(trans("mysql_bind").format(addr=bind.strip()))
            else:
                 self.lbl_bind.setText(trans("mysql_bind").format(addr="?"))

            # Status
            status = backend.get_mysql_status()
            self.lbl_service_status.setText(status.strip())
            
            self.log(trans("success"))

        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")

    def get_error_log(self):
        self.log(trans("show_error_log") + "...")
        try:
            out = self.get_backend().get_mysql_error_log()
            self.log(out)
        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")

    def search_nginx_db_errors(self):
        self.log(trans("search_db_nginx") + "...")
        try:
            out = self.get_backend().search_db_errors_in_nginx()
            if not out.strip():
                self.log(trans("info") + ": Empty")
            else:
                self.log(out)
        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")

    def search_sys_db_errors(self):
        self.log(trans("search_db_sys") + "...")
        try:
            out = self.get_backend().search_db_errors_in_varlog()
            if not out.strip():
                self.log(trans("info") + ": Empty")
            else:
                self.log(out)
        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")

    def clear_mysql_logs(self):
        from PySide6.QtWidgets import QMessageBox
        confirm = QMessageBox.question(self, trans("confirmation"), trans("msg_confirm_clear_mysql"))
        if confirm != QMessageBox.Yes:
            return
        
        self.log(trans("clear_mysql_logs") + "...")
        try:
            msg = self.get_backend().truncate_mysql_logs()
            self.log(msg)
        except Exception as e:
            self.log_error(f"{trans('error')}: {e}")

    def log(self, msg: str):
        self.output_text.append(f"INFO: {msg}\n" + "-"*40)
        sb = self.output_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def log_error(self, msg: str):
        self.output_text.append(f"<span style='color:red'>ERROR: {msg}</span>\n" + "-"*40)
        sb = self.output_text.verticalScrollBar()
        sb.setValue(sb.maximum())
