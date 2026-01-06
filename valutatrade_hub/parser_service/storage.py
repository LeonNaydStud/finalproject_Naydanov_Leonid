"""
Модуль для работы с хранилищем данных парсера.
"""

import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class ParserStorage:
    """Класс для работы с хранилищем данных парсера."""

    def __init__(self, history_file_path: str):
        """
        Инициализация хранилища.

        Args:
            history_file_path: Путь к файлу истории
        """
        self.history_file_path = Path(history_file_path)
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """Создает директорию для файлов если она не существует."""
        self.history_file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_history_record(self, record: Dict[str, Any]):
        """
        Сохраняет запись в историю.

        Args:
            record: Запись для сохранения
        """
        # Загружаем существующую историю
        history = self.load_history()

        # Добавляем новую запись
        history.append(record)

        # Сохраняем атомарно
        self._save_json_atomic(self.history_file_path, history)

    def load_history(self) -> List[Dict[str, Any]]:
        """
        Загружает историю курсов.

        Returns:
            Список исторических записей
        """
        if not self.history_file_path.exists():
            return []

        try:
            with open(self.history_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Если файл поврежден, создаем новый
            return []

    def get_recent_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает последние записи из истории.

        Args:
            limit: Максимальное количество записей

        Returns:
            Список последних записей
        """
        history = self.load_history()
        return history[-limit:] if history else []

    def get_currency_pair_history(self, from_currency: str, to_currency: str,
                                  limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получает историю для конкретной пары валют.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            limit: Максимальное количество записей

        Returns:
            Список записей для пары валют
        """
        history = self.load_history()
        pair_history = []

        for record in reversed(history):
            if (record.get('from_currency') == from_currency and
                    record.get('to_currency') == to_currency):
                pair_history.append(record)

                if len(pair_history) >= limit:
                    break

        return list(reversed(pair_history))

    def get_last_rate(self, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Получает последний курс для пары валют.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта

        Returns:
            Последняя запись о курсе или пустой словарь
        """
        history = self.get_currency_pair_history(from_currency, to_currency, limit=1)
        return history[0] if history else {}

    def cleanup_old_records(self, max_age_days: int = 30):
        """
        Удаляет старые записи из истории.

        Args:
            max_age_days: Максимальный возраст записей в днях
        """
        history = self.load_history()
        cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        filtered_history = []
        for record in history:
            try:
                record_date = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                if record_date.timestamp() > cutoff_date:
                    filtered_history.append(record)
            except (KeyError, ValueError):
                # Пропускаем записи с некорректными датами
                continue

        # Сохраняем отфильтрованную историю
        self._save_json_atomic(self.history_file_path, filtered_history)

        removed_count = len(history) - len(filtered_history)
        if removed_count > 0:
            print(f"Удалено {removed_count} старых записей из истории")

    def _save_json_atomic(self, filepath: Path, data: Any):
        """
        Сохраняет JSON атомарно через временный файл.

        Args:
            filepath: Путь к файлу
            data: Данные для сохранения
        """
        # Создаем временный файл
        temp_fd, temp_path = tempfile.mkstemp(
            prefix=filepath.stem,
            suffix='.tmp',
            dir=filepath.parent
        )

        try:
            # Записываем данные во временный файл
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Заменяем оригинальный файл временным
            os.replace(temp_path, filepath)

        except Exception:
            # В случае ошибки удаляем временный файл
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise