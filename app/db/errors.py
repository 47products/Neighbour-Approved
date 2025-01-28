"""
Repository error handling module.

This module defines repository-specific exceptions for handling database-level errors.
These exceptions focus on data access concerns and provide clear separation from
service-layer error handling.
"""

from typing import Any, Dict, Optional


class RepositoryError(Exception):
    """Base exception for repository-level errors."""

    def __init__(
        self,
        message: str = "Repository operation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize repository error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RecordNotFoundError(RepositoryError):
    """Exception raised when a database record cannot be found."""

    def __init__(
        self,
        message: str = "Record not found in database",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize not found error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message, details)


class DuplicateRecordError(RepositoryError):
    """Exception raised when attempting to create a duplicate record."""

    def __init__(
        self,
        message: str = "Record already exists in database",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize duplicate record error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message, details)


class DatabaseConnectionError(RepositoryError):
    """Exception raised when database connection fails."""

    def __init__(
        self,
        message: str = "Failed to connect to database",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize connection error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message, details)


class QueryError(RepositoryError):
    """Exception raised when a database query fails."""

    def __init__(
        self,
        message: str = "Database query failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize query error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message, details)


class TransactionError(RepositoryError):
    """Exception raised when a database transaction fails."""

    def __init__(
        self,
        message: str = "Database transaction failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize transaction error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message, details)


class IntegrityError(RepositoryError):
    """Exception raised when database integrity is violated."""

    def __init__(
        self,
        message: str = "Database integrity violation",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize integrity error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message, details)


class ValidationError(RepositoryError):
    """Exception raised when database validation fails."""

    def __init__(
        self,
        message: str = "Database validation failed",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize validation error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message, details)


class MappingError(RepositoryError):
    """Exception raised when object mapping fails."""

    def __init__(
        self,
        message: str = "Failed to map database record",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize mapping error.

        Args:
            message: Error description
            details: Additional error context
        """
        super().__init__(message, details)
