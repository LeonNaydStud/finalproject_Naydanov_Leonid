"""
Декораторы для логирования операций.
"""

import functools
import logging
import time
from typing import Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


def log_action(action: str, verbose: bool = False):
    """
    Декоратор для логирования действий пользователя.

    Args:
        action: Название действия (BUY, SELL, REGISTER, LOGIN)
        verbose: Подробное логирование с контекстом
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = "OK"
            error_info = None

            try:
                # Извлекаем информацию о пользователе из аргументов
                user_info = {}
                if 'user_id' in kwargs:
                    user_info['user_id'] = kwargs['user_id']
                if 'username' in kwargs:
                    user_info['username'] = kwargs['username']

                # Выполняем функцию
                return_value = func(*args, **kwargs)

                # Дополнительная информация для verbose режима
                context = {}
                if verbose:
                    if 'currency_code' in kwargs:
                        context['currency'] = kwargs['currency_code']
                    if 'amount' in kwargs:
                        context['amount'] = kwargs['amount']
                    if hasattr(return_value, '__dict__'):
                        context.update({k: v for k, v in return_value.__dict__.items()
                                        if not k.startswith('_')})

                # Логируем успешное выполнение
                log_message = {
                    'action': action,
                    'user_info': user_info,
                    'context': context if verbose else None,
                    'duration_ms': round((time.time() - start_time) * 1000, 2),
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }

                logger.info(f"{action} completed: {log_message}")

                return return_value

            except Exception as e:
                result = "ERROR"
                error_info = {
                    'type': type(e).__name__,
                    'message': str(e)
                }

                # Логируем ошибку
                log_message = {
                    'action': action,
                    'result': result,
                    'error': error_info,
                    'duration_ms': round((time.time() - start_time) * 1000, 2),
                    'timestamp': datetime.now().isoformat()
                }

                logger.error(f"{action} failed: {log_message}")
                raise

        return wrapper

    return decorator