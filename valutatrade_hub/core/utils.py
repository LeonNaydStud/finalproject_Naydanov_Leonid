from .currencies import get_currency
from .exceptions import CurrencyNotFoundError

def validate_currency_code(code: str):
    try:
        get_currency(code)
    except CurrencyNotFoundError:
        raise

def convert_amount(amount, from_code, to_code, rates):
    key = f"{from_code}_{to_code}"
    rate = rates.get(key)
    if rate is None:
        raise ValueError(f"Нет курса для {from_code}->{to_code}")
    return amount * rate
