"""
Unit tests for the Transaction Management module.

This module tests:
- The TransactionManager class for transaction handling (both success and failure scenarios).
- The transactional and async_transactional decorators.
- The NestedTransactionManager class for nested transactions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.transaction_manager import (
    TransactionManager,
    transactional,
    async_transactional,
    NestedTransactionManager,
)
from app.core.error_handling import DatabaseError

# ------------------------
# TransactionManager tests
# ------------------------


def test_transaction_manager_commit():
    """
    Test that TransactionManager commits successfully.
    """
    db = MagicMock(spec=AsyncSession)
    manager = TransactionManager(db)
    manager.commit()
    db.commit.assert_called_once()


def test_transaction_manager_rollback():
    """
    Test that TransactionManager rolls back successfully.
    """
    db = MagicMock(spec=AsyncSession)
    manager = TransactionManager(db)
    manager.rollback()
    db.rollback.assert_called_once()


def test_transaction_manager_commit_failure():
    """
    Test that if commit() fails, rollback() is called and the error is raised.
    """
    db = MagicMock(spec=AsyncSession)
    db.commit.side_effect = Exception("commit failed")
    manager = TransactionManager(db)
    with pytest.raises(Exception, match="commit failed"):
        manager.commit()
    db.rollback.assert_called_once()


def test_transaction_manager_rollback_failure():
    """
    Test that if rollback() itself fails, the error is raised.
    """
    db = MagicMock(spec=AsyncSession)
    db.rollback.side_effect = Exception("rollback failed")
    manager = TransactionManager(db)
    with pytest.raises(Exception, match="rollback failed"):
        manager.rollback()


@pytest.mark.asyncio
async def test_transaction_manager_async_transaction():
    """
    Test that TransactionManager handles async transactions successfully.
    """
    db = AsyncMock(spec=AsyncSession)
    # Simulate an async context manager for begin_nested
    db.begin_nested.return_value.__aenter__.return_value = db
    db.begin_nested.return_value.__aexit__.return_value = None

    manager = TransactionManager(db)
    async with manager.transaction():
        pass

    db.begin_nested.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_transaction_manager_async_transaction_failure():
    """
    Test that an exception during async transaction causes a rollback.
    """
    db = AsyncMock(spec=AsyncSession)
    # Set up the async context manager for begin_nested.
    db.begin_nested.return_value.__aenter__.return_value = db
    db.begin_nested.return_value.__aexit__.return_value = None

    # Simulate failure during commit
    db.commit.side_effect = Exception("async commit failed")

    manager = TransactionManager(db)
    with pytest.raises(Exception, match="async commit failed"):
        async with manager.transaction():
            pass

    db.rollback.assert_called_once()


# -------------------------------
# transactional decorator tests
# -------------------------------


# To test the synchronous transactional decorator, we patch
# TransactionManager.transaction with a dummy synchronous context manager.
@contextmanager
def dummy_sync_transaction(self):
    try:
        yield self.db
        self.db.commit()
    except Exception as e:
        self.db.rollback()
        raise


def test_transactional_decorator_success():
    """
    Test that a function decorated with @transactional commits successfully.
    """
    original_transaction = TransactionManager.transaction
    TransactionManager.transaction = dummy_sync_transaction

    dummy_db = MagicMock(spec=Session)
    dummy_db.commit = MagicMock()
    dummy_db.rollback = MagicMock()

    @transactional
    def dummy_func(db):
        # simulate some database operation
        return "success"

    result = dummy_func(dummy_db)
    assert result == "success"
    dummy_db.commit.assert_called_once()

    # Restore the original transaction method.
    TransactionManager.transaction = original_transaction


def test_transactional_decorator_failure():
    """
    Test that a function decorated with @transactional raises a DatabaseError on exception.
    """
    original_transaction = TransactionManager.transaction
    TransactionManager.transaction = dummy_sync_transaction

    dummy_db = MagicMock(spec=Session)
    # Simulate failure during commit within the context manager.
    dummy_db.commit = MagicMock(side_effect=Exception("commit error"))
    dummy_db.rollback = MagicMock()

    @transactional
    def dummy_func(db):
        return "should not reach"

    with pytest.raises(DatabaseError, match="Transaction failed in dummy_func"):
        dummy_func(dummy_db)
    dummy_db.rollback.assert_called_once()

    TransactionManager.transaction = original_transaction


# -----------------------------------
# async_transactional decorator tests
# -----------------------------------


@asynccontextmanager
async def dummy_async_transaction(self):
    try:
        yield self.db
        await self.db.commit()
    except Exception as e:
        await self.db.rollback()
        raise


@pytest.mark.asyncio
async def test_async_transactional_decorator_success():
    """
    Test that a function decorated with @async_transactional commits successfully.
    """
    original_transaction = TransactionManager.transaction
    TransactionManager.transaction = dummy_async_transaction

    dummy_db = AsyncMock(spec=AsyncSession)
    dummy_db.commit = AsyncMock()
    dummy_db.rollback = AsyncMock()

    @async_transactional
    async def dummy_async_func(db):
        return "async success"

    result = await dummy_async_func(dummy_db)
    assert result == "async success"
    dummy_db.commit.assert_awaited_once()

    TransactionManager.transaction = original_transaction


@pytest.mark.asyncio
async def test_async_transactional_decorator_failure():
    """
    Test that a function decorated with @async_transactional raises a DatabaseError on exception.
    """
    original_transaction = TransactionManager.transaction
    TransactionManager.transaction = dummy_async_transaction

    dummy_db = AsyncMock(spec=AsyncSession)
    dummy_db.commit = AsyncMock(side_effect=Exception("async commit error"))
    dummy_db.rollback = AsyncMock()

    @async_transactional
    async def dummy_async_func(db):
        return "should not succeed"

    with pytest.raises(DatabaseError, match="Transaction failed in dummy_async_func"):
        await dummy_async_func(dummy_db)
    dummy_db.rollback.assert_awaited_once()

    TransactionManager.transaction = original_transaction


# ------------------------------
# NestedTransactionManager tests
# ------------------------------


def test_nested_transaction_begin():
    """
    Test that begin_nested() calls the underlying db.begin_nested() and stores the savepoint.
    """
    dummy_db = MagicMock(spec=Session)
    dummy_db.begin_nested.return_value = "savepoint"
    manager = NestedTransactionManager(dummy_db)
    manager.begin_nested()
    dummy_db.begin_nested.assert_called_once()
    assert manager._savepoint == "savepoint"


def test_nested_transaction_commit():
    """
    Test that the nested transaction context manager commits successfully.
    """
    dummy_db = MagicMock(spec=Session)
    dummy_savepoint = MagicMock()
    dummy_db.begin_nested.return_value = dummy_savepoint
    dummy_db.commit = MagicMock()

    manager = NestedTransactionManager(dummy_db)
    with manager.nested_transaction() as session:
        # Simulate operations inside the nested transaction.
        assert session is dummy_db

    dummy_db.begin_nested.assert_called_once()
    dummy_db.commit.assert_called_once()


def test_nested_transaction_rollback():
    """
    Test that an exception within the nested transaction causes a rollback to the savepoint.
    """
    dummy_db = MagicMock(spec=Session)
    dummy_savepoint = MagicMock()
    dummy_db.begin_nested.return_value = dummy_savepoint
    dummy_db.commit = MagicMock(side_effect=Exception("commit failed"))

    manager = NestedTransactionManager(dummy_db)

    with pytest.raises(Exception, match="commit failed"):
        with manager.nested_transaction() as session:
            # Perform operations here if needed. The exception will be triggered on commit.
            pass

    dummy_savepoint.rollback.assert_called_once()


def test_nested_transaction_rollback_failure():
    """
    Test that if the rollback on a nested transaction fails, the exception is raised.
    """
    dummy_db = MagicMock(spec=Session)
    dummy_savepoint = MagicMock()
    dummy_savepoint.rollback.side_effect = Exception("rollback nested failed")
    dummy_db.begin_nested.return_value = dummy_savepoint

    manager = NestedTransactionManager(dummy_db)
    manager.begin_nested()
    with pytest.raises(Exception, match="rollback nested failed"):
        manager.rollback_nested()


def test_commit_with_awaitable():
    """Test commit when db.commit returns an awaitable."""
    dummy_db = MagicMock()
    dummy_db.commit = AsyncMock(return_value=None)
    dummy_db.rollback = MagicMock()
    manager = TransactionManager(dummy_db)
    manager.commit()
    dummy_db.commit.assert_called_once()
    dummy_db.rollback.assert_not_called()


def test_rollback_with_awaitable():
    """Test rollback when db.rollback returns an awaitable."""
    dummy_db = MagicMock()
    dummy_db.rollback = AsyncMock(return_value=None)
    manager = TransactionManager(dummy_db)
    manager.rollback()
    dummy_db.rollback.assert_called_once()


def test_transaction_sync_normal():
    """Test the synchronous transaction context manager with normal execution."""
    dummy_db = MagicMock()
    dummy_db.commit = MagicMock()
    dummy_db.rollback = MagicMock()
    manager = TransactionManager(dummy_db)
    with manager.transaction_sync() as db:
        assert db is dummy_db
    dummy_db.commit.assert_called_once()
    dummy_db.rollback.assert_not_called()


def test_transaction_sync_exception():
    """Test the synchronous transaction context manager when an exception occurs."""
    dummy_db = MagicMock()
    dummy_db.commit = MagicMock()
    dummy_db.rollback = MagicMock()
    manager = TransactionManager(dummy_db)
    with pytest.raises(Exception, match="error"):
        with manager.transaction_sync() as db:
            raise Exception("error")
    dummy_db.rollback.assert_called_once()
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_async_transaction_normal():
    """Test the asynchronous transaction context manager with normal execution."""
    dummy_db = AsyncMock(spec=AsyncSession)
    # Simulate the begin_nested async context manager.
    dummy_db.begin_nested.return_value.__aenter__.return_value = dummy_db
    dummy_db.begin_nested.return_value.__aexit__.return_value = None
    dummy_db.commit = AsyncMock(return_value=None)
    manager = TransactionManager(dummy_db)
    async with manager.transaction() as db:
        assert db is dummy_db
    dummy_db.begin_nested.assert_called_once()
    dummy_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_transaction_exception():
    """Test the asynchronous transaction context manager when commit fails."""
    dummy_db = AsyncMock(spec=AsyncSession)
    dummy_db.begin_nested.return_value.__aenter__.return_value = dummy_db
    dummy_db.begin_nested.return_value.__aexit__.return_value = None
    dummy_db.commit = AsyncMock(side_effect=Exception("async commit error"))
    dummy_db.rollback = AsyncMock(return_value=None)
    manager = TransactionManager(dummy_db)
    with pytest.raises(Exception, match="async commit error"):
        async with manager.transaction() as db:
            pass
    dummy_db.rollback.assert_awaited_once()


# -------------------------
# Tests for the transactional decorator
# -------------------------


def test_transactional_decorator_get_db(monkeypatch):
    """Test the transactional decorator when no db is provided and get_db is used."""
    dummy_db = MagicMock(spec=Session)
    dummy_db.commit = MagicMock()
    dummy_db.rollback = MagicMock()

    def dummy_get_db():
        yield dummy_db

    monkeypatch.setattr("app.core.transaction_manager.get_db", dummy_get_db)

    @transactional
    def dummy_func(db):
        return "got db"

    result = dummy_func()
    assert result == "got db"
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_async_transactional_decorator_get_db(monkeypatch):
    """Test the async transactional decorator when no db is provided and get_db is used."""
    dummy_db = AsyncMock(spec=AsyncSession)
    dummy_db.begin_nested.return_value.__aenter__.return_value = dummy_db
    dummy_db.begin_nested.return_value.__aexit__.return_value = None
    dummy_db.commit = AsyncMock(return_value=None)
    dummy_db.rollback = AsyncMock(return_value=None)

    # For async, get_db returns an iterator.
    monkeypatch.setattr("app.core.transaction_manager.get_db", lambda: iter([dummy_db]))

    @async_transactional
    async def dummy_async_func(db):
        return "got async db"

    result = await dummy_async_func()
    assert result == "got async db"
    dummy_db.commit.assert_awaited_once()


def test_transactional_decorator_http_exception():
    """Test that the transactional decorator re-raises HTTPException without wrapping."""
    dummy_db = MagicMock(spec=Session)
    dummy_db.commit = MagicMock(side_effect=Exception("commit error"))
    dummy_db.rollback = MagicMock()

    @transactional
    def dummy_func(db):
        raise HTTPException(status_code=400, detail="Bad Request")

    with pytest.raises(HTTPException):
        dummy_func(dummy_db)


@pytest.mark.asyncio
async def test_async_transactional_decorator_http_exception():
    """Test that the async transactional decorator re-raises HTTPException without wrapping."""
    dummy_db = AsyncMock(spec=AsyncSession)
    dummy_db.begin_nested.return_value.__aenter__.return_value = dummy_db
    dummy_db.begin_nested.return_value.__aexit__.return_value = None
    dummy_db.commit = AsyncMock(return_value=None)
    dummy_db.rollback = AsyncMock(return_value=None)

    @async_transactional
    async def dummy_async_func(db):
        raise HTTPException(status_code=400, detail="Bad Request")

    with pytest.raises(HTTPException):
        await dummy_async_func(dummy_db)


# -------------------------
# Tests for NestedTransactionManager
# -------------------------


def test_nested_transaction_commit_no_savepoint():
    """Test commit_nested when no savepoint was started (should do nothing)."""
    dummy_db = MagicMock(spec=Session)
    manager = NestedTransactionManager(dummy_db)
    # Call commit_nested without a savepoint; should not call commit.
    manager.commit_nested()
    dummy_db.commit.assert_not_called()


def test_nested_transaction_rollback_no_savepoint():
    """Test rollback_nested when no savepoint was started (should do nothing)."""
    dummy_db = MagicMock(spec=Session)
    manager = NestedTransactionManager(dummy_db)
    # Calling rollback_nested with no savepoint should not throw.
    manager.rollback_nested()


def test_nested_transaction_nested_transaction_rollback_failure():
    """Test that if rollback_nested fails, the exception is propagated."""
    dummy_db = MagicMock(spec=Session)
    dummy_savepoint = MagicMock()
    dummy_savepoint.rollback.side_effect = Exception("rollback nested failed")
    dummy_db.begin_nested.return_value = dummy_savepoint
    manager = NestedTransactionManager(dummy_db)
    with pytest.raises(Exception, match="rollback nested failed"):
        with manager.nested_transaction() as session:
            raise Exception("test error")
