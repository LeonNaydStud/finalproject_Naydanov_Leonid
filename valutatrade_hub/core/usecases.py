from datetime import datetime
import os
import hashlib

from valutatrade_hub.core.models import User
from valutatrade_hub.core.utils import (
    load_users,
    save_users,
    get_next_user_id,
    find_user_by_username,
    load_portfolios,
    save_portfolios,
    get_or_create_portfolio,
    get_stub_exchange_rates,
)

# =========================
# SESSION (простая in-memory)
# =========================

_current_user: User | None = None


def get_current_user() -> User | None:
    return _current_user


def require_login():
    if _current_user is None:
        raise PermissionError("Сначала выполните login")


# =========================
# AUTH
# =========================

def register_user(username: str, password: str) -> str:
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    if find_user_by_username(username):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    users = load_users()
    user_id = get_next_user_id(users)

    salt = os.urandom(8).hex()
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()

    user = User(
        user_id=user_id,
        username=username,
        hashed_password=hashed_password,
        salt=salt,
        registration_date=datetime.now(),
    )

    users.append(user)
    save_users(users)

    portfolios = load_portfolios()
    portfolios[user_id] = get_or_create_portfolio(user_id)
    save_portfolios(portfolios)

    return f"Пользователь '{username}' зарегистрирован (id={user_id})."


def login_user(username: str, password: str) -> str:
    global _current_user

    user = find_user_by_username(username)
    if not user:
        raise ValueError(f"Пользователь '{username}' не найден")

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    _current_user = user
    return f"Вы вошли как '{username}'"


def logout_user() -> str:
    global _current_user
    _current_user = None
    return "Вы вышли из системы"


# =========================
# PORTFOLIO
# =========================

def show_portfolio(base_currency: str = "USD") -> dict:
    require_login()
    base_currency = base_currency.upper()

    portfolio = get_or_create_portfolio(_current_user.user_id)
    wallets = portfolio.wallets

    if not wallets:
        return {
            "username": _current_user.username,
            "base": base_currency,
            "wallets": [],
            "total": 0.0,
        }

    exchange_rates = get_stub_exchange_rates()
    rows = []

    total = 0.0
    for wallet in wallets.values():
        if wallet.currency_code == base_currency:
            value = wallet.balance
        else:
            key = f"{wallet.currency_code}_{base_currency}"
            if key not in exchange_rates:
                raise ValueError(f"Неизвестная валюта '{wallet.currency_code}'")
            value = wallet.balance * exchange_rates[key]

        rows.append(
            {
                "currency": wallet.currency_code,
                "balance": wallet.balance,
                "value": round(value, 2),
            }
        )
        total += value

    return {
        "username": _current_user.username,
        "base": base_currency,
        "wallets": rows,
        "total": round(total, 2),
    }


# =========================
# BUY / SELL
# =========================

def buy_currency(currency: str, amount: float) -> dict:
    require_login()

    currency = currency.upper()
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    portfolio = get_or_create_portfolio(_current_user.user_id)

    try:
        wallet = portfolio.get_wallet(currency)
        before = wallet.balance
    except ValueError:
        portfolio.add_currency(currency)
        wallet = portfolio.get_wallet(currency)
        before = 0.0

    wallet.deposit(amount)

    portfolios = load_portfolios()
    portfolios[_current_user.user_id] = portfolio
    save_portfolios(portfolios)

    rates = get_stub_exchange_rates()
    rate_key = f"{currency}_USD"

    rate = rates.get(rate_key)
    cost = round(amount * rate, 2) if rate else None

    return {
        "currency": currency,
        "before": before,
        "after": wallet.balance,
        "rate": rate,
        "cost": cost,
    }


def sell_currency(currency: str, amount: float) -> dict:
    require_login()

    currency = currency.upper()
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    portfolio = get_or_create_portfolio(_current_user.user_id)
    wallet = portfolio.get_wallet(currency)

    before = wallet.balance
    wallet.withdraw(amount)

    portfolios = load_portfolios()
    portfolios[_current_user.user_id] = portfolio
    save_portfolios(portfolios)

    rates = get_stub_exchange_rates()
    rate_key = f"{currency}_USD"
    rate = rates.get(rate_key)
    revenue = round(amount * rate, 2) if rate else None

    return {
        "currency": currency,
        "before": before,
        "after": wallet.balance,
        "rate": rate,
        "revenue": revenue,
    }


# =========================
# RATES
# =========================

def get_rate(from_currency: str, to_currency: str) -> dict:
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    rates = get_stub_exchange_rates()

    key = f"{from_currency}_{to_currency}"
    reverse_key = f"{to_currency}_{from_currency}"

    if key in rates:
        rate = rates[key]
        reverse = round(1 / rate, 8)
    elif reverse_key in rates:
        reverse = rates[reverse_key]
        rate = round(1 / reverse, 8)
    else:
        raise ValueError(f"Курс {from_currency}→{to_currency} недоступен")

    return {
        "from": from_currency,
        "to": to_currency,
        "rate": rate,
        "reverse": reverse,
    }
