"""
Error handling framework for the Neighbour Approved application.

This module provides a comprehensive error handling system including custom exceptions,
error handlers, and middleware for consistent error handling across the application.
It ensures that all errors are properly logged, formatted, and returned to clients
in a consistent manner.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import (
    IntegrityError,
    NoResultFound,
    SQLAlchemyError,
)
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class BaseAppException(Exception):
    """Base exception for application-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


# Database Exceptions
class DatabaseError(BaseAppException):
    """Base exception for database-related errors."""

    def __init__(
        self,
        message: str = "Database error occurred",
        error_code: str = "DATABASE_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, status_code, details)


class RecordNotFoundError(DatabaseError):
    """Exception raised when a database record is not found."""

    def __init__(
        self,
        message: str = "Record not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message, "RECORD_NOT_FOUND", status.HTTP_404_NOT_FOUND, details
        )


class DuplicateRecordError(DatabaseError):
    """Exception raised for unique constraint violations."""

    def __init__(
        self,
        message: str = "Record already exists",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "DUPLICATE_RECORD", status.HTTP_409_CONFLICT, details)


# Authentication/Authorization Exceptions
class AuthenticationError(BaseAppException):
    """Exception raised for authentication failures."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message, "AUTHENTICATION_FAILED", status.HTTP_401_UNAUTHORIZED, details
        )


class AuthorizationError(BaseAppException):
    """Exception raised for authorization failures."""

    def __init__(
        self,
        message: str = "Not authorized to perform this action",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message, "AUTHORIZATION_FAILED", status.HTTP_403_FORBIDDEN, details
        )


# Validation Exceptions
class ValidationError(BaseAppException):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message, "VALIDATION_ERROR", status.HTTP_422_UNPROCESSABLE_ENTITY, details
        )


# Business Logic Exceptions
class BusinessLogicError(BaseAppException):
    """Exception raised for business rule violations."""

    def __init__(
        self,
        message: str = "Business rule violation",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message, "BUSINESS_LOGIC_ERROR", status.HTTP_400_BAD_REQUEST, details
        )


# Feature Flag Exceptions
class FeatureFlagError(BaseAppException):
    """Base exception for feature flag related errors."""

    def __init__(
        self,
        message: str = "Feature flag error occurred",
        error_code: str = "FEATURE_FLAG_ERROR",
        status_code: int = status.HTTP_403_FORBIDDEN,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, status_code, details)


class FeatureNotAvailableError(FeatureFlagError):
    """Exception raised when a feature is not available in the current plan."""

    def __init__(
        self,
        feature_key: str,
        message: str = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = (
            message or f"Feature '{feature_key}' is not available in your current plan"
        )
        super().__init__(
            message,
            "FEATURE_NOT_AVAILABLE",
            status.HTTP_403_FORBIDDEN,
            details or {"feature_key": feature_key},
        )


class FeatureLimitExceededError(FeatureFlagError):
    """Exception raised when a feature's usage limit is exceeded."""

    def __init__(
        self,
        feature_key: str,
        current_usage: int,
        limit: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = (
            f"Usage limit exceeded for feature '{feature_key}': {current_usage}/{limit}"
        )
        super().__init__(
            message,
            "FEATURE_LIMIT_EXCEEDED",
            status.HTTP_403_FORBIDDEN,
            details
            or {
                "feature_key": feature_key,
                "current_usage": current_usage,
                "limit": limit,
            },
        )


# Subscription Exceptions
class SubscriptionError(BaseAppException):
    """Base exception for subscription related errors."""

    def __init__(
        self,
        message: str = "Subscription error occurred",
        error_code: str = "SUBSCRIPTION_ERROR",
        status_code: int = status.HTTP_403_FORBIDDEN,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, status_code, details)


class SubscriptionRequiredError(SubscriptionError):
    """Exception raised when a subscription is required but not present."""

    def __init__(
        self,
        message: str = "This action requires an active subscription",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message, "SUBSCRIPTION_REQUIRED", status.HTTP_403_FORBIDDEN, details
        )


class SubscriptionExpiredError(SubscriptionError):
    """Exception raised when the subscription has expired."""

    def __init__(
        self,
        expiry_date: datetime,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"Subscription expired on {expiry_date}"
        super().__init__(
            message,
            "SUBSCRIPTION_EXPIRED",
            status.HTTP_403_FORBIDDEN,
            details or {"expiry_date": expiry_date},
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response."""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=error_code, message=message, details=details
        ).model_dump(exclude_none=True),
    )


async def database_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy exceptions."""
    logger.error(
        "database_error",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
    )

    if isinstance(exc, NoResultFound):
        return create_error_response(
            "RECORD_NOT_FOUND", "Record not found", status.HTTP_404_NOT_FOUND
        )

    if isinstance(exc, IntegrityError):
        return create_error_response(
            "INTEGRITY_ERROR", "Database integrity error", status.HTTP_409_CONFLICT
        )

    return create_error_response(
        "DATABASE_ERROR",
        "An unexpected database error occurred",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation exceptions."""
    logger.error(
        "validation_error",
        error=str(exc),
        url=str(request.url),
        validation_errors=exc.errors(),
    )

    return create_error_response(
        "VALIDATION_ERROR",
        "Request validation failed",
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        {"errors": exc.errors()},
    )


async def app_exception_handler(
    request: Request, exc: BaseAppException
) -> JSONResponse:
    """Handle application-specific exceptions."""
    logger.error(
        "application_error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        url=str(request.url),
    )

    return create_error_response(
        exc.error_code, exc.message, exc.status_code, exc.details
    )


async def feature_flag_exception_handler(
    request: Request, exc: FeatureFlagError
) -> JSONResponse:
    """Handle feature flag related exceptions."""
    logger.error(
        "feature_flag_error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        url=str(request.url),
    )

    return create_error_response(
        exc.error_code, exc.message, exc.status_code, exc.details
    )


async def subscription_exception_handler(
    request: Request, exc: SubscriptionError
) -> JSONResponse:
    """Handle subscription related exceptions."""
    logger.error(
        "subscription_error",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        url=str(request.url),
    )

    return create_error_response(
        exc.error_code, exc.message, exc.status_code, exc.details
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Configure error handlers for the application."""
    # Register feature flag and subscription handlers
    app.add_exception_handler(FeatureFlagError, feature_flag_exception_handler)
    app.add_exception_handler(SubscriptionError, subscription_exception_handler)

    # Register core error handlers
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(BaseAppException, app_exception_handler)

    @app.exception_handler(Exception)
    async def catch_all_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle any unhandled exceptions."""
        logger.error(
            "unhandled_error",
            error=str(exc),
            error_type=type(exc).__name__,
            url=str(request.url),
        )

        return create_error_response(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
