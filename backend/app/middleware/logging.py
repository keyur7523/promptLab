"""Structured logging middleware with correlation IDs."""
import structlog
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time


# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs and log all requests.

    Adds a unique trace_id to each request for tracking across services.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        # Generate correlation ID
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        # Bind trace_id to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(trace_id=trace_id)

        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None
        )

        # Process request and measure latency
        start_time = time.time()
        try:
            response = await call_next(request)
            latency_ms = int((time.time() - start_time) * 1000)

            # Log response
            logger.info(
                "request_completed",
                status_code=response.status_code,
                latency_ms=latency_ms
            )

            # Add trace ID to response headers
            response.headers["X-Trace-ID"] = trace_id

            return response

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            # Log error
            logger.error(
                "request_failed",
                error=str(e),
                error_type=type(e).__name__,
                latency_ms=latency_ms
            )
            raise


def get_logger():
    """Get configured structured logger."""
    return logger
