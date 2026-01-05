import hashlib
from datetime import datetime
from ..infra.database import DatabaseManager
from ..core.models import User, Portfolio
from ..decorators import log_action
from .currencies import get_currency
from .exceptions import InsufficientFundsError, CurrencyNotFoundError

db = DatabaseManager()

@log_action("REGISTER")
def register(username, password):
    users = db.read_json(db.users_file)
    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")
    salt = "SALT"
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    user_id = max([u["user_id"] for u in users], default=0) + 1
    user = User(user_id, username, hashed, salt, datetime.now().isoformat())
    users.append({
        "user_id": user.user_id,
        "username": username,
        "hashed_password": hashed,
        "salt": salt,
        "registration_date": user._registration_date
    })
    db.write_json(db.users_file, users)

    portfolios = db.read_json(db.portfolios_file)
    portfolios.append({"user_id": user_id, "wallets": {}})
    db.write_json(db.portfolios_file, portfolios)
    return user

@log_action("LOGIN")
def login(username, password):
    users = db.read_json(db.users_file)
    u = next((x for x in users if x["username"] == username), None)
    if not u:
        raise ValueError(f"Пользователь '{username}' не найден")
    user = User(u["user_id"], u["username"], u["hashed_password"], u["salt"], u["registration_date"])
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")
    return user

@log_action("SHOW_PORTFOLIO")
def show_portfolio(user_id):
    portfolios = db.read_json(db.portfolios_file)
    portfolio_data = next((p for p in portfolios if p["user_id"] == user_id), None)
    if not portfolio_data:
        return {}
    return portfolio_data["wallets"]

@log_action("BUY")
def buy(user_id, currency_code, amount):
    portfolios = db.read_json(db.portfolios_file)
    p_data = next((p for p in portfolios if p["user_id"] == user_id), None)
    if not p_data:
        raise ValueError("Нет портфеля")
    wallets = p_data["wallets"]
    if currency_code not in wallets:
        wallets[currency_code] = {"currency_code": currency_code, "balance": 0.0}
    wallets[currency_code]["balance"] += amount
    db.write_json(db.portfolios_file, portfolios)

@log_action("SELL")
def sell(user_id, currency_code, amount):
    portfolios = db.read_json(db.portfolios_file)
    p_data = next((p for p in portfolios if p["user_id"] == user_id), None)
    if not p_data:
        raise ValueError("Нет портфеля")
    wallets = p_data["wallets"]
    if currency_code not in wallets or wallets[currency_code]["balance"] < amount:
        raise InsufficientFundsError(wallets.get(currency_code, {"balance": 0})["balance"], amount, currency_code)
    wallets[currency_code]["balance"] -= amount
    db.write_json(db.portfolios_file, portfolios)

@log_action("GET_RATE")
def get_rate(from_code, to_code):
    rates = db.read_json(db.rates_file)
    key = f"{from_code}_{to_code}"
    if key not in rates:
        raise CurrencyNotFoundError(key)
    return rates[key]["rate"], rates[key]["updated_at"]
