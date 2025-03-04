# pylint: disable=unused-argument
"""
Exception handling module for the Neighbour Approved application.

This module provides centralised exception handling for the application.
It defines custom exceptions, middleware for API error responses,
and utilities for logging exceptions consistently.
"""

from typing import Dict, Any, Optional, Type, Callable, Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging.logger import get_logger

logger = get_logger(__name__)


class BaseAppException(Exception):
    """
    Base exception class for application-specific exceptions.

    This serves as the parent class for all custom exceptions in the application,
    providing consistent structure and behaviour.

    Attributes:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code to return
        details: Additional error details
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception with error information.

        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            status_code: HTTP status code to return
            details: Additional error details
        """
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(BaseAppException):
    """Exception raised when a requested resource cannot be found."""

    def __init__(
        self,
        message: str = "The requested resource was not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[str, int]] = None,
    ):
        """
        Initialize the exception with resource information.

        Args:
            message: Human-readable error message
            resource_type: Type of resource that was not found
            resource_id: ID of resource that was not found
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            error_code="RESOURCE_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ValidationError(BaseAppException):
    """Exception raised when validation fails for input data."""

    def __init__(
        self, message: str = "Validation error", fields: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the exception with validation information.

        Args:
            message: Human-readable error message
            fields: Dictionary of field names to error messages
        """
        details = {"fields": fields} if fields else {}

        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationError(BaseAppException):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        """
        Initialize the exception with authentication information.

        Args:
            message: Human-readable error message
        """
        super().__init__(
            error_code="AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(BaseAppException):
    """Exception raised when a user lacks permission for an operation."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        required_permission: Optional[str] = None,
    ):
        """
        Initialize the exception with authorization information.

        Args:
            message: Human-readable error message
            required_permission: Permission that was required
        """
        details = {}
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            error_code="AUTHORIZATION_ERROR",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class DatabaseError(BaseAppException):
    """Exception raised when a database operation fails."""

    def __init__(
        self,
        message: str = "A database error occurred",
        operation: Optional[str] = None,
    ):
        """
        Initialize the exception with database information.

        Args:
            message: Human-readable error message
            operation: Database operation that failed
        """
        details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            error_code="DATABASE_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ExternalServiceError(BaseAppException):
    """Exception raised when an external service call fails."""

    def __init__(
        self, message: str = "External service error", service: Optional[str] = None
    ):
        """
        Initialize the exception with service information.

        Args:
            message: Human-readable error message
            service: Name of the external service
        """
        details = {}
        if service:
            details["service"] = service

        super().__init__(
            error_code="EXTERNAL_SERVICE_ERROR",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


# Map of exception types to handlers
EXCEPTION_HANDLERS: Dict[Type[Exception], Callable] = {}


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation exceptions from FastAPI.

    Args:
        request: FastAPI request object
        exc: Validation exception

    Returns:
        JSONResponse: Structured error response
    """
    error_details = {}

    for error in exc.errors():
        location = error.get("loc", [])
        if location and len(location) >= 2:
            field = location[1]
            error_details[field] = error.get("msg", "Invalid value")

    logger.warning("Validation error: %s", exc.errors())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"fields": error_details},
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions from FastAPI.

    Args:
        request: FastAPI request object
        exc: HTTP exception

    Returns:
        JSONResponse: Structured error response
    """
    logger.warning("HTTP exception: %s - %s", exc.status_code, exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {},
        },
    )


async def app_exception_handler(request: Request, exc: BaseAppException):
    """
    Handle application-specific exceptions.

    Args:
        request: FastAPI request object
        exc: Application exception

    Returns:
        JSONResponse: Structured error response
    """
    # Log the exception
    if exc.status_code >= 500:
        logger.error(
            "Application exception: %s - %s", exc.error_code, exc.message, exc_info=True
        )
    else:
        logger.warning("Application exception: %s - %s", exc.error_code, exc.message)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Handle any unhandled exceptions.

    Args:
        request: FastAPI request object
        exc: Unhandled exception

    Returns:
        JSONResponse: Structured error response
    """
    # Log the unhandled exception
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)},
        },
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Register built-in exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Register application exception handlers
    app.add_exception_handler(BaseAppException, app_exception_handler)

    # Register catch-all handler for unhandled exceptions
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Register any additional handlers from the EXCEPTION_HANDLERS dict
    for exc_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)
