class InsufficientFundsError(Exception):
    def __init__(self, available, required, code):
        super().__init__(f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}")

class CurrencyNotFoundError(Exception):
    def __init__(self, code):
        super().__init__(f"Неизвестная валюта '{code}'")

class ApiRequestError(Exception):
    def __init__(self, reason):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
