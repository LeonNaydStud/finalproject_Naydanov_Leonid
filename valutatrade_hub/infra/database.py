"""
Модуль для работы с JSON хранилищем данных.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from ..infra.settings import SettingsLoader


class DatabaseManager:
    """
    Singleton класс для управления JSON хранилищем данных.
    """

    _instance = None

    def __new__(cls):
        """
        Реализация паттерна Singleton.

        Returns:
            Единственный экземпляр DatabaseManager
        """
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_database()
        return cls._instance

    def _init_database(self):
        """Инициализирует базу данных."""
        self.settings = SettingsLoader()
        self.data_path = Path(self.settings.get("data_path", "data"))

        # Создаем директорию если не существует
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Инициализируем файлы если не существуют
        self._init_file("users.json", [])
        self._init_file("portfolios.json", [])
        self._init_file("rates.json", {"pairs": {}, "last_refresh": None})
        self._init_file("exchange_rates.json", [])

    def _init_file(self, filename: str, default_content: Any):
        """
        Инициализирует файл с содержимым по умолчанию.

        Args:
            filename: Имя файла
            default_content: Содержимое по умолчанию
        """
        filepath = self.data_path / filename
        if not filepath.exists():
            self._save_json(filepath, default_content)

    def _get_filepath(self, filename: str) -> Path:
        """
        Возвращает полный путь к файлу.

        Args:
            filename: Имя файла

        Returns:
            Полный путь Path
        """
        return self.data_path / filename

    def _load_json(self, filepath: Path) -> Any:
        """
        Загружает JSON из файла.

        Args:
            filepath: Путь к файлу

        Returns:
            Загруженные данные

        Raises:
            FileNotFoundError: Если файл не существует
            json.JSONDecodeError: Если JSON поврежден
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Ошибка при чтении JSON из {filepath}: {e}", "", 0)

    def _save_json(self, filepath: Path, data: Any):
        """
        Сохраняет данные в JSON файл.

        Args:
            filepath: Путь к файлу
            data: Данные для сохранения
        """
        # Создаем временный файл для атомарной записи
        temp_filepath = filepath.with_suffix('.tmp')

        try:
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Заменяем оригинальный файл временным
            os.replace(temp_filepath, filepath)
        except Exception as e:
            # Удаляем временный файл в случае ошибки
            if temp_filepath.exists():
                os.remove(temp_filepath)
            raise IOError(f"Ошибка при сохранении файла {filepath}: {e}")

    def load_users(self) -> List[Dict]:
        """
        Загружает список пользователей.

        Returns:
            Список пользователей
        """
        filepath = self._get_filepath("users.json")
        return self._load_json(filepath)

    def save_users(self, users: List[Dict]):
        """
        Сохраняет список пользователей.

        Args:
            users: Список пользователей
        """
        filepath = self._get_filepath("users.json")
        self._save_json(filepath, users)

    def load_portfolios(self) -> List[Dict]:
        """
        Загружает список портфелей.

        Returns:
            Список портфелей
        """
        filepath = self._get_filepath("portfolios.json")
        return self._load_json(filepath)

    def save_portfolios(self, portfolios: List[Dict]):
        """
        Сохраняет список портфелей.

        Args:
            portfolios: Список портфелей
        """
        filepath = self._get_filepath("portfolios.json")
        self._save_json(filepath, portfolios)

    def save_portfolio(self, portfolio: Dict):
        """
        Сохраняет один портфель (добавляет или обновляет существующий).

        Args:
            portfolio: Данные портфеля
        """
        portfolios = self.load_portfolios()
        user_id = portfolio["user_id"]

        # Ищем существующий портфель
        found = False
        for i, p in enumerate(portfolios):
            if p["user_id"] == user_id:
                portfolios[i] = portfolio
                found = True
                break

        # Если не найден, добавляем новый
        if not found:
            portfolios.append(portfolio)

        self.save_portfolios(portfolios)

    def load_rates(self) -> Dict:
        """
        Загружает текущие курсы валют.

        Returns:
            Словарь с курсами
        """
        filepath = self._get_filepath("rates.json")
        return self._load_json(filepath)

    def save_rates(self, rates: Dict):
        """
        Сохраняет курсы валют.

        Args:
            rates: Словарь с курсами
        """
        filepath = self._get_filepath("rates.json")
        self._save_json(filepath, rates)

    def load_exchange_rates_history(self) -> List[Dict]:
        """
        Загружает историю курсов валют.

        Returns:
            Список исторических записей
        """
        filepath = self._get_filepath("exchange_rates.json")
        return self._load_json(filepath)

    def save_exchange_rates_history(self, history: List[Dict]):
        """
        Сохраняет историю курсов валют.

        Args:
            history: Список исторических записей
        """
        filepath = self._get_filepath("exchange_rates.json")
        self._save_json(filepath, history)

    def add_exchange_rate_record(self, record: Dict):
        """
        Добавляет запись в историю курсов.

        Args:
            record: Запись о курсе
        """
        history = self.load_exchange_rates_history()
        history.append(record)
        self.save_exchange_rates_history(history)

    def get_last_exchange_rate(self, from_currency: str, to_currency: str) -> Dict:
        """
        Получает последнюю запись о курсе для пары валют.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта

        Returns:
            Последняя запись о курсе или пустой словарь если не найдена
        """
        history = self.load_exchange_rates_history()

        # Ищем последнюю запись для пары валют
        for record in reversed(history):
            if (record.get("from_currency") == from_currency and
                    record.get("to_currency") == to_currency):
                return record

        return {}