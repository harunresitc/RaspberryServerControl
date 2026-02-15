import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QSpinBox, 
    QPushButton, QCheckBox, QFileDialog, QStyle
)
from backend.config import ConnConfig
from backend.settings import SettingsManager

class ConnectionBar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        # ... existing init code ...
        self.main_window = main_window
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        from backend.lang_manager import trans

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Local", "SSH"])
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText(trans("ph_host"))
        self.user_edit = QLineEdit("pi")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(trans("ph_password"))
        self.password_edit.setEchoMode(QLineEdit.Password)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText(trans("ph_key"))
        self.key_btn = QPushButton(trans("btn_select_key"))
        self.key_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        
        self.connect_btn = QPushButton(trans("btn_connect_save"))
        self.connect_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.connect_btn.setStyleSheet("font-weight: bold; background-color: #264f78;")
        self.sudo_nopass_chk = QCheckBox(trans("chk_sudo_nopass"))
        self.sudo_nopass_chk.setChecked(True)

        # Row 0
        self.layout.addWidget(QLabel(trans("lbl_mode")), 0, 0)
        self.layout.addWidget(self.mode_combo, 0, 1)
        self.layout.addWidget(QLabel(trans("lbl_host")), 0, 2)
        self.layout.addWidget(self.host_edit, 0, 3)
        self.layout.addWidget(QLabel(trans("lbl_user")), 0, 4)
        self.layout.addWidget(self.user_edit, 0, 5)

        # Row 1
        self.layout.addWidget(QLabel(trans("lbl_port")), 1, 0)
        self.layout.addWidget(self.port_spin, 1, 1)
        self.layout.addWidget(QLabel(trans("lbl_password")), 1, 2)
        self.layout.addWidget(self.password_edit, 1, 3)
        self.layout.addWidget(QLabel(trans("lbl_key")), 1, 4)
        key_layout = QGridLayout() # sub layout to fit edit and btn
        self.layout.addWidget(self.key_edit, 1, 5)
        self.layout.addWidget(self.key_btn, 1, 6) # moved btn to next col

        # Row 2
        self.layout.addWidget(self.sudo_nopass_chk, 2, 0, 1, 2)
        self.layout.addWidget(self.connect_btn, 2, 2, 1, 5)

        # signals
        self.key_btn.clicked.connect(self.pick_key)
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.mode_combo.currentTextChanged.connect(self._mode_changed)
        
        # Connect Enter key in fields to connect action
        # Only for password field as requested
        self.password_edit.returnPressed.connect(self.on_connect_clicked)

        # Load settings
        self.load_defaults()

    def load_defaults(self):
        cfg = SettingsManager.load_last_config()
        if cfg:
            index = self.mode_combo.findText(cfg.mode.upper(), Qt.MatchFixedString) # Requires Qt import or case handling
            if cfg.mode.lower() == "ssh":
                self.mode_combo.setCurrentIndex(1) 
            else:
                self.mode_combo.setCurrentIndex(0)
                
            self.host_edit.setText(cfg.host)
            self.user_edit.setText(cfg.user)
            self.port_spin.setValue(cfg.port)
            self.key_edit.setText(cfg.key_path)
            self.sudo_nopass_chk.setChecked(cfg.use_sudo_nopass)
        
        self._mode_changed(self.mode_combo.currentText())

        # If SSH and host is filled, focus password
        if cfg and cfg.mode == "ssh" and cfg.host:
             self.password_edit.setFocus()

    def _mode_changed(self, text: str):
        is_ssh = (text.strip().lower() == "ssh")
        self.host_edit.setEnabled(is_ssh)
        self.user_edit.setEnabled(is_ssh)
        self.password_edit.setEnabled(is_ssh)
        self.port_spin.setEnabled(is_ssh)
        self.key_edit.setEnabled(is_ssh)
        self.key_btn.setEnabled(is_ssh)
        self.sudo_nopass_chk.setEnabled(is_ssh)

    def pick_key(self):
        path, _ = QFileDialog.getOpenFileName(self, trans("select_key"), os.path.expanduser("~"))
        if path:
            self.key_edit.setText(path)

    def on_connect_clicked(self):
        # Save before connecting
        cfg = self.get_config()
        SettingsManager.save_last_config(cfg)
        self.main_window.apply_connection()

    def get_config(self) -> ConnConfig:
        mode = self.mode_combo.currentText().strip().lower()
        if mode == "local":
            return ConnConfig(mode="local")
        
        return ConnConfig(
            mode="ssh",
            host=self.host_edit.text().strip(),
            user=self.user_edit.text().strip() or "pi",
            password=self.password_edit.text().strip(),
            port=int(self.port_spin.value()),
            key_path=self.key_edit.text().strip(),
            use_sudo_nopass=self.sudo_nopass_chk.isChecked(),
        )
