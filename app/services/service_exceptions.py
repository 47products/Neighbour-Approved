"""
Service layer exception handling module for Neighbour Approved application.

This module defines a comprehensive exception hierarchy for the service layer,
providing specific exception types for different categories of business logic
errors. It enables precise error handling and appropriate HTTP status code
mapping while maintaining clear error messages for API consumers.
"""

from typing import Any, Dict, Optional
from fastapi import status
from app.core.error_handling import BaseAppException


class ServiceError(BaseAppException):
    """Base exception for all service layer errors.

    This exception serves as the foundation for all service-specific exceptions,
    ensuring consistent error handling patterns across the service layer.
    """

    def __init__(
        self,
        message: str = "Service operation failed",
        error_code: str = "SERVICE_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize service error.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error context
        """
        super().__init__(message, error_code, status_code, details)


class ValidationError(ServiceError):
    """Exception for business rule validation failures.

    Raised when an operation violates business rules or constraints,
    distinct from schema validation errors.
    """

    def __init__(
        self,
        message: str = "Business validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation error.

        Args:
            message: Validation error description
            details: Additional validation context
        """
        super().__init__(
            message,
            "BUSINESS_VALIDATION_ERROR",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            details,
        )


class AccessDeniedError(ServiceError):
    """Exception for authorization and access control failures.

    Raised when an operation is not permitted due to business rules
    or access control policies.
    """

    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize access denied error.

        Args:
            message: Access denial reason
            details: Additional context about the access attempt
        """
        super().__init__(
            message,
            "ACCESS_DENIED",
            status.HTTP_403_FORBIDDEN,
            details,
        )


class ResourceNotFoundError(ServiceError):
    """Exception for business-logic level resource not found conditions.

    Raised when a required resource does not exist or is not accessible
    in the current context.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize resource not found error.

        Args:
            message: Description of the missing resource
            details: Additional context about the resource
        """
        super().__init__(
            message,
            "RESOURCE_NOT_FOUND",
            status.HTTP_404_NOT_FOUND,
            details,
        )


class DuplicateResourceError(ServiceError):
    """Exception for unique constraint violations at business logic level.

    Raised when an operation would create a duplicate resource where
    business rules require uniqueness.
    """

    def __init__(
        self,
        message: str = "Resource already exists",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize duplicate resource error.

        Args:
            message: Description of the uniqueness violation
            details: Additional context about the duplicate
        """
        super().__init__(
            message,
            "DUPLICATE_RESOURCE",
            status.HTTP_409_CONFLICT,
            details,
        )


class BusinessRuleViolationError(ServiceError):
    """Exception for violations of complex business rules.

    Raised when an operation violates business rules that go beyond
    simple validation or access control.
    """

    def __init__(
        self,
        message: str = "Business rule violation",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize business rule violation error.

        Args:
            message: Description of the rule violation
            details: Additional context about the violation
        """
        super().__init__(
            message,
            "BUSINESS_RULE_VIOLATION",
            status.HTTP_400_BAD_REQUEST,
            details,
        )


class DependencyError(ServiceError):
    """Exception for failures in service dependencies.

    Raised when a required service dependency is unavailable or returns
    an error.
    """

    def __init__(
        self,
        message: str = "Service dependency error",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize dependency error.

        Args:
            message: Description of the dependency failure
            details: Additional context about the dependency
        """
        super().__init__(
            message,
            "DEPENDENCY_ERROR",
            status.HTTP_502_BAD_GATEWAY,
            details,
        )


class StateError(ServiceError):
    """Exception for invalid state transitions.

    Raised when an operation is not allowed due to the current state
    of a resource.
    """

    def __init__(
        self,
        message: str = "Invalid state transition",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize state error.

        Args:
            message: Description of the state violation
            details: Additional context about the state
        """
        super().__init__(
            message,
            "INVALID_STATE",
            status.HTTP_409_CONFLICT,
            details,
        )


class QuotaExceededError(ServiceError):
    """Exception for quota and limit violations.

    Raised when an operation would exceed defined quotas or limits
    in the business rules.
    """

    def __init__(
        self,
        message: str = "Quota exceeded",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize quota exceeded error.

        Args:
            message: Description of the quota violation
            details: Additional context about the quota
        """
        super().__init__(
            message,
            "QUOTA_EXCEEDED",
            status.HTTP_429_TOO_MANY_REQUESTS,
            details,
        )


class ExternalServiceError(ServiceError):
    """Exception for external service integration failures.

    Raised when an operation fails due to an error in an external
    service integration.
    """

    def __init__(
        self,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize external service error.

        Args:
            message: Description of the external service failure
            details: Additional context about the external service
        """
        super().__init__(
            message,
            "EXTERNAL_SERVICE_ERROR",
            status.HTTP_502_BAD_GATEWAY,
            details,
        )


class ConcurrencyError(ServiceError):
    """Exception for concurrent modification conflicts.

    Raised when an operation fails due to concurrent modifications
    of the same resource.
    """

    def __init__(
        self,
        message: str = "Concurrent modification conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize concurrency error.

        Args:
            message: Description of the concurrency conflict
            details: Additional context about the conflict
        """
        super().__init__(
            message,
            "CONCURRENCY_CONFLICT",
            status.HTTP_409_CONFLICT,
            details,
        )


class RoleAssignmentError(ServiceError):
    """Exception for role assignment failures.

    Raised when a role assignment operation cannot be completed due to
    business rule violations, such as incompatible role combinations or
    permission hierarchy conflicts.

    Args:
        message: Description of the role assignment error
        details: Optional additional context about the error
    """

    def __init__(
        self,
        message: str = "Role assignment failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize role assignment error.

        Args:
            message: Human-readable error description
            details: Additional error context
        """
        super().__init__(
            message,
            "ROLE_ASSIGNMENT_ERROR",
            status.HTTP_409_CONFLICT,
            details,
        )


class AuthenticationError(ServiceError):
    """Exception for authentication failures.

    Raised when user authentication fails, such as incorrect credentials
    or invalid authentication tokens.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize authentication error.

        Args:
            message: Description of the authentication failure
            details: Additional error context
        """
        super().__init__(
            message,
            "AUTHENTICATION_FAILED",
            status.HTTP_401_UNAUTHORIZED,
            details,
        )


class EmailVerificationError(ServiceError):
    """Exception for email verification failures.

    Raised when email verification fails due to invalid or expired tokens.
    """

    def __init__(
        self,
        message: str = "Email verification failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize email verification error.

        Args:
            message: Description of the verification failure
            details: Additional error context
        """
        super().__init__(
            message,
            "EMAIL_VERIFICATION_FAILED",
            status.HTTP_400_BAD_REQUEST,
            details,
        )


class UserManagementError(ServiceError):
    """Exception for user management operation failures.

    Raised when user management operations fail due to business rule violations.
    """

    def __init__(
        self,
        message: str = "User management operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize user management error.

        Args:
            message: Description of the operation failure
            details: Additional error context
        """
        super().__init__(
            message,
            "USER_MANAGEMENT_ERROR",
            status.HTTP_400_BAD_REQUEST,
            details,
        )
