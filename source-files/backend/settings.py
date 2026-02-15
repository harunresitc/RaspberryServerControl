import json
import os
from .config import ConnConfig

SETTINGS_FILE = "settings.json"

class SettingsManager:
    @staticmethod
    def load_settings() -> dict:
        if not os.path.exists(SETTINGS_FILE):
            return {}
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    @staticmethod
    def save_settings(data: dict):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Ayarlar kaydedilemedi: {e}")

    @staticmethod
    def get_language() -> str:
        data = SettingsManager.load_settings()
        return data.get("language", "tr")

    @staticmethod
    def set_language(lang_code: str):
        data = SettingsManager.load_settings()
        data["language"] = lang_code
        SettingsManager.save_settings(data)

    @staticmethod
    def load_last_config() -> ConnConfig | None:
        data = SettingsManager.load_settings()
        last = data.get("last_connection", {})
        if not last:
            return None
        return ConnConfig(
            mode=last.get("mode", "local"),
            host=last.get("host", ""),
            user=last.get("user", "pi"),
            port=last.get("port", 22),
            key_path=last.get("key_path", ""),
            use_sudo_nopass=last.get("use_sudo_nopass", True)
            # Password is deliberately NOT saved for security, user asked for it to be requested
        )

    @staticmethod
    def save_last_config(cfg: ConnConfig):
        data = SettingsManager.load_settings()
        data["last_connection"] = {
            "mode": cfg.mode,
            "host": cfg.host,
            "user": cfg.user,
            "port": cfg.port,
            "key_path": cfg.key_path,
            "use_sudo_nopass": cfg.use_sudo_nopass
            # No password saved
        }
        SettingsManager.save_settings(data)

