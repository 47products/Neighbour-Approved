"""
Test Module for UserRepository Core Operations.

This module tests the core CRUD operations provided by the UserRepository,
including create, get, update, delete, exists, and count methods. The tests
simulate both positive and negative scenarios using dummy database fixtures.

Typical usage example:
    $ pytest tests/unit/test_db/test_repositories/test_user_repository/test_user_repository.py

Dependencies:
    - pytest
    - unittest.mock's AsyncMock and MagicMock
    - SQLAlchemyError for simulating database errors
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError, IntegrityError as SAIntegrityError

from app.db.repositories.user_repository.user_repository import UserRepository
from app.db.errors import QueryError, IntegrityError
from app.db.models.user_model import User


# Dummy schema class to simulate a Pydantic model with a model_dump() method.
class DummySchema:
    """
    Dummy schema for simulating user creation or update data.

    Attributes:
        _data (dict): The underlying data for the schema.
    """

    def __init__(self, data: dict):
        self._data = data

    def model_dump(self, **kwargs) -> dict:
        """
        Dump the underlying data as a dictionary.

        Accepts arbitrary keyword arguments (e.g. exclude_unset) for compatibility.

        Returns:
            dict: The data dictionary.
        """
        return self._data


@pytest.mark.asyncio
async def test_create_user_success(dummy_db, mock_user):
    """
    Test that create() successfully creates a user record.

    Verifies that flush, refresh, and commit are invoked.
    """
    dummy_db.flush = AsyncMock()
    dummy_db.refresh = AsyncMock(return_value=mock_user)
    dummy_db.commit = AsyncMock()

    schema = DummySchema(
        {"id": mock_user.id, "email": mock_user.email, "is_active": mock_user.is_active}
    )
    repo = UserRepository(db=dummy_db)
    created_user = await repo.create(schema)

    assert created_user.email == mock_user.email
    dummy_db.commit.assert_called_once()
    dummy_db.flush.assert_called_once()
    dummy_db.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_integrity_error(dummy_db, mock_user):
    """
    Test that create() raises an IntegrityError on unique constraint violation.

    Simulates a failure during flush.
    """
    dummy_db.flush = AsyncMock(
        side_effect=SAIntegrityError("Integrity Error", {}, None)
    )
    dummy_db.rollback = AsyncMock()

    schema = DummySchema(
        {"id": mock_user.id, "email": mock_user.email, "is_active": mock_user.is_active}
    )
    repo = UserRepository(db=dummy_db)

    with pytest.raises(IntegrityError):
        await repo.create(schema)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_success(dummy_db, mock_user):
    """
    Test that get() returns the user when found.
    """
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_user
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = UserRepository(db=dummy_db)
    user = await repo.get(mock_user.id)

    assert user == mock_user
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_failure(dummy_db, mock_user):
    """
    Test that get() raises a QueryError when a database error occurs.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("DB error"))
    repo = UserRepository(db=dummy_db)

    with pytest.raises(QueryError):
        await repo.get(mock_user.id)


@pytest.mark.asyncio
async def test_update_user_success(dummy_db, mock_user):
    """
    Test that update() successfully updates a user record.

    Verifies that the updated email is set and commit and refresh are called.
    """
    repo = UserRepository(db=dummy_db)
    repo.get = AsyncMock(return_value=mock_user)
    dummy_db.commit = AsyncMock()
    dummy_db.refresh = AsyncMock(return_value=mock_user)

    new_email = "new_email@example.com"
    schema = DummySchema({"email": new_email})
    updated_user = await repo.update(id=mock_user.id, schema=schema)

    assert updated_user.email == new_email
    dummy_db.commit.assert_called_once()
    dummy_db.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_not_found(dummy_db, mock_user):
    """
    Test that update() raises an error when the user is not found.

    Simulates get() returning None.
    """
    repo = UserRepository(db=dummy_db)
    repo.get = AsyncMock(return_value=None)

    schema = DummySchema({"email": "update@example.com"})

    with pytest.raises(
        Exception
    ):  # Replace Exception with RecordNotFoundError if available
        await repo.update(id=999, schema=schema)


@pytest.mark.asyncio
async def test_delete_user_success(dummy_db, mock_user):
    """
    Test that delete() returns True when deletion is successful.
    """
    result_mock = MagicMock()
    result_mock.rowcount = 1
    dummy_db.execute = AsyncMock(return_value=result_mock)
    dummy_db.commit = AsyncMock()

    repo = UserRepository(db=dummy_db)
    success = await repo.delete(mock_user.id)

    assert success is True
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_failure(dummy_db, mock_user):
    """
    Test that delete() raises an error when deletion fails.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("DB error"))
    dummy_db.rollback = AsyncMock()

    repo = UserRepository(db=dummy_db)
    with pytest.raises(
        Exception
    ):  # Replace Exception with TransactionError if available
        await repo.delete(mock_user.id)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_exists_user(dummy_db, mock_user):
    """
    Test that exists() returns True when the user exists.
    """
    result_mock = MagicMock()
    result_mock.scalar.return_value = 1
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = UserRepository(db=dummy_db)
    exists = await repo.exists(mock_user.id)
    assert exists is True


@pytest.mark.asyncio
async def test_count_users(dummy_db, mock_user):
    """
    Test that count() returns the correct number of user records.
    """
    result_mock = MagicMock()
    result_mock.scalar.return_value = 5
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = UserRepository(db=dummy_db)
    count = await repo.count()
    assert count == 5
