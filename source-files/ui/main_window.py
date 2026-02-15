from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMessageBox, QLabel, QStatusBar, QApplication, QStyle, QHBoxLayout, QPushButton
)
from PySide6.QtCore import QTimer, QDateTime, Qt
import sys
import os

# Allow running this file directly
if __name__ == "__main__":
    # Add project root to sys.path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from backend.base import Backend
from backend.local import LocalBackend
from backend.ssh import SSHBackend
from backend.config import ConnConfig
from backend.settings import SettingsManager
from backend.lang_manager import L, trans

# Use absolute imports to allow running as main
from ui.connection_bar import ConnectionBar
from ui.nginx_tab import NginxTab
from ui.varlog_tab import VarLogTab
from ui.php_tab import PHPTab
from ui.mysql_tab import MySQLTab
from ui.utils import show_error, show_info
from ui.styles import DARK_THEME_QSS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load Language first
        lang = SettingsManager.get_language()
        L.load_language(lang)
        
        self.setWindowTitle(trans("app_title") + " v1.0.0")


        # Default backend
        self.cfg = ConnConfig(mode="local")
        self.backend: Backend | None = None # Start disconnected until user clicks Connect


        # Set Icon
        from PySide6.QtGui import QIcon
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        icon_path = os.path.join(project_root, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))


        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)

        # Connection Bar
        self.conn_bar = ConnectionBar(self)
        main.addWidget(self.conn_bar)

        # Tabs
        self.tabs = QTabWidget()
        main.addWidget(self.tabs, 1)

        self.tab_nginx = NginxTab(self)
        self.tab_varlog = VarLogTab(self)
        self.tab_php = PHPTab(self)
        self.tab_mysql = MySQLTab(self)
        
        # Add tabs with icons
        icon_nginx = self.style().standardIcon(QStyle.SP_ComputerIcon)
        icon_folder = self.style().standardIcon(QStyle.SP_DirIcon)
        icon_php = self.style().standardIcon(QStyle.SP_FileIcon)
        icon_db = self.style().standardIcon(QStyle.SP_DriveCDIcon)

        self.tabs.addTab(self.tab_nginx, icon_nginx, trans("tab_nginx"))
        self.tabs.addTab(self.tab_varlog, icon_folder, trans("tab_varlog"))
        self.tabs.addTab(self.tab_php, icon_php, trans("tab_php"))
        self.tabs.addTab(self.tab_mysql, icon_db, trans("tab_mysql"))

        # Custom Status Bar Widget
        self.status_widget = QWidget()
        self.status_layout = QHBoxLayout(self.status_widget)
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setSpacing(10)
        
        # Nginx Info
        self.nginx_label = QLabel(trans("lbl_nginx") + " -")
        self.nginx_reload_btn = QPushButton(trans("btn_reload"))
        self.nginx_restart_btn = QPushButton(trans("btn_restart"))
        self.nginx_stop_btn = QPushButton(trans("btn_stop"))
        
        # PHP Info
        self.php_label = QLabel(trans("lbl_php") + " -")
        self.php_reload_btn = QPushButton(trans("btn_reload"))
        self.php_restart_btn = QPushButton(trans("btn_restart"))
        self.php_stop_btn = QPushButton(trans("btn_stop"))

        # MySQL Info
        self.mysql_label = QLabel(trans("lbl_db") + " -")
        self.mysql_reload_btn = QPushButton(trans("btn_reload"))
        self.mysql_restart_btn = QPushButton(trans("btn_restart"))
        self.mysql_stop_btn = QPushButton(trans("btn_stop"))
        
        self.last_update_label = QLabel(trans("lbl_last") + " -")

        # Style buttons small
        for btn in [self.nginx_reload_btn, self.nginx_restart_btn, self.nginx_stop_btn,
                    self.php_reload_btn, self.php_restart_btn, self.php_stop_btn,
                    self.mysql_reload_btn, self.mysql_restart_btn, self.mysql_stop_btn]:
            btn.setFixedSize(60, 20)
            btn.setStyleSheet("font-size: 10px; padding: 0px;")

        # Add to layout
        # Nginx
        self.status_layout.addWidget(self.nginx_label)
        self.status_layout.addWidget(self.nginx_reload_btn)
        self.status_layout.addWidget(self.nginx_restart_btn)
        self.status_layout.addWidget(self.nginx_stop_btn)
        
        # Separator
        line1 = QLabel("|")
        line1.setStyleSheet("color: gray;")
        self.status_layout.addWidget(line1)
        
        # PHP
        self.status_layout.addWidget(self.php_label)
        self.status_layout.addWidget(self.php_reload_btn)
        self.status_layout.addWidget(self.php_restart_btn)
        self.status_layout.addWidget(self.php_stop_btn)

        # Separator
        line2 = QLabel("|")
        line2.setStyleSheet("color: gray;")
        self.status_layout.addWidget(line2)

        # MySQL
        self.status_layout.addWidget(self.mysql_label)
        self.status_layout.addWidget(self.mysql_reload_btn)
        self.status_layout.addWidget(self.mysql_restart_btn)
        self.status_layout.addWidget(self.mysql_stop_btn)
        
        self.status_layout.addStretch()
        self.status_layout.addWidget(self.last_update_label)

        # Connect buttons
        self.nginx_reload_btn.clicked.connect(lambda: self.control_service("nginx", "reload"))
        self.nginx_restart_btn.clicked.connect(lambda: self.control_service("nginx", "restart"))
        self.nginx_stop_btn.clicked.connect(lambda: self.control_service("nginx", "stop"))
        
        # PHP Dynamic Service Name
        self.current_php_service = None
        self.php_reload_btn.clicked.connect(lambda: self.control_service(self.current_php_service, "reload"))
        self.php_restart_btn.clicked.connect(lambda: self.control_service(self.current_php_service, "restart"))
        self.php_stop_btn.clicked.connect(lambda: self.control_service(self.current_php_service, "stop"))

        # MySQL Dynamic Service Name (mysql or mariadb)
        self.current_mysql_service = "mariadb"
        self.mysql_reload_btn.clicked.connect(lambda: self.control_service(self.current_mysql_service, "reload"))
        self.mysql_restart_btn.clicked.connect(lambda: self.control_service(self.current_mysql_service, "restart"))
        self.mysql_stop_btn.clicked.connect(lambda: self.control_service(self.current_mysql_service, "stop"))

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.addWidget(self.status_widget, 1) # 1 = stretch
        
        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_nginx_status)

        # Menu Bar
        self.create_menu()

        self.resize(1150, 700) # Slightly wider

    def create_menu(self):
        menu_bar = self.menuBar()
        
        # Language Menu
        lang_menu = menu_bar.addMenu(trans("menu_lang"))
        
        # English Action
        action_en = lang_menu.addAction("English")
        action_en.triggered.connect(lambda: self.change_language("en"))
        
        # Turkish Action
        action_tr = lang_menu.addAction("Türkçe")
        action_tr.triggered.connect(lambda: self.change_language("tr"))

    def control_service(self, service_name, action):
        if not service_name:
            show_error(self, trans("error"), trans("err_service_name"))
            return
            
        confirm = QMessageBox.question(self, trans("confirmation"), trans("msg_confirm_service_action").format(service=service_name, action=action))
        if confirm != QMessageBox.Yes:
            return
            
        try:
            msg = self.backend.control_service(service_name, action)
            show_info(self, trans("info"), msg)
            self.update_nginx_status() # Refresh status immediately
        except Exception as e:
            show_error(self, trans("err_op_failed"), str(e))

    def change_language(self, lang_code: str):
        SettingsManager.set_language(lang_code)
        L.load_language(lang_code)
        QMessageBox.information(self, trans("info"), trans("menu_restart_needed"))
        # Ideally, we would reload the whole UI, but a restart prompt is valid for complex apps
        # Updating just title as a sign
        self.setWindowTitle(trans("app_title") + " v1.0.0")

    def get_valid_backend(self) -> Backend:
        if not self.backend:
            raise Exception(trans("msg_connect_first"))
        return self.backend

    def apply_connection(self):
        # Called by ConnectionBar
        cfg = self.conn_bar.get_config()
        
        # Show connecting state
        # self.status_label was replaced by status_widget components. 
        # We can update one of the labels there, or just rely on cursor.
        # Let's update nginx_label temporarily or add a status label back?
        # Actually in previous step `status_label` was removed and replaced by `status_widget`.
        # so self.status_label does not exist!
        # I should use self.last_update_label or similar to show "Connecting..."
        self.last_update_label.setText(trans("status_connecting"))
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        
        try:
            if cfg.mode == "local":
                self.cfg = cfg
                self.backend = LocalBackend()
                # show_info(self, "OK", "Local mod aktif.") -> Custom success below
            else:
                # SSH
                try:
                    self.cfg = cfg
                    self.backend = SSHBackend(cfg)
                    # Simple test
                    _ = self.backend.tail("/etc/hostname", 1)
                except Exception as e:
                    show_error(self, trans("err_conn_failed"), str(e))
                    return

            # Success Dialog with Green Checkmark
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(trans("success"))
            msg_box.setText(f"{trans('msg_conn_success')}: {cfg.mode}")
            
            # Use StandardPixmap for tick if available, mostly DialogApplyButton is a tick
            msg_box.setIconPixmap(self.style().standardPixmap(QStyle.SP_DialogApplyButton))
            # Or if we want green specifically, we might need a custom icon or style sheet on the label?
            # StandardPixmap is safest for native look. SP_DialogApplyButton is usually a check.
            
            msg_box.exec()
            
            # Start monitoring
            self.update_nginx_status()
            self.tab_php.refresh_info() # Refresh PHP info on connect
            self.tab_mysql.refresh_info() # Refresh MySQL info on connect
            self.timer.start(60000) # 60 seconds
            
        finally:
              QApplication.restoreOverrideCursor()

    def update_nginx_status(self):
        if not self.backend:
            return
        
        try:
            # Nginx Status
            ver = self.backend.get_nginx_version()
            status = self.backend.get_nginx_status()
            
            s_lower = status.lower().strip()
            if "inactive" in s_lower:
                color = "red"
                short_status = trans("status_inactive")
            elif "active" in s_lower:
                color = "green"
                short_status = trans("status_active")
            else:
                color = "orange"
                short_status = trans("status_unknown")
            
            # Update Nginx Label
            self.nginx_label.setText(f"{trans('lbl_nginx')} {ver} | <span style='color:{color}; font-weight:bold'>{short_status}</span>")

            # PHP Status
            php_ver_raw = self.backend.get_php_version()
            # "PHP 8.2.7 (cli)..." -> "8.2.7"
            php_ver_short = php_ver_raw.split(' ')[1] if len(php_ver_raw.split(' ')) > 1 else "?"
            
            # Determine PHP Service Name
            php_status = self.backend.get_php_fpm_status(php_ver_raw)
            
            # Simple parsing again to find service name for buttons
            # We need a robust way. Backend could return name?
            # For now, replicate logic:
            import re
            match = re.search(r"PHP (\d+\.\d+)", php_ver_raw)
            if match:
                 self.current_php_service = f"php{match.group(1)}-fpm"
            else:
                 self.current_php_service = None

            p_lower = php_status.lower().strip()
            
            if "inactive" in p_lower:
                p_color = "red"
                p_short = trans("status_inactive")
            elif "active" in p_lower:
                p_color = "green"
                p_short = trans("status_active")
            elif "php yok" in p_lower or "bulunamadı" in p_lower:
                p_color = "gray"
                p_short = trans("status_not_found")
            else:
                p_color = "orange"
                p_short = trans("status_unknown")

            # Update PHP Label
            self.php_label.setText(f"{trans('lbl_php')} {php_ver_short} | <span style='color:{p_color}; font-weight:bold'>{p_short}</span>")
            
            # MySQL Status
            mysql_service = self.backend.get_mysql_service_name()
            self.current_mysql_service = mysql_service
            
            # For status bar we just want active/inactive, not full output
            # But get_mysql_status returns full output. We might need a simpler check or parse it.
            # LocalBackend.get_mysql_status is simulated. SSHBackend returns `systemctl status`.
            # Let's use get_mysql_status and parse "Active: active" line or similar.
            
            mysql_status_full = self.backend.get_mysql_status()
            m_lower = mysql_status_full.lower()
            
            if "active: active" in m_lower:
                m_color = "green"
                m_short = trans("status_active")
            elif "active: inactive" in m_lower or "dead" in m_lower:
                m_color = "red"
                m_short = trans("status_inactive")
            else:
                m_color = "orange"
                m_short = trans("status_unknown")
                
            # Version
            # get_mysql_version returns full string e.g. "mysql  Ver 15.1 ..."
            # Let's try to extract shorter version
            db_ver_raw = self.backend.get_mysql_version()
            # Try to simplify: "mysql Ver 15.1 Distrib 10.5.19-MariaDB" -> "10.5.19-MariaDB"
            # Split by Distrib? or just take first few words?
            # Or regex matching \d+\.\d+
            db_ver_short = "DB"
            match = re.search(r"Distrib (\d+\.\d+\.\d+-MariaDB)", db_ver_raw)
            if match:
                db_ver_short = match.group(1)
            else:
                # Fallback
                match = re.search(r"Ver (\d+\.\d+)", db_ver_raw)
                if match: db_ver_short = match.group(1)
            
            self.mysql_label.setText(f"{mysql_service}: {db_ver_short} | <span style='color:{m_color}; font-weight:bold'>{m_short}</span>")

            time_str = QDateTime.currentDateTime().toString("HH:mm:ss")
            self.last_update_label.setText(f"{trans('lbl_last')} {time_str}")
            
        except Exception as e:
            self.nginx_label.setText(f"Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
