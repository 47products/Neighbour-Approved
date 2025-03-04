"""
Request logging middleware for the Neighbour Approved application.

This module provides middleware for logging HTTP requests and responses,
including timing information, status codes, and other relevant details.
"""

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    This middleware logs information about incoming requests and outgoing responses,
    including timing information, status codes, and other relevant details.
    It also adds a request ID to facilitate request tracing across logs.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request and response, logging relevant information.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint handler

        Returns:
            Response: The HTTP response
        """
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log the start of the request
        start_time = time.time()
        method = request.method
        url = str(request.url)
        client = (
            f"{request.client.host}:{request.client.port}"
            if request.client
            else "unknown"
        )

        logger.info(
            "Request started: %s %s from %s [request_id=%s]",
            method,
            url,
            client,
            request_id,
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time
            formatted_process_time = f"{process_time:.4f}"

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log the completion of the request
            status_code = response.status_code
            logger.info(
                "Request completed: %s %s [status=%s] [time=%ss] [request_id=%s]",
                method,
                url,
                status_code,
                formatted_process_time,
                request_id,
            )

            return response

        except Exception as exc:
            # Calculate processing time even for failed requests
            process_time = time.time() - start_time
            formatted_process_time = f"{process_time:.4f}"

            # Log the exception
            logger.error(
                "Request failed: %s %s [error=%s] [time=%ss] [request_id=%s]",
                method,
                url,
                str(exc),
                formatted_process_time,
                request_id,
                exc_info=True,
            )

            # Re-raise the exception to be handled by exception handlers
            raise


def add_request_logging_middleware(app):
    """
    Add the request logging middleware to the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)
