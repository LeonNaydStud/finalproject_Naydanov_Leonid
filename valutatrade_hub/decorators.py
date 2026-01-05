from functools import wraps
from .logging_config import logger

def log_action(action_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.info(f"{action_name} args={args} kwargs={kwargs} result=OK")
                return result
            except Exception as e:
                logger.error(f"{action_name} args={args} kwargs={kwargs} error={e}")
                raise
        return wrapper
    return decorator
