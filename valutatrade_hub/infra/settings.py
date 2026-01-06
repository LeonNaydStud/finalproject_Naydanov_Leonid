"""
Модуль для загрузки и управления настройками приложения.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict


class SettingsLoader:
    """
    Singleton класс для загрузки и управления настройками.
    """

    _instance = None
    _settings = None

    def __new__(cls):
        """
        Реализация паттерна Singleton через __new__.

        Returns:
            Единственный экземпляр SettingsLoader
        """
        if cls._instance is None:
            cls._instance = super(SettingsLoader, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self):
        """Загружает настройки из различных источников."""
        self._settings = {}

        # 1. Загружаем настройки из pyproject.toml (секция [tool.valutatrade])
        try:
            import tomllib
            pyproject_path = Path("pyproject.toml")
            if pyproject_path.exists():
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomllib.load(f)
                    valutatrade_settings = pyproject_data.get("tool", {}).get("valutatrade", {})
                    self._settings.update(valutatrade_settings)
        except (ImportError, FileNotFoundError, KeyError):
            pass  # Пропускаем если не удалось загрузить

        # 2. Загружаем настройки из переменных окружения
        env_settings = {
            "data_path": os.getenv("VALUTATRADE_DATA_PATH"),
            "rates_ttl_seconds": os.getenv("VALUTATRADE_RATES_TTL_SECONDS"),
            "default_base_currency": os.getenv("VALUTATRADE_DEFAULT_BASE_CURRENCY"),
            "log_file": os.getenv("VALUTATRADE_LOG_FILE"),
            "exchangerate_api_key": os.getenv("EXCHANGERATE_API_KEY"),
        }

        # Фильтруем None значения и конвертируем типы
        for key, value in env_settings.items():
            if value is not None:
                if key == "rates_ttl_seconds":
                    self._settings[key] = int(value)
                else:
                    self._settings[key] = value

        # 3. Загружаем настройки из config.json если существует
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self._settings.update(config_data)
            except (json.JSONDecodeError, IOError):
                pass

        # 4. Устанавливаем значения по умолчанию
        defaults = {
            "data_path": "data",
            "rates_ttl_seconds": 300,  # 5 минут
            "default_base_currency": "USD",
            "log_file": "logs/actions.log",
            "exchangerate_api_key": None,
        }

        for key, default_value in defaults.items():
            if key not in self._settings:
                self._settings[key] = default_value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение настройки.

        Args:
            key: Ключ настройки
            default: Значение по умолчанию

        Returns:
            Значение настройки или default если не найдено
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        """
        Устанавливает значение настройки.

        Args:
            key: Ключ настройки
            value: Новое значение
        """
        self._settings[key] = value

    def reload(self):
        """Перезагружает настройки из источников."""
        self._load_settings()

    def to_dict(self) -> Dict:
        """
        Возвращает все настройки в виде словаря.

        Returns:
            Словарь с настройками
        """
        return self._settings.copy()

    def save_to_file(self, filepath: str = "config.json"):
        """
        Сохраняет текущие настройки в файл.

        Args:
            filepath: Путь к файлу
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise IOError(f"Не удалось сохранить настройки: {e}")