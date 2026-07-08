"""
Database query tracking for performance observability.

Uses Django's execute_wrapper hook (official API) to intercept
queries without requiring DEBUG=True. This is production-safe
and has minimal overhead.
"""

import logging
import time

logger = logging.getLogger("observability")


class QueryTracker:
    """
    Context manager that tracks SQL queries executed within its scope.

    Usage:
        from core.observability.db import QueryTracker

        with QueryTracker() as tracker:
            # ... your ORM code ...
            pass

        print(tracker.count)       # number of queries
        print(tracker.total_ms)    # total DB time in ms
        print(tracker.slow_queries)  # queries above threshold
    """

    def __init__(self, slow_threshold_ms: float = 500):
        self.slow_threshold_ms = slow_threshold_ms
        self.count = 0
        self.total_ms = 0.0
        self.slow_queries: list[dict] = []

    def __enter__(self):
        from django.db import connection

        self._connection = connection
        self._wrapper = self._make_wrapper()
        connection.execute_wrappers.append(self._wrapper)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connection.execute_wrappers.remove(self._wrapper)
        return False

    def _make_wrapper(self):
        tracker = self

        def wrapper(execute, sql, params, many, context):
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                tracker.count += 1
                tracker.total_ms += duration_ms

                if duration_ms >= tracker.slow_threshold_ms:
                    slow_entry = {
                        "sql": str(sql)[:500],
                        "duration_ms": round(duration_ms, 2),
                    }
                    tracker.slow_queries.append(slow_entry)

        return wrapper

    def log_slow_queries(self, correlation_id: str = None):
        """Log any slow queries detected during tracking."""
        for sq in self.slow_queries:
            data = {
                "type": "slow_query",
                "correlation_id": correlation_id,
                **sq,
            }
            logger.warning("perf", extra=data)
