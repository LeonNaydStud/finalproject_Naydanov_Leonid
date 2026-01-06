"""
Бизнес-логика приложения.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Tuple
from pathlib import Path

from ..infra.database import DatabaseManager
from ..infra.settings import SettingsLoader
from ..decorators import log_action
from ..core.exceptions import (
    InsufficientFundsError, CurrencyNotFoundError, 
    UserNotFoundError, AuthenticationError, ValidationError
)
from ..core.models import User, Portfolio
from ..core.currencies import get_currency
from ..core.utils import (
    validate_currency_code, validate_amount,
    validate_username, convert_currency, is_rate_fresh
)

logger = logging.getLogger(__name__)


class UserUseCases:
    """Кейсы использования для работы с пользователями."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db = db_manager

    @log_action("REGISTER", verbose=True)
    def register_user(self, username: str, password: str) -> Tuple[User, Portfolio]:
        """
        Регистрирует нового пользователя.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Кортеж (User, Portfolio)

        Raises:
            ValidationError: Если данные невалидны
        """
        username = validate_username(username)

        if len(password) < 4:
            raise ValidationError("Пароль должен быть не короче 4 символов")

        # Проверяем уникальность username
        users = self.db.load_users()
        for user_data in users:
            if user_data["username"] == username:
                raise ValidationError(f"Имя пользователя '{username}' уже занято")

        # Создаем нового пользователя
        new_user = User.create_user(username, password)

        # Генерируем user_id
        if users:
            new_user_id = max(u["user_id"] for u in users) + 1
        else:
            new_user_id = 1

        # Обновляем ID и сохраняем
        user_dict = new_user.to_dict()
        user_dict["user_id"] = new_user_id
        users.append(user_dict)
        self.db.save_users(users)

        # Создаем портфель для пользователя
        portfolio = Portfolio(user_id=new_user_id)
        portfolio.add_currency("USD")  # Создаем USD кошелек по умолчанию
        self.db.save_portfolio(portfolio.to_dict())

        # Возвращаем объекты
        final_user = User.from_dict(user_dict)
        return final_user, portfolio

    @log_action("LOGIN", verbose=True)
    def login_user(self, username: str, password: str) -> User:
        """
        Аутентифицирует пользователя.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Объект User

        Raises:
            UserNotFoundError: Если пользователь не найден
            AuthenticationError: Если пароль неверный
        """
        users = self.db.load_users()

        # Ищем пользователя
        user_data = None
        for u in users:
            if u["username"] == username:
                user_data = u
                break

        if not user_data:
            raise UserNotFoundError(username)

        # Проверяем пароль
        user = User.from_dict(user_data)
        if not user.verify_password(password):
            raise AuthenticationError()

        return user

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Изменяет пароль пользователя.

        Args:
            user_id: ID пользователя
            old_password: Старый пароль
            new_password: Новый пароль

        Returns:
            True если успешно

        Raises:
            AuthenticationError: Если старый пароль неверный
            ValidationError: Если новый пароль невалидный
        """
        users = self.db.load_users()

        # Находим пользователя
        user_index = -1
        user_data = None
        for i, u in enumerate(users):
            if u["user_id"] == user_id:
                user_index = i
                user_data = u
                break

        if user_index == -1:
            raise UserNotFoundError(f"ID: {user_id}")

        # Проверяем старый пароль
        user = User.from_dict(user_data)
        if not user.verify_password(old_password):
            raise AuthenticationError("Неверный старый пароль")

        # Меняем пароль
        user.change_password(new_password)

        # Сохраняем изменения
        users[user_index] = user.to_dict()
        self.db.save_users(users)

        return True


class PortfolioUseCases:
    """Кейсы использования для работы с портфелем."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Инициализация.

        Args:
            db_manager: Менеджер базы данных
        """
        self.db = db_manager
        self.settings = SettingsLoader()

    def get_portfolio(self, user_id: int) -> Portfolio:
        """
        Получает портфель пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Объект Portfolio

        Raises:
            UserNotFoundError: Если портфель не найден
        """
        portfolios = self.db.load_portfolios()

        for portfolio_data in portfolios:
            if portfolio_data["user_id"] == user_id:
                return Portfolio.from_dict(portfolio_data)

        # Если портфель не найден, создаем новый
        portfolio = Portfolio(user_id=user_id)
        portfolio.add_currency("USD")  # Создаем USD кошелек по умолчанию
        self.db.save_portfolio(portfolio.to_dict())

        return portfolio

    def show_portfolio(self, user_id: int, base_currency: str = "USD") -> Dict:
        """
        Показывает портфель пользователя.

        Args:
            user_id: ID пользователя
            base_currency: Базовая валюта для расчета стоимости

        Returns:
            Словарь с информацией о портфеле
        """
        portfolio = self.get_portfolio(user_id)

        # Получаем текущие курсы
        exchange_rates = self.get_exchange_rates()

        # Рассчитываем стоимость каждого кошелька
        wallets_info = []
        for wallet in portfolio.wallets.values():
            try:
                # Получаем информацию о валюте
                currency = get_currency(wallet.currency_code)
                currency_info = currency.get_display_info()
            except CurrencyNotFoundError:
                currency_info = f"Неизвестная валюта: {wallet.currency_code}"

            # Рассчитываем стоимость в базовой валюте
            if wallet.currency_code == base_currency:
                value_in_base = wallet.balance
            else:
                try:
                    value_in_base = convert_currency(
                        wallet.balance,
                        wallet.currency_code,
                        base_currency,
                        exchange_rates.get("pairs", {})
                    )
                except (KeyError, ValidationError):
                    value_in_base = 0.0

            wallets_info.append({
                "currency_code": wallet.currency_code,
                "balance": wallet.balance,
                "value_in_base": value_in_base,
                "currency_info": currency_info
            })

        # Рассчитываем общую стоимость
        total_value = portfolio.get_total_value(base_currency, exchange_rates.get("pairs", {}))

        # Получаем информацию о пользователе
        users = self.db.load_users()
        username = next((u["username"] for u in users if u["user_id"] == user_id), "Неизвестный")

        return {
            "username": username,
            "user_id": user_id,
            "base_currency": base_currency,
            "wallets": wallets_info,
            "total_value": total_value,
            "rates_updated_at": exchange_rates.get("last_refresh", "Неизвестно")
        }

    @log_action("BUY", verbose=True)
    def buy_currency(self, user_id: int, currency_code: str, amount: float) -> Dict:
        """
        Покупает валюту.

        Args:
            user_id: ID пользователя
            currency_code: Код покупаемой валюты
            amount: Количество покупаемой валюты

        Returns:
            Словарь с результатом операции

        Raises:
            ValidationError: Если данные невалидны
            InsufficientFundsError: Если недостаточно USD для покупки
        """
        # Валидация входа
        currency_code = validate_currency_code(currency_code)
        amount = validate_amount(amount)

        # Получаем портфель
        portfolio = self.get_portfolio(user_id)

        # Получаем курс
        exchange_rates = self.get_exchange_rates()
        pairs = exchange_rates.get("pairs", {})

        # Рассчитываем стоимость в USD
        rate_key = f"{currency_code}_USD"
        if rate_key not in pairs:
            raise ValidationError(f"Не удалось получить курс для {currency_code}→USD")

        rate = pairs[rate_key]["rate"]
        cost_usd = amount * rate

        # Проверяем наличие USD кошелька и средств
        usd_wallet = portfolio.get_wallet("USD")
        if not usd_wallet:
            raise ValidationError("У вас нет USD кошелька. Сначала создайте его.")

        if usd_wallet.balance < cost_usd:
            raise InsufficientFundsError(usd_wallet.balance, cost_usd, "USD")

        # Выполняем операцию
        usd_wallet.withdraw(cost_usd)

        # Добавляем или получаем кошелек для покупаемой валюты
        target_wallet = portfolio.add_currency(currency_code)
        old_balance = target_wallet.balance
        target_wallet.deposit(amount)

        # Сохраняем изменения
        self.save_portfolio(portfolio)

        # Записываем транзакцию
        self.record_transaction(
            user_id=user_id,
            action="BUY",
            from_currency="USD",
            to_currency=currency_code,
            amount=amount,
            rate=rate,
            total_cost=cost_usd
        )

        return {
            "success": True,
            "message": f"Покупка выполнена: {amount:.4f} {currency_code} по курсу {rate:.2f} USD/{currency_code}",
            "details": {
                "currency": currency_code,
                "amount": amount,
                "rate": rate,
                "cost_usd": cost_usd,
                "old_balance": old_balance,
                "new_balance": target_wallet.balance,
                "usd_balance_after": usd_wallet.balance
            }
        }

    @log_action("SELL", verbose=True)
    def sell_currency(self, user_id: int, currency_code: str, amount: float) -> Dict:
        """
        Продает валюту.

        Args:
            user_id: ID пользователя
            currency_code: Код продаваемой валюты
            amount: Количество продаваемой валюты

        Returns:
            Словарь с результатом операции

        Raises:
            ValidationError: Если данные невалидны
            InsufficientFundsError: Если недостаточно валюты для продажи
        """
        # Валидация входа
        currency_code = validate_currency_code(currency_code)
        amount = validate_amount(amount)

        # Получаем портфель
        portfolio = self.get_portfolio(user_id)

        # Проверяем наличие кошелька и средств
        wallet = portfolio.get_wallet(currency_code)
        if not wallet:
            raise ValidationError(f"У вас нет кошелька '{currency_code}'")

        if wallet.balance < amount:
            raise InsufficientFundsError(wallet.balance, amount, currency_code)

        # Получаем курс
        exchange_rates = self.get_exchange_rates()
        pairs = exchange_rates.get("pairs", {})

        # Рассчитываем выручку в USD
        rate_key = f"{currency_code}_USD"
        if rate_key not in pairs:
            raise ValidationError(f"Не удалось получить курс для {currency_code}→USD")

        rate = pairs[rate_key]["rate"]
        revenue_usd = amount * rate

        # Выполняем операцию
        old_balance = wallet.balance
        wallet.withdraw(amount)

        # Начисляем USD
        usd_wallet = portfolio.add_currency("USD")
        usd_old_balance = usd_wallet.balance
        usd_wallet.deposit(revenue_usd)

        # Сохраняем изменения
        self.save_portfolio(portfolio)

        # Записываем транзакцию
        self.record_transaction(
            user_id=user_id,
            action="SELL",
            from_currency=currency_code,
            to_currency="USD",
            amount=amount,
            rate=rate,
            total_revenue=revenue_usd
        )

        return {
            "success": True,
            "message": f"Продажа выполнена: {amount:.4f} {currency_code} по курсу {rate:.2f} USD/{currency_code}",
            "details": {
                "currency": currency_code,
                "amount": amount,
                "rate": rate,
                "revenue_usd": revenue_usd,
                "old_balance": old_balance,
                "new_balance": wallet.balance,
                "usd_old_balance": usd_old_balance,
                "usd_new_balance": usd_wallet.balance
            }
        }

    def get_exchange_rates(self) -> Dict:
        """
        Получает текущие курсы валют.

        Returns:
            Словарь с курсами валют
        """
        try:
            rates_data = self.db.load_rates()

            # Проверяем свежесть данных
            last_refresh = rates_data.get("last_refresh")
            ttl_seconds = self.settings.get("rates_ttl_seconds", 300)

            if last_refresh and is_rate_fresh(last_refresh, ttl_seconds):
                return rates_data

            # Данные устарели, пытаемся обновить
            logger.warning("Курсы валют устарели, требуется обновление")

            # Здесь можно вызвать парсер для обновления курсов
            # Для простоты возвращаем устаревшие данные
            return rates_data

        except (FileNotFoundError, json.JSONDecodeError):
            # Файл не существует или поврежден
            logger.error("Не удалось загрузить курсы валют")
            return {"pairs": {}, "last_refresh": None}

    def get_rate(self, from_currency: str, to_currency: str) -> Dict:
        """
        Получает курс между двумя валютами.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта

        Returns:
            Словарь с информацией о курсе
        """
        # Валидация валют
        from_currency = validate_currency_code(from_currency)
        to_currency = validate_currency_code(to_currency)

        # Получаем курсы
        exchange_rates = self.get_exchange_rates()
        pairs = exchange_rates.get("pairs", {})

        # Пытаемся найти прямой курс
        rate_key = f"{from_currency}_{to_currency}"
        if rate_key in pairs:
            rate_info = pairs[rate_key]
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate_info["rate"],
                "updated_at": rate_info["updated_at"],
                "source": rate_info["source"],
                "is_direct": True
            }

        # Пытаемся найти обратный курс
        reverse_key = f"{to_currency}_{from_currency}"
        if reverse_key in pairs:
            rate_info = pairs[reverse_key]
            return {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": 1 / rate_info["rate"],
                "updated_at": rate_info["updated_at"],
                "source": rate_info["source"],
                "is_direct": False
            }

        # Курс не найден
        raise ValidationError(
            f"Не удалось найти курс для конвертации {from_currency} → {to_currency}"
        )

    def save_portfolio(self, portfolio: Portfolio):
        """
        Сохраняет портфель.

        Args:
            portfolio: Объект Portfolio
        """
        portfolios = self.db.load_portfolios()

        # Ищем существующий портфель
        found = False
        for i, p in enumerate(portfolios):
            if p["user_id"] == portfolio.user_id:
                portfolios[i] = portfolio.to_dict()
                found = True
                break

        # Если не найден, добавляем новый
        if not found:
            portfolios.append(portfolio.to_dict())

        self.db.save_portfolios(portfolios)

    def record_transaction(self, user_id: int, action: str, from_currency: str,
                          to_currency: str, amount: float, rate: float,
                          total_cost: float = None, total_revenue: float = None):
        """
        Записывает транзакцию в историю.

        Args:
            user_id: ID пользователя
            action: Действие (BUY/SELL)
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            amount: Количество
            rate: Курс обмена
            total_cost: Общая стоимость (для покупки)
            total_revenue: Общая выручка (для продажи)
        """
        transaction = {
            "user_id": user_id,
            "action": action,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "rate": rate,
            "timestamp": datetime.now().isoformat(),
            "total_cost": total_cost,
            "total_revenue": total_revenue
        }

        # Загружаем существующие транзакции
        try:
            transactions_path = Path(self.settings.get("data_path", "data")) / "transactions.json"
            if transactions_path.exists():
                with open(transactions_path, 'r', encoding='utf-8') as f:
                    transactions = json.load(f)
            else:
                transactions = []
        except (FileNotFoundError, json.JSONDecodeError):
            transactions = []

        # Добавляем новую транзакцию
        transactions.append(transaction)

        # Сохраняем
        try:
            with open(transactions_path, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Ошибка при сохранении транзакции: {e}")