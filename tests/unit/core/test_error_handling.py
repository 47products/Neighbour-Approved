"""
Unit tests for the error handling module.

This module tests all aspects of the `error_handling.py` module, including:
- Custom exceptions and their initialization
- Exception handlers for different error types
- JSON response structure and correctness
- The catch-all handler for unhandled exceptions
- The setup_error_handlers function to confirm correct registration

Typical usage example:
    pytest tests/unit/test_core/test_error_handling.py
"""

import json
import pytest
from datetime import datetime
from fastapi import FastAPI, status, Request
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from app.core.error_handling import (
    # Custom Exceptions
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
    # Handlers
    app_exception_handler,
    database_exception_handler,
    validation_exception_handler,
    feature_flag_exception_handler,
    subscription_exception_handler,
    catch_all_handler,
    # Utility
    create_error_response,
    setup_error_handlers,
)


#
# EXISTING TESTS
#


@pytest.mark.asyncio
async def test_database_exception_handler():
    """
    Test that database exceptions are correctly handled: NoResultFound => 404 "RECORD_NOT_FOUND".
    """
    scope = {"type": "http", "path": "/", "client": ("127.0.0.1", 8000), "headers": []}
    request = Request(scope=scope)

    response = await database_exception_handler(request, NoResultFound())

    assert response.status_code == status.HTTP_404_NOT_FOUND
    response_data = json.loads(response.body.decode("utf-8"))
    assert response_data["error_code"] == "RECORD_NOT_FOUND"


@pytest.mark.asyncio
async def test_app_exception_handler():
    """
    Test that custom application exceptions are correctly handled (BaseAppException example).
    """
    scope = {
        "type": "http",
        "path": "/test-path",
        "client": ("127.0.0.1", 8000),
        "headers": [],
    }
    request = Request(scope=scope)

    exc = BaseAppException("Custom error", "CUSTOM_ERROR", status.HTTP_400_BAD_REQUEST)
    response = await app_exception_handler(request, exc)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
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
            {"expiry_date": datetime(2024, 6, 1)},
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
    assert response_json["message"] == "Test message"


@pytest.mark.asyncio
async def test_database_exception_handler_integrity_error():
    """
    IntegrityError => 409 + "INTEGRITY_ERROR".
    """
    scope = {
        "type": "http",
        "path": "/dbtest",
        "client": ("127.0.0.1", 8000),
        "headers": [],
    }
    request = Request(scope=scope)
    exc = IntegrityError("Integrity problem", params=None, orig=None)

    response = await database_exception_handler(request, exc)
    assert response.status_code == status.HTTP_409_CONFLICT
    data = json.loads(response.body.decode("utf-8"))
    assert data["error_code"] == "INTEGRITY_ERROR"
    assert data["message"] == "Database integrity error"


@pytest.mark.asyncio
async def test_database_exception_handler_generic_sqlalchemy():
    """
    Generic SQLAlchemyError => 500 + "DATABASE_ERROR".
    """
    scope = {
        "type": "http",
        "path": "/dbother",
        "client": ("127.0.0.1", 8000),
        "headers": [],
    }
    request = Request(scope=scope)
    exc = SQLAlchemyError("Something DB-ish")

    response = await database_exception_handler(request, exc)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = json.loads(response.body.decode("utf-8"))
    assert data["error_code"] == "DATABASE_ERROR"
    assert "An unexpected database error occurred" in data["message"]


@pytest.mark.asyncio
async def test_validation_exception_handler():
    """
    RequestValidationError => 422 + "VALIDATION_ERROR".
    """
    scope = {
        "type": "http",
        "path": "/validate",
        "client": ("127.0.0.1", 8000),
        "headers": [],
    }
    request = Request(scope=scope)

    # Fake a validation error
    exc = RequestValidationError([{"loc": ["body", "field"], "msg": "Missing field"}])

    response = await validation_exception_handler(request, exc)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = json.loads(response.body.decode("utf-8"))
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "Request validation failed" in data["message"]
    assert data["details"]["errors"][0]["msg"] == "Missing field"


@pytest.mark.asyncio
async def test_feature_flag_exception_handler():
    """
    FeatureFlagError => 403 (by default).
    """
    scope = {
        "type": "http",
        "path": "/feature-flag",
        "client": ("127.0.0.1", 8000),
        "headers": [],
    }
    request = Request(scope=scope)
    exc = FeatureFlagError("A feature-flag problem")

    response = await feature_flag_exception_handler(request, exc)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = json.loads(response.body.decode("utf-8"))
    assert data["error_code"] == "FEATURE_FLAG_ERROR"
    assert data["message"] == "A feature-flag problem"


@pytest.mark.asyncio
async def test_subscription_exception_handler():
    """
    SubscriptionError => 403 (by default).
    """
    scope = {
        "type": "http",
        "path": "/subscribe-err",
        "client": ("127.0.0.1", 8000),
        "headers": [],
    }
    request = Request(scope=scope)
    exc = SubscriptionError("A subscription problem")

    response = await subscription_exception_handler(request, exc)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = json.loads(response.body.decode("utf-8"))
    assert data["error_code"] == "SUBSCRIPTION_ERROR"
    assert data["message"] == "A subscription problem"


@pytest.mark.asyncio
async def test_catch_all_handler_unit():
    """
    Test that an unhandled exception => 500 "INTERNAL_SERVER_ERROR".
    """
    scope = {
        "type": "http",
        "path": "/unhandled",
        "client": ("127.0.0.1", 8000),
        "headers": [],
    }
    request = Request(scope=scope)

    exc = ValueError("some random error")
    response = await catch_all_handler(request, exc)

    assert response.status_code == 500
    data = json.loads(response.body.decode("utf-8"))
    assert data["error_code"] == "INTERNAL_SERVER_ERROR"
    assert data["message"] == "An unexpected error occurred"
