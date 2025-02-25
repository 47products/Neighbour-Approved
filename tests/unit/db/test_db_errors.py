"""
Repository error handling module for Neighbour Approved.

This module defines repository-specific exceptions for handling database-level errors
in the Neighbour Approved application. These exceptions focus on data access concerns
and provide clear separation from service-layer error handling.

Key Classes:
    - RepositoryError: Base exception for repository-level errors
    - RecordNotFoundError: Exception raised when a database record cannot be found
    - DuplicateRecordError: Exception raised when attempting to create a duplicate record
    - DatabaseConnectionError: Exception raised when database connection fails
    - QueryError: Exception raised when a database query fails
    - TransactionError: Exception raised when a database transaction fails
    - IntegrityError: Exception raised when database integrity is violated
    - ValidationError: Exception raised when database validation fails
    - MappingError: Exception raised when object mapping fails

Usage Example:
    from app.db.errors import RecordNotFoundError

    def get_user_by_id(db_session, user_id: int):
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            raise RecordNotFoundError(details={"user_id": user_id})
        return user

Dependencies:
    - Python 3.9+
    - SQLAlchemy
    - Pydantic (for typed details, if needed)
    - structlog (optional, for logging errors)

Version:
    1.0.0
"""

import pytest
from app.db.errors import (
    RepositoryError,
    RecordNotFoundError,
    DuplicateRecordError,
    DatabaseConnectionError,
    QueryError,
    TransactionError,
    IntegrityError,
    ValidationError,
    MappingError,
)


def test_repository_error_default():
    """
    Test the default initialization of RepositoryError.
    """
    exc = RepositoryError()
    assert exc.message == "Repository operation failed"
    assert exc.details == {}

    with pytest.raises(RepositoryError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Repository operation failed"


def test_repository_error_custom():
    """
    Test custom initialization of RepositoryError with custom message and details.
    """
    exc = RepositoryError(message="Custom error", details={"info": "some data"})
    assert exc.message == "Custom error"
    assert exc.details == {"info": "some data"}

    with pytest.raises(RepositoryError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Custom error"


def test_record_not_found_error_default():
    """
    Test the default initialization of RecordNotFoundError.
    """
    exc = RecordNotFoundError()
    assert exc.message == "Record not found in database"
    assert exc.details == {}

    with pytest.raises(RecordNotFoundError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Record not found in database"
    # Also check inheritance
    assert isinstance(exc, RepositoryError)


def test_record_not_found_error_custom():
    """
    Test custom initialization of RecordNotFoundError with custom message and details.
    """
    exc = RecordNotFoundError(message="Custom not found", details={"id": 123})
    assert exc.message == "Custom not found"
    assert exc.details == {"id": 123}

    with pytest.raises(RecordNotFoundError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Custom not found"


def test_duplicate_record_error_default():
    """
    Test the default initialization of DuplicateRecordError.
    """
    exc = DuplicateRecordError()
    assert exc.message == "Record already exists in database"
    assert exc.details == {}

    with pytest.raises(DuplicateRecordError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Record already exists in database"
    assert isinstance(exc, RepositoryError)


def test_duplicate_record_error_custom():
    """
    Test custom initialization of DuplicateRecordError with custom message and details.
    """
    exc = DuplicateRecordError(message="Duplicate found", details={"field": "email"})
    assert exc.message == "Duplicate found"
    assert exc.details == {"field": "email"}

    with pytest.raises(DuplicateRecordError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Duplicate found"


def test_database_connection_error_default():
    """
    Test the default initialization of DatabaseConnectionError.
    """
    exc = DatabaseConnectionError()
    assert exc.message == "Failed to connect to database"
    assert exc.details == {}

    with pytest.raises(DatabaseConnectionError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Failed to connect to database"
    assert isinstance(exc, RepositoryError)


def test_database_connection_error_custom():
    """
    Test custom initialization of DatabaseConnectionError with custom message and details.
    """
    exc = DatabaseConnectionError(message="Connection refused", details={"host": "db"})
    assert exc.message == "Connection refused"
    assert exc.details == {"host": "db"}

    with pytest.raises(DatabaseConnectionError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Connection refused"


def test_query_error_default():
    """
    Test the default initialization of QueryError.
    """
    exc = QueryError()
    assert exc.message == "Database query failed"
    assert exc.details == {}

    with pytest.raises(QueryError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Database query failed"
    assert isinstance(exc, RepositoryError)


def test_query_error_custom():
    """
    Test custom initialization of QueryError with custom message and details.
    """
    exc = QueryError(message="Invalid query syntax", details={"query": "SELECT *"})
    assert exc.message == "Invalid query syntax"
    assert exc.details == {"query": "SELECT *"}

    with pytest.raises(QueryError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Invalid query syntax"


def test_transaction_error_default():
    """
    Test the default initialization of TransactionError.
    """
    exc = TransactionError()
    assert exc.message == "Database transaction failed"
    assert exc.details == {}

    with pytest.raises(TransactionError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Database transaction failed"
    assert isinstance(exc, RepositoryError)


def test_transaction_error_custom():
    """
    Test custom initialization of TransactionError with custom message and details.
    """
    exc = TransactionError(message="Could not commit", details={"tx_id": "abc123"})
    assert exc.message == "Could not commit"
    assert exc.details == {"tx_id": "abc123"}

    with pytest.raises(TransactionError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Could not commit"


def test_integrity_error_default():
    """
    Test the default initialization of IntegrityError.
    """
    exc = IntegrityError()
    assert exc.message == "Database integrity violation"
    assert exc.details == {}

    with pytest.raises(IntegrityError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Database integrity violation"
    assert isinstance(exc, RepositoryError)


def test_integrity_error_custom():
    """
    Test custom initialization of IntegrityError with custom message and details.
    """
    exc = IntegrityError(
        message="Foreign key constraint failed", details={"fk": "user_id"}
    )
    assert exc.message == "Foreign key constraint failed"
    assert exc.details == {"fk": "user_id"}

    with pytest.raises(IntegrityError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Foreign key constraint failed"


def test_validation_error_default():
    """
    Test the default initialization of ValidationError.
    """
    exc = ValidationError()
    assert exc.message == "Database validation failed"
    assert exc.details == {}

    with pytest.raises(ValidationError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Database validation failed"
    assert isinstance(exc, RepositoryError)


def test_validation_error_custom():
    """
    Test custom initialization of ValidationError with custom message and details.
    """
    exc = ValidationError(message="Invalid data format", details={"field": "username"})
    assert exc.message == "Invalid data format"
    assert exc.details == {"field": "username"}

    with pytest.raises(ValidationError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Invalid data format"


def test_mapping_error_default():
    """
    Test the default initialization of MappingError.
    """
    exc = MappingError()
    assert exc.message == "Failed to map database record"
    assert exc.details == {}

    with pytest.raises(MappingError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Failed to map database record"
    assert isinstance(exc, RepositoryError)


def test_mapping_error_custom():
    """
    Test custom initialization of MappingError with custom message and details.
    """
    exc = MappingError(message="Could not map row to model", details={"row_id": 99})
    assert exc.message == "Could not map row to model"
    assert exc.details == {"row_id": 99}

    with pytest.raises(MappingError) as exc_info:
        raise exc
    assert str(exc_info.value) == "Could not map row to model"
