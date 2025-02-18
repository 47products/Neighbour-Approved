"""
Unit tests for the Transaction Management module.

This module tests:
- The `TransactionManager` class for transaction handling.
- The `transactional` and `async_transactional` decorators.
- The `NestedTransactionManager` class for nested transactions.

Typical usage example:
    pytest tests/unit/test_core/test_transaction_manager.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
    Test that TransactionManager rolls back on error.
    """
    db = MagicMock(spec=AsyncSession)
    manager = TransactionManager(db)

    manager.rollback()
    db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_transaction_manager_async_transaction():
    """
    Test that TransactionManager handles async transactions.
    """
    db = AsyncMock(spec=AsyncSession)
    manager = TransactionManager(db)

    async with manager.transaction():
        pass

    db.begin_nested.assert_called_once()
    db.commit.assert_called_once()
