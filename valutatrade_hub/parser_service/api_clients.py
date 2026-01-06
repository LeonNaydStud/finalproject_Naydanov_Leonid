"""
Клиенты для работы с внешними API.
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, Optional

from ..core.exceptions import ApiRequestError
from .config import ParserConfig


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API клиентов."""

    def __init__(self, config: ParserConfig):
        """
        Инициализация клиента.

        Args:
            config: Конфигурация парсера
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ValutaTradeHub/1.0',
            'Accept': 'application/json'
        })

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает курсы валют.

        Returns:
            Словарь с курсами валют

        Raises:
            ApiRequestError: При ошибке запроса
        """
        pass

    def _make_request(self, url: str, params: Optional[Dict] = None,
                      max_retries: int = None) -> requests.Response:
        """
        Выполняет HTTP запрос с повторными попытками.

        Args:
            url: URL для запроса
            params: Параметры запроса
            max_retries: Максимальное количество попыток

        Returns:
            Ответ сервера

        Raises:
            ApiRequestError: При ошибке запроса после всех попыток
        """
        if max_retries is None:
            max_retries = self.config.RETRY_COUNT

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                return response

            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise ApiRequestError(f"Таймаут запроса к {url}")

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise ApiRequestError(f"Ошибка соединения с {url}")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    if attempt < max_retries:
                        # Экспоненциальная задержка
                        delay = self.config.RETRY_DELAY * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    raise ApiRequestError("Превышен лимит запросов к API")
                else:
                    raise ApiRequestError(f"HTTP ошибка {e.response.status_code}: {e}")

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise ApiRequestError(f"Ошибка запроса к {url}: {str(e)}")

        # Если все попытки не удались
        raise ApiRequestError(f"Не удалось выполнить запрос после {max_retries} попыток: {last_exception}")


class CoinGeckoClient(BaseApiClient):
    """Клиент для работы с CoinGecko API."""

    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает курсы криптовалют от CoinGecko.

        Returns:
            Словарь с курсами криптовалют к USD
        """
        # Формируем список ID криптовалют
        crypto_ids = []
        crypto_codes = []

        for code in self.config.CRYPTO_CURRENCIES:
            if code in self.config.CRYPTO_ID_MAP:
                crypto_ids.append(self.config.CRYPTO_ID_MAP[code])
                crypto_codes.append(code)

        if not crypto_ids:
            return {}

        # Формируем параметры запроса
        params = {
            'ids': ','.join(crypto_ids),
            'vs_currencies': 'usd'
        }

        # Выполняем запрос
        response = self._make_request(self.config.COINGECKO_URL, params)
        data = response.json()

        # Извлекаем курсы
        rates = {}
        for code, crypto_id in zip(crypto_codes, crypto_ids):
            if crypto_id in data and 'usd' in data[crypto_id]:
                rate_key = f"{code}_{self.config.BASE_CURRENCY}"
                rates[rate_key] = float(data[crypto_id]['usd'])

        return rates


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для работы с ExchangeRate-API."""

    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает курсы фиатных валют от ExchangeRate-API.

        Returns:
            Словарь с курсами фиатных валют к USD
        """
        # Формируем URL запроса
        url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/USD"

        # Выполняем запрос
        response = self._make_request(url)
        data = response.json()

        # Проверяем успешность ответа
        if data.get('result') != 'success':
            raise ApiRequestError(f"API вернуло ошибку: {data.get('error-type', 'Неизвестная ошибка')}")

        # Извлекаем курсы
        rates = {}
        base_currency = data.get('base_code', 'USD')

        for target_currency in self.config.FIAT_CURRENCIES:
            if target_currency in data.get('rates', {}):
                rate_key = f"{target_currency}_{base_currency}"
                rates[rate_key] = float(data['rates'][target_currency])

        return rates

    def get_supported_currencies(self) -> Dict:
        """
        Получает список поддерживаемых валют.

        Returns:
            Словарь с информацией о поддерживаемых валютах
        """
        url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/codes"

        response = self._make_request(url)
        data = response.json()

        if data.get('result') != 'success':
            raise ApiRequestError(f"API вернуло ошибку: {data.get('error-type', 'Неизвестная ошибка')}")

        return data