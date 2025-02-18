"""
Transaction management module for the Neighbour Approved application.

This module provides transaction management utilities and decorators to ensure
data consistency across database operations. It implements both synchronous and
asynchronous transaction handling with proper error management and rollback capabilities.
"""

import asyncio
import inspect
from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from typing import Any, AsyncGenerator, Callable, Generator, cast, Union

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.database_session_management import get_db
from app.core.error_handling import DatabaseError

logger = structlog.get_logger(__name__)

# Allow both synchronous and asynchronous sessions.
DBSessionType = Union[Session, AsyncSession]


class TransactionManager:
    """
    Manages database transactions with automatic commit/rollback handling.
    Supports both synchronous and asynchronous sessions.
    """

    def __init__(self, db: DBSessionType):
        """Initialize with a database session."""
        self.db = db
        self._logger = logger.bind(transaction_id=id(self))

    def commit(self) -> None:
        """Commit the current transaction synchronously."""
        try:
            result = self.db.commit()
            if inspect.isawaitable(result):
                # Run the coroutine if commit is asynchronous.
                asyncio.run(result)
            self._logger.debug("transaction_commit_success")
        except Exception as e:
            self._logger.error("transaction_commit_failed", error=str(e))
            self.rollback()
            raise

    def rollback(self) -> None:
        """Roll back the current transaction synchronously."""
        try:
            result = self.db.rollback()
            if inspect.isawaitable(result):
                asyncio.run(result)
            self._logger.debug("transaction_rollback_success")
        except Exception as e:
            self._logger.error("transaction_rollback_failed", error=str(e))
            raise

    @contextmanager
    def transaction_sync(self) -> Generator[DBSessionType, None, None]:
        """
        Synchronous context manager for handling transactions.
        Uses a try/except/else pattern to avoid duplicate rollback calls.
        """
        try:
            yield self.db
        except Exception:
            self.rollback()
            raise
        else:
            self.commit()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Asynchronous context manager for handling transactions.
        """

        async def _do_rollback():
            try:
                result = self.db.rollback()
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                self._logger.error("rollback_failed", error=str(e))
                raise

        try:
            async with self.db.begin_nested():
                yield self.db
                result = self.db.commit()
                if inspect.isawaitable(result):
                    await result
        except Exception as e:
            await _do_rollback()
            self._logger.error(
                "transaction_failed", error=str(e), error_type=type(e).__name__
            )
            raise


def transactional[T](func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for managing database transactions in synchronous functions.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Accept both Session and AsyncSession.
        from sqlalchemy.ext.asyncio import AsyncSession

        db = next(
            (arg for arg in args if isinstance(arg, (Session, AsyncSession))), None
        )
        if db is None:
            db = kwargs.get("db")
        if db is None:
            db = next(get_db())
            kwargs["db"] = db

        transaction_manager = TransactionManager(db)
        try:
            with transaction_manager.transaction_sync():
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


def async_transactional[T](func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for managing database transactions in asynchronous functions.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        # Accept both Session and AsyncSession.
        from sqlalchemy.ext.asyncio import AsyncSession

        db = next(
            (arg for arg in args if isinstance(arg, (Session, AsyncSession))), None
        )
        if db is None:
            db = kwargs.get("db")
        if db is None:
            db = next(get_db())
            kwargs["db"] = db

        transaction_manager = TransactionManager(db)
        try:
            async with transaction_manager.transaction():
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
    Assumes a synchronous Session.
    """

    def __init__(self, db: Session):
        """Initialize with a database session."""
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
        """
        try:
            self.begin_nested()
            yield self.db
        except Exception as e:
            self.rollback_nested()
            self._logger.error(
                "nested_transaction_failed", error=str(e), error_type=type(e).__name__
            )
            raise
        else:
            self.commit_nested()
