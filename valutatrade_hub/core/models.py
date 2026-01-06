"""
Основные модели данных приложения.
"""

import hashlib
import secrets
from datetime import datetime
from typing import Dict, Optional
from ..core.exceptions import InsufficientFundsError, ValidationError


class User:
    """Класс пользователя системы."""

    def __init__(self, user_id: int, username: str, hashed_password: str,
                 salt: str, registration_date: datetime):
        """
        Инициализация пользователя.

        Args:
            user_id: Уникальный идентификатор пользователя
            username: Имя пользователя
            hashed_password: Хешированный пароль
            salt: Соль для хеширования
            registration_date: Дата регистрации
        """
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        """Возвращает ID пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Возвращает имя пользователя."""
        return self._username

    @username.setter
    def username(self, value: str):
        """Устанавливает имя пользователя."""
        if not value or not isinstance(value, str):
            raise ValidationError("Имя пользователя не может быть пустым")
        self._username = value

    @property
    def hashed_password(self) -> str:
        """Возвращает хешированный пароль."""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Возвращает соль для хеширования."""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Возвращает дату регистрации."""
        return self._registration_date

    def get_user_info(self) -> Dict:
        """Возвращает информацию о пользователе (без пароля)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date.isoformat()
        }

    def change_password(self, new_password: str):
        """
        Изменяет пароль пользователя.

        Args:
            new_password: Новый пароль

        Raises:
            ValidationError: Если пароль слишком короткий
        """
        if len(new_password) < 4:
            raise ValidationError("Пароль должен быть не короче 4 символов")

        # Генерация новой соли и хеширование пароля
        new_salt = secrets.token_hex(8)
        new_hashed_password = self._hash_password(new_password, new_salt)

        self._hashed_password = new_hashed_password
        self._salt = new_salt

    def verify_password(self, password: str) -> bool:
        """
        Проверяет пароль пользователя.

        Args:
            password: Пароль для проверки

        Returns:
            True если пароль верный, иначе False
        """
        hashed_password = self._hash_password(password, self.salt)
        return hashed_password == self.hashed_password

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """
        Хеширует пароль с солью.

        Args:
            password: Пароль
            salt: Соль

        Returns:
            Хешированный пароль
        """
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    @classmethod
    def create_user(cls, username: str, password: str) -> 'User':
        """
        Создает нового пользователя.

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            Новый объект User
        """
        if len(password) < 4:
            raise ValidationError("Пароль должен быть не короче 4 символов")

        # Генерация соли и хеширование пароля
        salt = secrets.token_hex(8)
        hashed_password = cls._hash_password(password, salt)

        return cls(
            user_id=0,  # Будет установлен при сохранении
            username=username,
            hashed_password=hashed_password,
            salt=salt,
            registration_date=datetime.now()
        )

    def to_dict(self) -> Dict:
        """Конвертирует пользователя в словарь для сохранения."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "hashed_password": self.hashed_password,
            "salt": self.salt,
            "registration_date": self.registration_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Создает пользователя из словаря."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"])
        )


class Wallet:
    """Класс кошелька для конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Инициализация кошелька.

        Args:
            currency_code: Код валюты
            balance: Начальный баланс
        """
        self._currency_code = currency_code.upper()
        self._balance = float(balance)

    @property
    def currency_code(self) -> str:
        """Возвращает код валюты."""
        return self._currency_code

    @property
    def balance(self) -> float:
        """Возвращает текущий баланс."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Устанавливает баланс."""
        value = float(value)
        if value < 0:
            raise ValidationError("Баланс не может быть отрицательным")
        self._balance = value

    def deposit(self, amount: float):
        """
        Пополняет баланс.

        Args:
            amount: Сумма для пополнения

        Raises:
            ValidationError: Если сумма не положительная
        """
        amount = float(amount)
        if amount <= 0:
            raise ValidationError("Сумма пополнения должна быть положительной")
        self.balance += amount

    def withdraw(self, amount: float):
        """
        Снимает средства с кошелька.

        Args:
            amount: Сумма для снятия

        Raises:
            ValidationError: Если сумма не положительная
            InsufficientFundsError: Если недостаточно средств
        """
        amount = float(amount)
        if amount <= 0:
            raise ValidationError("Сумма снятия должна быть положительной")

        if amount > self.balance:
            raise InsufficientFundsError(self.balance, amount, self.currency_code)

        self.balance -= amount

    def get_balance_info(self) -> Dict:
        """Возвращает информацию о балансе."""
        return {
            "currency_code": self.currency_code,
            "balance": self.balance
        }

    def to_dict(self) -> Dict:
        """Конвертирует кошелек в словарь для сохранения."""
        return {
            "currency_code": self.currency_code,
            "balance": self.balance
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Wallet':
        """Создает кошелек из словаря."""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )


class Portfolio:
    """Класс для управления всеми кошельками пользователя."""

    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        """
        Инициализация портфеля.

        Args:
            user_id: ID пользователя
            wallets: Словарь кошельков
        """
        self._user_id = user_id
        self._wallets = wallets or {}

    @property
    def user_id(self) -> int:
        """Возвращает ID пользователя."""
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавляет новую валюту в портфель.

        Args:
            currency_code: Код валюты

        Returns:
            Созданный или существующий кошелек

        Raises:
            ValidationError: Если код валюты некорректен
        """
        currency_code = currency_code.upper()

        if not currency_code:
            raise ValidationError("Код валюты не может быть пустым")

        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)

        return self._wallets[currency_code]

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """
        Возвращает кошелек по коду валюты.

        Args:
            currency_code: Код валюты

        Returns:
            Объект Wallet или None если не найден
        """
        return self._wallets.get(currency_code.upper())

    def get_total_value(self, base_currency: str = 'USD',
                        exchange_rates: Optional[Dict] = None) -> float:
        """
        Рассчитывает общую стоимость портфеля в базовой валюте.

        Args:
            base_currency: Код базовой валюты
            exchange_rates: Словарь курсов обмена

        Returns:
            Общая стоимость портфеля
        """
        if not exchange_rates:
            # Используем фиктивные курсы для демонстрации
            exchange_rates = {
                "USD_USD": 1.0,
                "EUR_USD": 1.0786,
                "BTC_USD": 59337.21,
                "ETH_USD": 3720.00,
                "GBP_USD": 1.2623,
                "RUB_USD": 0.01016,
            }

        total_value = 0.0

        for wallet in self._wallets.values():
            if wallet.currency_code == base_currency:
                total_value += wallet.balance
            else:
                rate_key = f"{wallet.currency_code}_{base_currency}"
                if rate_key in exchange_rates:
                    total_value += wallet.balance * exchange_rates[rate_key]
                else:
                    # Пробуем найти обратный курс
                    reverse_key = f"{base_currency}_{wallet.currency_code}"
                    if reverse_key in exchange_rates:
                        total_value += wallet.balance / exchange_rates[reverse_key]

        return total_value

    def to_dict(self) -> Dict:
        """Конвертирует портфель в словарь для сохранения."""
        return {
            "user_id": self.user_id,
            "wallets": {
                code: wallet.to_dict()
                for code, wallet in self._wallets.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Portfolio':
        """Создает портфель из словаря."""
        wallets = {}
        for code, wallet_data in data.get("wallets", {}).items():
            wallets[code] = Wallet.from_dict(wallet_data)

        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )