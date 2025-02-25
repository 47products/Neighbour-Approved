"""
Unit tests for the service_exceptions module.

This module tests the behavior of the exception classes defined in the
service_exceptions module. It verifies that exceptions instantiate with
the correct default attributes, accept custom parameters, and maintain the
proper inheritance hierarchy. Additionally, it checks the string representation
of the exceptions.

Usage:
    $ pytest test_service_exceptions.py
"""

import pytest
from fastapi import status
from app.services.service_exceptions import (
    ServiceError,
    ValidationError,
    AccessDeniedError,
    ResourceNotFoundError,
    DuplicateResourceError,
    BusinessRuleViolationError,
    DependencyError,
    StateError,
    QuotaExceededError,
    ExternalServiceError,
    ConcurrencyError,
    RoleAssignmentError,
    AuthenticationError,
    EmailVerificationError,
    UserManagementError,
)


@pytest.mark.parametrize(
    "exc_class, default_message, default_code, default_status",
    [
        (
            ServiceError,
            "Service operation failed",
            "SERVICE_ERROR",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
        (
            ValidationError,
            "Business validation failed",
            "BUSINESS_VALIDATION_ERROR",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            AccessDeniedError,
            "Access denied",
            "ACCESS_DENIED",
            status.HTTP_403_FORBIDDEN,
        ),
        (
            ResourceNotFoundError,
            "Resource not found",
            "RESOURCE_NOT_FOUND",
            status.HTTP_404_NOT_FOUND,
        ),
        (
            DuplicateResourceError,
            "Resource already exists",
            "DUPLICATE_RESOURCE",
            status.HTTP_409_CONFLICT,
        ),
        (
            BusinessRuleViolationError,
            "Business rule violation",
            "BUSINESS_RULE_VIOLATION",
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            DependencyError,
            "Service dependency error",
            "DEPENDENCY_ERROR",
            status.HTTP_502_BAD_GATEWAY,
        ),
        (
            StateError,
            "Invalid state transition",
            "INVALID_STATE",
            status.HTTP_409_CONFLICT,
        ),
        (
            QuotaExceededError,
            "Quota exceeded",
            "QUOTA_EXCEEDED",
            status.HTTP_429_TOO_MANY_REQUESTS,
        ),
        (
            ExternalServiceError,
            "External service error",
            "EXTERNAL_SERVICE_ERROR",
            status.HTTP_502_BAD_GATEWAY,
        ),
        (
            ConcurrencyError,
            "Concurrent modification conflict",
            "CONCURRENCY_CONFLICT",
            status.HTTP_409_CONFLICT,
        ),
        (
            RoleAssignmentError,
            "Role assignment failed",
            "ROLE_ASSIGNMENT_ERROR",
            status.HTTP_409_CONFLICT,
        ),
        (
            AuthenticationError,
            "Authentication failed",
            "AUTHENTICATION_FAILED",
            status.HTTP_401_UNAUTHORIZED,
        ),
        (
            EmailVerificationError,
            "Email verification failed",
            "EMAIL_VERIFICATION_FAILED",
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            UserManagementError,
            "User management operation failed",
            "USER_MANAGEMENT_ERROR",
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
)
def test_default_exception_attributes(
    exc_class, default_message, default_code, default_status
):
    """
    Test that exception classes instantiate with default attributes.

    This test instantiates each exception using its default parameters and verifies
    that the message, error_code, status_code, and details attributes are set correctly.
    Here, if no details are provided, we expect details to be an empty dict.
    """
    exc = exc_class()
    assert exc.message == default_message, "Default message does not match."
    assert exc.error_code == default_code, "Default error code does not match."
    assert exc.status_code == default_status, "Default status code does not match."
    # Instead of expecting details to be None, we check that it is an empty dict.
    assert exc.details == {}, "Default details should be an empty dict if not provided."


@pytest.mark.parametrize(
    "exc_class, custom_message, custom_details",
    [
        (ServiceError, "Custom service error", {"info": "detail"}),
        (ValidationError, "Custom validation error", {"field": "value"}),
        (AccessDeniedError, "Custom access denied", {"user": "test"}),
        (ResourceNotFoundError, "Custom resource not found", {"resource": "item"}),
        (DuplicateResourceError, "Custom duplicate resource", {"duplicate": True}),
        (BusinessRuleViolationError, "Custom business rule violation", {"rule": "X"}),
        (DependencyError, "Custom dependency error", {"dependency": "Y"}),
        (StateError, "Custom state error", {"state": "invalid"}),
        (QuotaExceededError, "Custom quota exceeded", {"quota": 10}),
        (ExternalServiceError, "Custom external error", {"service": "api"}),
        (ConcurrencyError, "Custom concurrency error", {"conflict": True}),
        (RoleAssignmentError, "Custom role assignment error", {"role": "admin"}),
        (AuthenticationError, "Custom authentication error", {"token": "expired"}),
        (
            EmailVerificationError,
            "Custom email verification error",
            {"token": "invalid"},
        ),
        (UserManagementError, "Custom user management error", {"operation": "update"}),
    ],
)
def test_custom_exception_attributes(exc_class, custom_message, custom_details):
    """
    Test that exception classes correctly use custom attributes.

    This test instantiates each exception with a custom message and details,
    then verifies that these attributes are set as provided.
    """
    exc = exc_class(message=custom_message, details=custom_details)
    assert exc.message == custom_message, "Custom message does not match."
    assert exc.details == custom_details, "Custom details do not match."


@pytest.mark.parametrize(
    "exc_class",
    [
        ValidationError,
        AccessDeniedError,
        ResourceNotFoundError,
        DuplicateResourceError,
        BusinessRuleViolationError,
        DependencyError,
        StateError,
        QuotaExceededError,
        ExternalServiceError,
        ConcurrencyError,
        RoleAssignmentError,
        AuthenticationError,
        EmailVerificationError,
        UserManagementError,
    ],
)
def test_exception_inheritance(exc_class):
    """
    Test that each service exception is a subclass of ServiceError.

    This ensures that the exception hierarchy is maintained for proper error handling.
    """
    exc = exc_class()
    assert isinstance(
        exc, ServiceError
    ), f"{exc_class.__name__} is not a subclass of ServiceError."


def test_str_representation():
    """
    Test the string representation of a service exception.

    This test verifies that the __str__ method returns a string that includes the message.
    """
    custom_message = "Test error"
    exc = ValidationError(message=custom_message)
    # Assuming the base exception's __str__ returns the message (or includes it)
    assert custom_message in str(
        exc
    ), "String representation does not include the custom message."
