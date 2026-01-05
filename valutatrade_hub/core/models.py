import hashlib
from datetime import datetime
from .exceptions import InsufficientFundsError

class User:
    def __init__(self, user_id, username, hashed_password, salt, registration_date):
        self._user_id = user_id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self):
        return self._user_id

    def get_user_info(self):
        return {
            "user_id": self._user_id,
            "username": self.username,
            "registration_date": self._registration_date
        }

    def verify_password(self, password: str):
        return self._hashed_password == hashlib.sha256((password + self._salt).encode()).hexdigest()

    def change_password(self, new_password: str):
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = hashlib.sha256((new_password + self._salt).encode()).hexdigest()

class Wallet:
    def __init__(self, currency_code, balance=0.0):
        self.currency_code = currency_code
        self._balance = float(balance)

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Некорректное значение баланса")
        self._balance = value

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        self._balance += amount

    def withdraw(self, amount):
        if amount > self._balance:
            raise InsufficientFundsError(self._balance, amount, self.currency_code)
        self._balance -= amount

    def get_balance_info(self):
        return {"currency_code": self.currency_code, "balance": self._balance}

class Portfolio:
    def __init__(self, user_id, wallets=None):
        self._user_id = user_id
        self._wallets = wallets or {}

    def add_currency(self, currency_code):
        if currency_code in self._wallets:
            return
        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code):
        return self._wallets.get(currency_code)

    @property
    def wallets(self):
        return self._wallets.copy()

    @property
    def user(self):
        return self._user_id

    def get_total_value(self, exchange_rates, base_currency="USD"):
        total = 0.0
        for code, wallet in self._wallets.items():
            rate = exchange_rates.get(f"{code}_{base_currency}", 1.0)
            total += wallet.balance * rate
        return total
