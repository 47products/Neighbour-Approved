"""
Logging middleware for FastAPI application.

This module provides middleware components for logging HTTP requests and responses,
ensuring comprehensive request tracking and monitoring capabilities.
"""

import time
import traceback
from typing import Callable
import uuid
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.db.config import get_settings

logger = structlog.get_logger(__name__)


def setup_logging_middleware(app: FastAPI) -> None:
    """Configure logging middleware for the application."""
    settings = get_settings()
    if settings.ENABLE_REQUEST_LOGGING:
        app.add_middleware(RequestLoggingMiddleware)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process and log request/response cycle."""
        # Skip logging for health check endpoints to reduce noise
        if request.url.path.endswith("/health"):
            return await call_next(request)

        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Bind request context
        request_logger = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Log request
        request_logger.info("http_request_started")

        # Process request and measure timing
        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log successful response
            request_logger.info(
                "http_request_completed",
                status_code=response.status_code,
                duration=round(duration, 3),
                content_length=response.headers.get("content-length"),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log failed request
            request_logger.error(
                "http_request_failed",
                error=str(e),
                error_type=type(e).__name__,
                duration=round(duration, 3),
                traceback=traceback.format_exc(),
            )
            raise
