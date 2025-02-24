"""
Logging middleware for the Neighbour Approved application.

This module provides middleware components for logging HTTP requests and responses,
ensuring comprehensive request tracking and monitoring capabilities. It integrates
with the application's middleware management system to provide standardized logging
across all requests.

The middleware captures key request metrics including:
- Request timing
- Status codes
- Error tracking
- Request context (path, method, client info)
- Response size

Example:
    ```python
    from app.core.middleware_management import MiddlewareRegistry
    
    registry = MiddlewareRegistry()
    registry.register(
        RequestLoggingMiddleware,
        priority=MiddlewarePriority.FIRST,
        config={"enable_request_logging": True}
    )
    ```
"""

import time
import traceback
from typing import List
import uuid
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import RequestResponseEndpoint
import structlog

from app.core.middleware_management import (
    BaseMiddleware,
    MiddlewareConfig,
    MiddlewareRegistry,
    MiddlewarePriority,
)
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class RequestLoggingConfig(MiddlewareConfig):
    """Configuration for request logging middleware."""

    skip_paths: List[str] = ["/health"]
    include_headers: bool = False
    include_query_params: bool = True
    max_body_size: int = 1024


class RequestLoggingMiddleware(BaseMiddleware[RequestLoggingConfig]):
    """
    Middleware for logging HTTP requests and responses.

    This middleware component provides comprehensive logging of HTTP request/response
    cycles, including timing, status codes, and error tracking.
    """

    config_class = RequestLoggingConfig

    async def process(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process and log request/response cycle.
        """
        settings = get_settings()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Bind structured log context
        request_logger = self._logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Ensure JSON format for structured logs in files
        if settings.LOG_FORMAT == "json":
            request_logger = structlog.get_logger(__name__).bind(json=True)

        request_logger.info("http_request_started")

        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            request_logger.info(
                "http_request_completed",
                status_code=response.status_code,
                duration=round(duration, 3),
                content_length=response.headers.get("content-length"),
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            duration = time.time() - start_time
            request_logger.error(
                "http_request_failed",
                error=str(e),
                error_type=type(e).__name__,
                duration=round(duration, 3),
                traceback=traceback.format_exc(),
            )
            raise

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Dispatch method required by BaseHTTPMiddleware.
        """
        if request.url.path in self.config.skip_paths:
            return await call_next(request)

        try:
            self._logger.debug("middleware_start", path=request.url.path)
            response = await self.process(request, call_next)
            self._logger.debug(
                "middleware_complete",
                path=request.url.path,
                status_code=response.status_code,
            )
            return response
        except Exception as e:
            self._logger.error(
                "middleware_error",
                error=str(e),
                error_type=type(e).__name__,
                path=request.url.path,
            )
            raise


def setup_logging_middleware(app: FastAPI) -> None:
    """
    Configure logging middleware for the application.

    This function initializes and registers the logging middleware with the
    application's middleware registry. It respects application settings for
    enabling/disabling request logging.
    """
    settings = get_settings()
    registry = MiddlewareRegistry()

    if settings.ENABLE_REQUEST_LOGGING:
        registry.register(
            RequestLoggingMiddleware,
            priority=MiddlewarePriority.FIRST,
            config={"enable_request_logging": True},
        )

    registry.apply_middlewares(app)
