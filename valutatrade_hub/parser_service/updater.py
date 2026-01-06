"""
Модуль для обновления курсов валют.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig, create_parser_config
from ..core.exceptions import ApiRequestError
from ..infra.database import DatabaseManager

logger = logging.getLogger(__name__)


class RatesUpdater:
    """Класс для обновления курсов валют."""

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Инициализация обновления.

        Args:
            config: Конфигурация парсера
        """
        self.config = config or create_parser_config()
        self.db = DatabaseManager()

        # Инициализируем клиенты
        self.clients = {
            'coingecko': CoinGeckoClient(self.config),
            'exchangerate': ExchangeRateApiClient(self.config)
        }

    def run_update(self, source: Optional[str] = None) -> Dict:
        """
        Выполняет обновление курсов валют.

        Args:
            source: Источник для обновления ('coingecko', 'exchangerate' или None для всех)

        Returns:
            Словарь с результатами обновления
        """
        logger.info(f"Начинаем обновление курсов (источник: {source or 'все'})")

        all_rates = {}
        results = {
            'success': True,
            'sources_updated': [],
            'rates_count': 0,
            'errors': []
        }

        # Определяем какие источники обновлять
        sources_to_update = []
        if source is None:
            sources_to_update = list(self.clients.keys())
        elif source in self.clients:
            sources_to_update = [source]
        else:
            raise ValueError(f"Неизвестный источник: {source}")

        # Обновляем курсы из каждого источника
        for source_name in sources_to_update:
            try:
                logger.info(f"Получаем курсы из {source_name}...")
                client = self.clients[source_name]
                rates = client.fetch_rates()

                all_rates.update(rates)
                results['sources_updated'].append(source_name)
                results['rates_count'] += len(rates)

                logger.info(f"Успешно получено {len(rates)} курсов от {source_name}")

            except ApiRequestError as e:
                logger.error(f"Ошибка при получении курсов от {source_name}: {e}")
                results['errors'].append({
                    'source': source_name,
                    'error': str(e)
                })
                results['success'] = False
            except Exception as e:
                logger.exception(f"Неожиданная ошибка при работе с {source_name}")
                results['errors'].append({
                    'source': source_name,
                    'error': f"Неожиданная ошибка: {str(e)}"
                })
                results['success'] = False

        # Если получили какие-то курсы, сохраняем их
        if all_rates:
            self._save_rates(all_rates)
            self._save_to_history(all_rates, sources_to_update)

        results['total_rates'] = len(all_rates)
        results['timestamp'] = datetime.now().isoformat()

        logger.info(f"Обновление завершено. Получено курсов: {len(all_rates)}")

        return results

    def _save_rates(self, rates: Dict[str, float]):
        """
        Сохраняет текущие курсы в файл rates.json.

        Args:
            rates: Словарь с курсами валют
        """
        now = datetime.now().isoformat()

        # Формируем структуру для сохранения
        rates_data = {
            "pairs": {},
            "last_refresh": now,
            "sources": list(set(key.split('_')[0] for key in rates.keys()))
        }

        # Добавляем информацию о каждой паре
        for pair_key, rate in rates.items():
            from_currency, to_currency = pair_key.split('_')

            rates_data["pairs"][pair_key] = {
                "rate": rate,
                "updated_at": now,
                "source": from_currency if from_currency in self.config.CRYPTO_CURRENCIES else "ExchangeRate-API"
            }

        # Сохраняем в базу данных
        self.db.save_rates(rates_data)

        logger.debug(f"Сохранено {len(rates)} курсов в rates.json")

    def _save_to_history(self, rates: Dict[str, float], sources: List[str]):
        """
        Сохраняет курсы в историю.

        Args:
            rates: Словарь с курсами валют
            sources: Список источников
        """
        now = datetime.now()

        for pair_key, rate in rates.items():
            from_currency, to_currency = pair_key.split('_')

            # Определяем источник
            if from_currency in self.config.CRYPTO_CURRENCIES:
                source = "CoinGecko"
            else:
                source = "ExchangeRate-API"

            # Создаем запись для истории
            record = {
                "id": f"{pair_key}_{now.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "timestamp": now.isoformat(),
                "source": source,
                "meta": {
                    "sources": sources,
                    "pair": pair_key
                }
            }

            # Добавляем запись в историю
            self.db.add_exchange_rate_record(record)

        logger.debug(f"Добавлено {len(rates)} записей в историю")

    def get_update_status(self) -> Dict:
        """
        Возвращает статус последнего обновления.

        Returns:
            Словарь со статусом обновления
        """
        try:
            rates_data = self.db.load_rates()
            last_refresh = rates_data.get("last_refresh")

            return {
                "last_refresh": last_refresh,
                "rates_count": len(rates_data.get("pairs", {})),
                "file_exists": True
            }
        except (FileNotFoundError, KeyError):
            return {
                "last_refresh": None,
                "rates_count": 0,
                "file_exists": False
            }