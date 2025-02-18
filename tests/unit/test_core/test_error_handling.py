"""
Unit tests for the error handling module.

This module tests all aspects of the `error_handling.py` module, including:
- Custom exceptions and their initialization
- Exception handlers for different error types
- JSON response structure and correctness

Typical usage example:
    pytest tests/unit/test_core/test_error_handling.py
"""

import json
import pytest
from fastapi import status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from pydantic import BaseModel, ValidationError as PydanticValidationError
from app.core.error_handling import (
    BaseAppException,
    DatabaseError,
    RecordNotFoundError,
    DuplicateRecordError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    BusinessLogicError,
    FeatureFlagError,
    FeatureNotAvailableError,
    FeatureLimitExceededError,
    SubscriptionError,
    SubscriptionRequiredError,
    SubscriptionExpiredError,
    database_exception_handler,
    validation_exception_handler,
    app_exception_handler,
    create_error_response,
)


@pytest.mark.asyncio
async def test_database_exception_handler():
    """
    Test that database exceptions are correctly handled.
    """
    request = Request(
        scope={
            "type": "http",
            "path": "/",
            "client": ("127.0.0.1", 8000),
            "headers": [],  # Empty list to satisfy Starlette's requirements
        }
    )
    response = await database_exception_handler(request, NoResultFound())

    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Decode response body and parse as JSON
    response_data = json.loads(response.body.decode("utf-8"))

    assert response_data["error_code"] == "RECORD_NOT_FOUND"


@pytest.mark.asyncio
async def test_app_exception_handler():
    """
    Test that custom application exceptions are correctly handled.
    """
    request = Request(
        scope={
            "type": "http",
            "path": "/test-path",
            "client": ("127.0.0.1", 8000),
            "headers": [],  # Ensure headers key is present
        }
    )

    exc = BaseAppException("Custom error", "CUSTOM_ERROR", status.HTTP_400_BAD_REQUEST)

    response = await app_exception_handler(request, exc)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Decode response body and parse as JSON
    response_data = json.loads(response.body.decode("utf-8"))

    assert response_data["error_code"] == "CUSTOM_ERROR"
    assert response_data["message"] == "Custom error"


@pytest.mark.parametrize(
    "exception_class, kwargs, error_code, status_code",
    [
        (DatabaseError, {}, "DATABASE_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR),
        (RecordNotFoundError, {}, "RECORD_NOT_FOUND", status.HTTP_404_NOT_FOUND),
        (DuplicateRecordError, {}, "DUPLICATE_RECORD", status.HTTP_409_CONFLICT),
        (
            AuthenticationError,
            {},
            "AUTHENTICATION_FAILED",
            status.HTTP_401_UNAUTHORIZED,
        ),
        (AuthorizationError, {}, "AUTHORIZATION_FAILED", status.HTTP_403_FORBIDDEN),
        (ValidationError, {}, "VALIDATION_ERROR", status.HTTP_422_UNPROCESSABLE_ENTITY),
        (BusinessLogicError, {}, "BUSINESS_LOGIC_ERROR", status.HTTP_400_BAD_REQUEST),
        (FeatureFlagError, {}, "FEATURE_FLAG_ERROR", status.HTTP_403_FORBIDDEN),
        (
            FeatureNotAvailableError,
            {"feature_key": "beta-feature"},
            "FEATURE_NOT_AVAILABLE",
            status.HTTP_403_FORBIDDEN,
        ),
        (
            FeatureLimitExceededError,
            {"feature_key": "api-calls", "current_usage": 105, "limit": 100},
            "FEATURE_LIMIT_EXCEEDED",
            status.HTTP_403_FORBIDDEN,
        ),
        (SubscriptionError, {}, "SUBSCRIPTION_ERROR", status.HTTP_403_FORBIDDEN),
        (
            SubscriptionRequiredError,
            {},
            "SUBSCRIPTION_REQUIRED",
            status.HTTP_403_FORBIDDEN,
        ),
        (
            SubscriptionExpiredError,
            {"expiry_date": "2024-06-01"},
            "SUBSCRIPTION_EXPIRED",
            status.HTTP_403_FORBIDDEN,
        ),
    ],
)
def test_custom_exceptions(exception_class, kwargs, error_code, status_code):
    """
    Test that custom exceptions initialize correctly with expected attributes.
    """
    exc = exception_class(**kwargs)
    assert exc.error_code == error_code
    assert exc.status_code == status_code


def test_create_error_response():
    """
    Test that error responses are correctly formatted.
    """
    response = create_error_response(
        "TEST_ERROR", "Test message", status.HTTP_400_BAD_REQUEST
    )
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response_json = json.loads(response.body.decode("utf-8"))
    assert response_json["error_code"] == "TEST_ERROR"
