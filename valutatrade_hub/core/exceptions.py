"""
Пользовательские исключения для приложения.
"""


class InsufficientFundsError(Exception):
    """Исключение при недостатке средств."""
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        super().__init__(
            f"Недостаточно средств: доступно {available} {code}, требуется {required} {code}"
        )


class CurrencyNotFoundError(Exception):
    """Исключение при неизвестной валюте."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(Exception):
    """Исключение при ошибке запроса к API."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")


class UserNotFoundError(Exception):
    """Исключение при отсутствии пользователя."""
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Пользователь '{username}' не найден")


class AuthenticationError(Exception):
    """Исключение при ошибке аутентификации."""
    def __init__(self, message: str = "Неверный пароль"):
        super().__init__(message)


class ValidationError(Exception):
    """Исключение при ошибке валидации."""
    def __init__(self, message: str):
        super().__init__(message)