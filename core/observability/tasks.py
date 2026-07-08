import logging
import time
import uuid
from functools import wraps

from zappa.asynchronous import task

from core.observability.db import QueryTracker
from core.observability.timing import set_correlation_id

logger = logging.getLogger("observability")

# Cold start detection for task invocations
_task_cold_start = True


def tracked_task(func):
    @task
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _task_cold_start

        correlation_id = uuid.uuid4().hex[:8]
        set_correlation_id(correlation_id)

        cold_start = _task_cold_start
        if _task_cold_start:
            _task_cold_start = False

        start = time.perf_counter()
        success = True
        error_msg = None

        try:
            with QueryTracker(slow_threshold_ms=500) as tracker:
                result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            error_msg = f"{type(e).__name__}: {str(e)[:200]}"
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            data = {
                "type": "task",
                "task_name": f"{func.__module__}.{func.__qualname__}",
                "correlation_id": correlation_id,
                "duration_ms": round(duration_ms, 2),
                "db_queries": tracker.count if "tracker" in dir() else 0,
                "db_time_ms": (
                    round(tracker.total_ms, 2) if "tracker" in dir() else 0
                ),
                "cold_start": cold_start,
                "success": success,
                "error": error_msg,
            }

            if duration_ms >= 2000 or not success:
                logger.warning("perf", extra=data)
            else:
                logger.info("perf", extra=data)

            # Log slow queries
            if "tracker" in dir():
                tracker.log_slow_queries(correlation_id=correlation_id)

    return wrapper
