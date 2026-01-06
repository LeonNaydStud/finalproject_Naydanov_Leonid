"""
Модуль для работы с валютами (фиатными и криптовалютными).
"""

from abc import ABC, abstractmethod
from typing import Dict
from ..core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для валют."""

    def __init__(self, name: str, code: str):
        """
        Инициализация валюты.

        Args:
            name: Человекочитаемое имя валюты
            code: Код валюты (ISO код или тикер)
        """
        if not name or not isinstance(name, str):
            raise ValueError("Имя валюты не может быть пустым")

        if not code or not isinstance(code, str):
            raise ValueError("Код валюты не может быть пустым")

        code = code.upper().strip()
        if len(code) < 2 or len(code) > 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")
        if ' ' in code:
            raise ValueError("Код валюты не может содержать пробелы")

        self._name = name
        self._code = code

    @property
    def name(self) -> str:
        """Возвращает имя валюты."""
        return self._name

    @property
    def code(self) -> str:
        """Возвращает код валюты."""
        return self._code

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты."""
        pass

    def __str__(self) -> str:
        return self.get_display_info()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', code='{self.code}')"


class FiatCurrency(Currency):
    """Класс для фиатных валют."""

    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализация фиатной валюты.

        Args:
            name: Имя валюты
            code: Код валюты
            issuing_country: Страна/зона эмиссии
        """
        super().__init__(name, code)
        self._issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        """Возвращает страну эмиссии."""
        return self._issuing_country

    def get_display_info(self) -> str:
        """Возвращает строковое представление фиатной валюты."""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Класс для криптовалют."""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        """
        Инициализация криптовалюты.

        Args:
            name: Имя криптовалюты
            code: Код криптовалюты
            algorithm: Алгоритм консенсуса
            market_cap: Рыночная капитализация
        """
        super().__init__(name, code)
        self._algorithm = algorithm
        self._market_cap = market_cap

    @property
    def algorithm(self) -> str:
        """Возвращает алгоритм консенсуса."""
        return self._algorithm

    @property
    def market_cap(self) -> float:
        """Возвращает рыночную капитализацию."""
        return self._market_cap

    @market_cap.setter
    def market_cap(self, value: float):
        """Устанавливает рыночную капитализацию."""
        if value < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
        self._market_cap = value

    def get_display_info(self) -> str:
        """Возвращает строковое представление криптовалюты."""
        mcap_str = f"{self.market_cap:.2e}" if self.market_cap > 1e6 else f"{self.market_cap:,.2f}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


# Реестр валют
class CurrencyRegistry:
    """Реестр всех доступных валют."""

    _currencies: Dict[str, Currency] = {}

    @classmethod
    def register(cls, currency: Currency):
        """Регистрирует валюту в реестре."""
        cls._currencies[currency.code] = currency

    @classmethod
    def get_currency(cls, code: str) -> Currency:
        """
        Возвращает объект валюты по коду.

        Args:
            code: Код валюты

        Returns:
            Объект Currency

        Raises:
            CurrencyNotFoundError: Если валюта не найдена
        """
        code = code.upper()
        if code not in cls._currencies:
            raise CurrencyNotFoundError(code)
        return cls._currencies[code]

    @classmethod
    def get_all_currencies(cls) -> Dict[str, Currency]:
        """Возвращает все зарегистрированные валюты."""
        return cls._currencies.copy()

    @classmethod
    def get_currency_codes(cls) -> list:
        """Возвращает список всех кодов валют."""
        return list(cls._currencies.keys())


# Инициализация реестра с основными валютами
def initialize_currencies():
    """Инициализирует реестр валют основными валютами."""
    # Фиатные валюты
    fiat_currencies = [
        FiatCurrency("US Dollar", "USD", "United States"),
        FiatCurrency("Euro", "EUR", "Eurozone"),
        FiatCurrency("British Pound", "GBP", "United Kingdom"),
        FiatCurrency("Russian Ruble", "RUB", "Russia"),
        FiatCurrency("Japanese Yen", "JPY", "Japan"),
        FiatCurrency("Swiss Franc", "CHF", "Switzerland"),
        FiatCurrency("Chinese Yuan", "CNY", "China"),
    ]

    # Криптовалюты
    crypto_currencies = [
        CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        CryptoCurrency("Ethereum", "ETH", "Ethash", 3.72e11),
        CryptoCurrency("Solana", "SOL", "Proof of History", 6.54e10),
        CryptoCurrency("Cardano", "ADA", "Ouroboros", 2.15e10),
        CryptoCurrency("Dogecoin", "DOGE", "Scrypt", 2.0e10),
    ]

    # Регистрация всех валют
    for currency in fiat_currencies + crypto_currencies:
        CurrencyRegistry.register(currency)


# Инициализация при импорте
initialize_currencies()


def get_currency(code: str) -> Currency:
    """
    Фабричный метод для получения валюты по коду.

    Args:
        code: Код валюты

    Returns:
        Объект Currency
    """
    return CurrencyRegistry.get_currency(code)