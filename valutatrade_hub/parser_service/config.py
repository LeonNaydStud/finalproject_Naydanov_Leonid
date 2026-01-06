"""
Конфигурация сервиса парсинга.
"""

import os
from dataclasses import dataclass
from typing import Tuple, Dict
from ..infra.settings import SettingsLoader


@dataclass
class ParserConfig:
    """Конфигурация парсера курсов валют."""

    # Ключ API
    EXCHANGERATE_API_KEY: str

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Базовые параметры
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple = ("EUR", "GBP", "RUB", "JPY", "CHF", "CNY")
    CRYPTO_CURRENCIES: Tuple = ("BTC", "ETH", "SOL", "ADA", "DOGE")

    # Сопоставление кодов криптовалют с ID в CoinGecko
    CRYPTO_ID_MAP: Dict = None

    # Пути к файлам
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10
    RETRY_COUNT: int = 3
    RETRY_DELAY: int = 1

    def __post_init__(self):
        """Инициализация после создания объекта."""
        if self.CRYPTO_ID_MAP is None:
            self.CRYPTO_ID_MAP = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
                "ADA": "cardano",
                "DOGE": "dogecoin",
            }


def create_parser_config() -> ParserConfig:
    """
    Создает конфигурацию парсера из настроек приложения.

    Returns:
        Объект ParserConfig
    """
    settings = SettingsLoader()

    # Получаем API ключ из настроек или переменных окружения
    api_key = settings.get("exchangerate_api_key") or os.getenv("EXCHANGERATE_API_KEY")

    if not api_key:
        raise ValueError(
            "API ключ для ExchangeRate-API не найден. "
            "Установите его в переменной окружения EXCHANGERATE_API_KEY "
            "или в настройках приложения."
        )

    # Получаем пути к файлам
    data_path = settings.get("data_path", "data")
    rates_file_path = os.path.join(data_path, "rates.json")
    history_file_path = os.path.join(data_path, "exchange_rates.json")

    # Получаем списки валют из настроек или используем значения по умолчанию
    fiat_currencies = settings.get("fiat_currencies", ("EUR", "GBP", "RUB", "JPY", "CHF", "CNY"))
    crypto_currencies = settings.get("crypto_currencies", ("BTC", "ETH", "SOL", "ADA", "DOGE"))

    # Создаем конфигурацию
    config = ParserConfig(
        EXCHANGERATE_API_KEY=api_key,
        RATES_FILE_PATH=rates_file_path,
        HISTORY_FILE_PATH=history_file_path,
        FIAT_CURRENCIES=tuple(fiat_currencies),
        CRYPTO_CURRENCIES=tuple(crypto_currencies),
        REQUEST_TIMEOUT=settings.get("request_timeout", 10),
    )

    return config