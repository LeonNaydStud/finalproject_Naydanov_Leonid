from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Dict


# =========================
# USER
# =========================

class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    # -------- getters --------

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    # -------- setters --------

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    # -------- password logic --------

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        return self._hashed_password == self._hash_password(password, self._salt)

    def change_password(self, new_password: str):
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        new_salt = os.urandom(8).hex()
        new_hash = self._hash_password(new_password, new_salt)

        self._salt = new_salt
        self._hashed_password = new_hash

    def get_user_info(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }


# =========================
# WALLET
# =========================

class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        if not currency_code or not currency_code.isupper():
            raise ValueError("Некорректный код валюты")

        self.currency_code = currency_code
        self._balance = 0.0
        self.balance = balance  # через сеттер

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float):
        self._validate_amount(amount)
        self._balance += amount

    def withdraw(self, amount: float):
        self._validate_amount(amount)
        if amount > self._balance:
            raise ValueError("Недостаточно средств")
        self._balance -= amount

    def get_balance_info(self) -> dict:
        return {
            "currency": self.currency_code,
            "balance": round(self._balance, 8),
        }

    @staticmethod
    def _validate_amount(amount: float):
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")


# =========================
# PORTFOLIO
# =========================

class Portfolio:
    def __init__(self, user_id: int, wallets: Dict[str, Wallet] | None = None):
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = wallets or {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return dict(self._wallets)

    def add_currency(self, currency_code: str):
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк {currency_code} уже существует")

        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Wallet:
        currency_code = currency_code.upper()
        if currency_code not in self._wallets:
            raise ValueError(f"Кошелёк {currency_code} не найден")
        return self._wallets[currency_code]

    def get_total_value(self, exchange_rates: dict, base_currency: str = "USD") -> float:
        total = 0.0
        base_currency = base_currency.upper()

        for wallet in self._wallets.values():
            if wallet.currency_code == base_currency:
                total += wallet.balance
                continue

            key = f"{wallet.currency_code}_{base_currency}"
            if key not in exchange_rates:
                raise ValueError(f"Нет курса для {wallet.currency_code}→{base_currency}")

            total += wallet.balance * exchange_rates[key]

        return round(total, 2)
