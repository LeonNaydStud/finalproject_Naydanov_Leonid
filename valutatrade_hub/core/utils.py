"""
Вспомогательные функции и утилиты.
"""

import re
from typing import Dict, Any
from datetime import datetime
from ..core.exceptions import ValidationError
from ..core.currencies import CurrencyRegistry


def validate_currency_code(code: str) -> str:
    """
    Валидирует код валюты.

    Args:
        code: Код валюты

    Returns:
        Валидированный код валюты

    Raises:
        ValidationError: Если код невалидный
    """
    if not code or not isinstance(code, str):
        raise ValidationError("Код валюты не может быть пустым")

    code = code.upper().strip()

    # Проверяем формат
    if not re.match(r'^[A-Z]{2,5}$', code):
        raise ValidationError(
            f"Код валюты '{code}' должен содержать 2-5 заглавных букв"
        )

    # Проверяем наличие в реестре
    if code not in CurrencyRegistry.get_currency_codes():
        raise ValidationError(f"Валюта '{code}' не поддерживается")

    return code


def validate_amount(amount: Any) -> float:
    """
    Валидирует сумму.

    Args:
        amount: Сумма

    Returns:
        Валидированная сумма как float

    Raises:
        ValidationError: Если сумма невалидная
    """
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValidationError("Сумма должна быть числом")

    if amount <= 0:
        raise ValidationError("Сумма должна быть положительной")

    return amount


def validate_username(username: str) -> str:
    """
    Валидирует имя пользователя.

    Args:
        username: Имя пользователя

    Returns:
        Валидированное имя пользователя

    Raises:
        ValidationError: Если имя невалидное
    """
    if not username or not isinstance(username, str):
        raise ValidationError("Имя пользователя не может быть пустым")

    username = username.strip()

    if len(username) < 3:
        raise ValidationError("Имя пользователя должно содержать минимум 3 символа")

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError(
            "Имя пользователя может содержать только буквы, цифры и подчеркивания"
        )

    return username


def format_currency(value: float, currency_code: str) -> str:
    """
    Форматирует денежную сумму.

    Args:
        value: Сумма
        currency_code: Код валюты

    Returns:
        Отформатированная строка
    """
    # Определяем количество знаков после запятой
    if currency_code in ["JPY", "KRW", "VND"]:
        decimals = 0
    elif currency_code in ["BTC", "ETH"]:
        decimals = 8
    else:
        decimals = 2

    # Форматируем число
    formatted_value = f"{value:,.{decimals}f}"

    return f"{formatted_value} {currency_code}"


def parse_datetime_string(dt_string: str) -> datetime:
    """
    Парсит строку даты-времени в разных форматах.

    Args:
        dt_string: Строка с датой-временем

    Returns:
        Объект datetime
    """
    if not dt_string:
        raise ValidationError("Пустая строка даты")

    # Убираем возможные пробелы и символ Z
    dt_string = dt_string.strip().replace('Z', '+00:00')

    # Пробуем разные форматы
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # 2026-01-06T14:47:30.064766+00:00
        "%Y-%m-%dT%H:%M:%S.%f",  # 2026-01-06T14:47:30.064766
        "%Y-%m-%dT%H:%M:%S%z",  # 2026-01-06T14:47:30+00:00
        "%Y-%m-%dT%H:%M:%S",  # 2026-01-06T14:47:30
        "%Y-%m-%d %H:%M:%S",  # 2026-01-06 14:47:30
        "%Y-%m-%dT%H:%M",  # 2026-01-06T14:47
        "%Y-%m-%d",  # 2026-01-06
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_string, fmt)
        except ValueError:
            continue

    # Если ни один формат не подошел, пробуем из ISO формата
    try:
        from datetime import datetime as dt
        return dt.fromisoformat(dt_string)
    except ValueError:
        pass

    raise ValidationError(f"Невозможно распознать формат даты: {dt_string}")


def is_rate_fresh(timestamp: str, ttl_seconds: int = 300) -> bool:
    """
    Проверяет, свежий ли курс.

    Args:
        timestamp: Время обновления курса
        ttl_seconds: Время жизни кэша в секундах

    Returns:
        True если курс свежий, иначе False
    """
    try:
        if not timestamp:
            return False

        last_update = parse_datetime_string(timestamp)
        now = datetime.now()

        # Если дата в будущем (ошибка в данных)
        if last_update > now:
            return False

        return (now - last_update).total_seconds() < ttl_seconds
    except (ValueError, TypeError, ValidationError):
        # Если не удалось распарсить дату
        return False

def convert_currency(amount: float, from_currency: str, to_currency: str,
                     exchange_rates: Dict) -> float:
    """
    Конвертирует сумму из одной валюты в другую.

    Args:
        amount: Сумма для конвертации
        from_currency: Исходная валюта
        to_currency: Целевая валюта
        exchange_rates: Словарь курсов

    Returns:
        Конвертированная сумма
    """
    if from_currency == to_currency:
        return amount

    # Прямой курс
    rate_key = f"{from_currency}_{to_currency}"
    if rate_key in exchange_rates:
        return amount * exchange_rates[rate_key]

    # Обратный курс
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in exchange_rates:
        return amount / exchange_rates[reverse_key]

    # Через USD как промежуточную валюту
    if from_currency != "USD" and to_currency != "USD":
        # Конвертируем сначала в USD
        usd_amount = convert_currency(amount, from_currency, "USD", exchange_rates)
        # Затем из USD в целевую валюту
        return convert_currency(usd_amount, "USD", to_currency, exchange_rates)

    raise ValidationError(f"Не удалось найти курс для конвертации {from_currency} → {to_currency}")