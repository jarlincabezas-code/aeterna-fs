import json
import os

class I18nManager:
    def __init__(self, language_code="en"):
        self.language_code = language_code
        self.translations = {}
        self._load_dictionary()

    def _load_dictionary(self):
        # Ruta dinámica para encontrar los archivos .json
        base_path = os.path.join(os.path.dirname(__file__), "..", "i18n")
        file_path = os.path.join(base_path, f"{self.language_code}.json")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            # Si no existe, cargar inglés por defecto
            default_path = os.path.join(base_path, "en.json")
            with open(default_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)

    def get(self, key):
        """Retorna la traducción o la llave si no existe."""
        return self.translations.get(key, key)