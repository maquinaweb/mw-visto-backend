"""
Performance middleware for Django/Zappa/Lambda.

Provides comprehensive per-request observability:
- Request duration
- DB query count and total time (N+1 detection)
- Slow query logging
- Cold start detection
- Response size
- Configurable sampling for production
"""

import logging
import random
import time
import uuid

from django.conf import settings

from core.observability.db import QueryTracker
from core.observability.timing import set_correlation_id

logger = logging.getLogger("observability")

# Cold start detection — True only on first invocation
_is_cold_start = True


class PerformanceMiddleware:
    """
    Middleware that collects and logs performance metrics for every
    request (subject to sampling).

    Emits JSON logs with type="request" containing:
        - correlation_id, method, path, view, status
        - duration_ms, db_queries, db_time_ms
        - response_bytes, cold_start, user_id

    Configure via settings:
        PERF_SAMPLE_RATE   — float 0.0-1.0 (default 1.0)
        PERF_SLOW_REQUEST_MS  — int (default 2000)
        PERF_SLOW_QUERY_MS   — int (default 500)
        PERF_N1_THRESHOLD    — int (default 30)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.sample_rate = getattr(settings, "PERF_SAMPLE_RATE", 1.0)
        self.slow_request_ms = getattr(settings, "PERF_SLOW_REQUEST_MS", 2000)
        self.slow_query_ms = getattr(settings, "PERF_SLOW_QUERY_MS", 500)
        self.n1_threshold = getattr(settings, "PERF_N1_THRESHOLD", 30)

    def __call__(self, request):
        global _is_cold_start

        # Determine if this request should be sampled
        should_sample = random.random() < self.sample_rate

        if not should_sample:
            return self.get_response(request)

        # Set correlation ID via contextvars
        correlation_id = uuid.uuid4().hex[:8]
        set_correlation_id(correlation_id)
        request.correlation_id = correlation_id

        # Track cold start
        cold_start = _is_cold_start
        if _is_cold_start:
            _is_cold_start = False

        start_time = time.perf_counter()

        # Execute request with DB query tracking
        with QueryTracker(slow_threshold_ms=self.slow_query_ms) as tracker:
            response = self.get_response(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Resolve view name
        resolver = getattr(request, "resolver_match", None)
        view_name = resolver.view_name if resolver else "unknown"

        # Get user info safely
        user = getattr(request, "user", None)
        user_id = None
        if user and getattr(user, "is_authenticated", False):
            user_id = user.id

        # Response size
        response_bytes = (
            len(response.content) if hasattr(response, "content") else 0
        )

        # Build log data
        data = {
            "type": "request",
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.path,
            "view": view_name,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "db_queries": tracker.count,
            "db_time_ms": round(tracker.total_ms, 2),
            "response_bytes": response_bytes,
            "cold_start": cold_start,
            "user_id": user_id,
        }

        # Determine log level
        is_slow = duration_ms >= self.slow_request_ms
        is_n1 = tracker.count >= self.n1_threshold

        if is_slow:
            data["slow_request"] = True
        if is_n1:
            data["n1_suspect"] = True

        if is_slow or is_n1:
            logger.warning("perf", extra=data)
        else:
            logger.info("perf", extra=data)

        # Log slow queries individually
        tracker.log_slow_queries(correlation_id=correlation_id)

        return response
