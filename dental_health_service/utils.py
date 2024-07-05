import time
import logging
from functools import wraps

logger = logging.getLogger()


def timelog(func):
    """Decorator for recording function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            logger.info(f'[Phase: {func.__name__}] ------------- START')
            return func(*args, **kwargs)
        finally:
            elapsed_time = time.time() - start_time
            logger.info(f"[Phase: {func.__name__}] ------------- END in {elapsed_time:.3f}(s)")
    return wrapper
