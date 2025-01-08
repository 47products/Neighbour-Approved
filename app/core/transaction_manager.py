"""
Transaction management module for the Neighbour Approved application.

This module provides transaction management utilities and decorators to ensure
data consistency across database operations. It implements both synchronous
and asynchronous transaction handling with proper error management and rollback
capabilities.
"""

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Generator, TypeVar, cast
from fastapi import HTTPException
from sqlalchemy.orm import Session
import structlog

from app.db.database_session_management import get_db
from app.core.error_handling import DatabaseError

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class TransactionManager:
    """
    Manages database transactions with automatic commit/rollback handling.

    This class provides methods for managing database transactions, ensuring
    proper handling of commits and rollbacks, and maintaining transaction
    isolation levels.
    """

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self._logger = logger.bind(transaction_id=id(self))

    def begin(self) -> None:
        """Begin a new transaction."""
        self._logger.debug("transaction_begin")
        self.db.begin()

    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.db.commit()
            self._logger.debug("transaction_commit_success")
        except Exception as e:
            self._logger.error("transaction_commit_failed", error=str(e))
            self.rollback()
            raise

    def rollback(self) -> None:
        """Roll back the current transaction."""
        try:
            self.db.rollback()
            self._logger.debug("transaction_rollback_success")
        except Exception as e:
            self._logger.error("transaction_rollback_failed", error=str(e))
            raise

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        Context manager for handling transactions.

        Usage:
            with TransactionManager(db).transaction() as session:
                session.add(some_object)
        """
        try:
            self.begin()
            yield self.db
            self.commit()
        except Exception as e:
            self.rollback()
            self._logger.error(
                "transaction_failed", error=str(e), error_type=type(e).__name__
            )
            raise


def transactional(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for managing database transactions in synchronous functions.

    Usage:
        @transactional
        def create_user(db: Session, user_data: dict) -> User:
            user = User(**user_data)
            db.add(user)
            return user
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        db = next((arg for arg in args if isinstance(arg, Session)), None)
        if db is None:
            db = kwargs.get("db")

        if db is None:
            db = next(get_db())
            kwargs["db"] = db

        transaction_manager = TransactionManager(db)

        try:
            with transaction_manager.transaction():
                result = func(*args, **kwargs)
                return result
        except Exception as e:
            logger.error(
                "transaction_error",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            if isinstance(e, HTTPException):
                raise
            raise DatabaseError(
                f"Transaction failed in {func.__name__}: {str(e)}"
            ) from e

    return cast(Callable[..., T], wrapper)


async def async_transactional(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for managing database transactions in asynchronous functions.

    Usage:
        @async_transactional
        async def create_user(db: Session, user_data: dict) -> User:
            user = User(**user_data)
            db.add(user)
            return user
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        db = next((arg for arg in args if isinstance(arg, Session)), None)
        if db is None:
            db = kwargs.get("db")

        if db is None:
            db = next(get_db())
            kwargs["db"] = db

        transaction_manager = TransactionManager(db)

        try:
            with transaction_manager.transaction():
                result = await func(*args, **kwargs)
                return result
        except Exception as e:
            logger.error(
                "async_transaction_error",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )
            if isinstance(e, HTTPException):
                raise
            raise DatabaseError(
                f"Transaction failed in {func.__name__}: {str(e)}"
            ) from e

    return cast(Callable[..., T], wrapper)


class NestedTransactionManager:
    """
    Manages nested transactions with proper savepoint handling.

    This class provides support for nested transactions using SQLAlchemy's
    savepoint functionality, allowing for more complex transaction patterns
    while maintaining data consistency.
    """

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self._logger = logger.bind(nested_transaction_id=id(self))
        self._savepoint = None

    def begin_nested(self) -> None:
        """Begin a new nested transaction with a savepoint."""
        self._logger.debug("nested_transaction_begin")
        self._savepoint = self.db.begin_nested()

    def commit_nested(self) -> None:
        """Commit the current nested transaction."""
        if self._savepoint is not None:
            try:
                self.db.commit()
                self._logger.debug("nested_transaction_commit_success")
            except Exception as e:
                self._logger.error("nested_transaction_commit_failed", error=str(e))
                self.rollback_nested()
                raise

    def rollback_nested(self) -> None:
        """Roll back to the last savepoint."""
        if self._savepoint is not None:
            try:
                self._savepoint.rollback()
                self._logger.debug("nested_transaction_rollback_success")
            except Exception as e:
                self._logger.error("nested_transaction_rollback_failed", error=str(e))
                raise

    @contextmanager
    def nested_transaction(self) -> Generator[Session, None, None]:
        """
        Context manager for handling nested transactions.

        Usage:
            with NestedTransactionManager(db).nested_transaction() as session:
                session.add(some_object)
        """
        try:
            self.begin_nested()
            yield self.db
            self.commit_nested()
        except Exception as e:
            self.rollback_nested()
            self._logger.error(
                "nested_transaction_failed", error=str(e), error_type=type(e).__name__
            )
            raise
