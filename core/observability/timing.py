import logging
import time
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

logger = logging.getLogger("observability")

correlation_id_var: ContextVar[str | None] = ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()


def set_correlation_id(cid: str) -> None:
    correlation_id_var.set(cid)


@contextmanager
def time_block(name: str, **extra):
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        data = {
            "type": "timing_block",
            "name": name,
            "duration_ms": round(duration_ms, 2),
            "correlation_id": get_correlation_id(),
            **extra,
        }
        logger.info("perf", extra=data)


def timeit(name: str = None):
    def decorator(func):
        block_name = name or f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            with time_block(block_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
