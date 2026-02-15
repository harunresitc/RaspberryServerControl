import json
import os

class LanguageManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
            cls._instance.current_lang = "tr"
            cls._instance.translations = {}
            cls._instance.base_path = os.path.dirname(os.path.abspath(__file__))
            cls._instance.lang_dir = os.path.join(cls._instance.base_path, "..", "lang")
        return cls._instance

    def load_language(self, lang_code: str):
        self.current_lang = lang_code
        file_path = os.path.join(self.lang_dir, f"{lang_code}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
            except Exception as e:
                print(f"Dil dosyası yüklenemedi ({lang_code}): {e}")
                self.translations = {}
        else:
            print(f"Dil dosyası bulunamadı: {file_path}")
            self.translations = {}

    def trans(self, key: str, default=None) -> str:
        val = self.translations.get(key)
        if val is None:
            return default if default is not None else key
        return val

    def get_available_languages(self) -> list:
        langs = []
        if os.path.exists(self.lang_dir):
            for f in os.listdir(self.lang_dir):
                if f.endswith(".json"):
                    langs.append(f.replace(".json", ""))
        return langs
    
    # Singleton access
    @staticmethod
    def get_instance():
        if LanguageManager._instance is None:
            LanguageManager()
        return LanguageManager._instance

# Global helper
L = LanguageManager.get_instance()
def trans(key, default=None):
    return L.trans(key, default)
