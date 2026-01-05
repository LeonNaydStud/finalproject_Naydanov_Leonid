import json
import os
from datetime import datetime
from typing import Dict, List

from valutatrade_hub.core.models import User, Wallet, Portfolio


# =========================
# PATHS
# =========================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DATA_DIR = os.path.join(BASE_DIR, "data")

USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")


# =========================
# HELPERS
# =========================

def _ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(USERS_FILE):
        _write_json(USERS_FILE, [])

    if not os.path.exists(PORTFOLIOS_FILE):
        _write_json(PORTFOLIOS_FILE, [])

    if not os.path.exists(RATES_FILE):
        _write_json(RATES_FILE, {})


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =========================
# USERS
# =========================

def load_users() -> List[User]:
    _ensure_data_files()
    raw_users = _read_json(USERS_FILE)

    users = []
    for u in raw_users:
        users.append(
            User(
                user_id=u["user_id"],
                username=u["username"],
                hashed_password=u["hashed_password"],
                salt=u["salt"],
                registration_date=datetime.fromisoformat(u["registration_date"]),
            )
        )
    return users


def save_users(users: List[User]):
    data = []
    for u in users:
        data.append(
            {
                "user_id": u.user_id,
                "username": u.username,
                "hashed_password": u._hashed_password,
                "salt": u._salt,
                "registration_date": u.registration_date.isoformat(),
            }
        )
    _write_json(USERS_FILE, data)


def get_next_user_id(users: List[User]) -> int:
    if not users:
        return 1
    return max(u.user_id for u in users) + 1


def find_user_by_username(username: str) -> User | None:
    for user in load_users():
        if user.username == username:
            return user
    return None


# =========================
# PORTFOLIOS
# =========================

def load_portfolios() -> Dict[int, Portfolio]:
    _ensure_data_files()
    raw = _read_json(PORTFOLIOS_FILE)

    portfolios: Dict[int, Portfolio] = {}

    for item in raw:
        user_id = item["user_id"]
        wallets = {}

        for code, w in item["wallets"].items():
            wallets[code] = Wallet(code, w["balance"])

        portfolios[user_id] = Portfolio(user_id, wallets)

    return portfolios


def save_portfolios(portfolios: Dict[int, Portfolio]):
    data = []

    for user_id, portfolio in portfolios.items():
        wallets = {}
        for code, wallet in portfolio.wallets.items():
            wallets[code] = {"balance": wallet.balance}

        data.append(
            {
                "user_id": user_id,
                "wallets": wallets,
            }
        )

    _write_json(PORTFOLIOS_FILE, data)


def get_or_create_portfolio(user_id: int) -> Portfolio:
    portfolios = load_portfolios()

    if user_id not in portfolios:
        portfolios[user_id] = Portfolio(user_id)
        save_portfolios(portfolios)

    return portfolios[user_id]


# =========================
# RATES
# =========================

def load_rates() -> dict:
    _ensure_data_files()
    return _read_json(RATES_FILE)


def save_rates(rates: dict):
    _write_json(RATES_FILE, rates)


# =========================
# FAKE EXCHANGE RATES (STUB)
# =========================

def get_stub_exchange_rates() -> dict:
    return {
        "BTC_USD": 59337.21,
        "ETH_USD": 3720.00,
        "EUR_USD": 1.07,
        "RUB_USD": 0.010,
    }
