from abc import ABC, abstractmethod
from .exceptions import CurrencyNotFoundError

class Currency(ABC):
    def __init__(self, code: str, name: str):
        code = code.upper()
        if not (2 <= len(code) <= 5) or ' ' in code:
            raise ValueError("Некорректный код валюты")
        if not name:
            raise ValueError("Имя валюты не может быть пустым")
        self.code = code
        self.name = name

    @abstractmethod
    def get_display_info(self) -> str:
        pass

class FiatCurrency(Currency):
    def __init__(self, code, name, issuing_country):
        super().__init__(code, name)
        self.issuing_country = issuing_country

    def get_display_info(self):
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    def __init__(self, code, name, algorithm, market_cap):
        super().__init__(code, name)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self):
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"

_currency_registry = {
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 4.2e11),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia")
}

def get_currency(code: str) -> Currency:
    code = code.upper()
    if code not in _currency_registry:
        raise CurrencyNotFoundError(code)
    return _currency_registry[code]
