"""
Test Module for UserRepository Update Operations.

This module tests the update mixin functions from the UserUpdatesMixin,
including update_last_login, update_status, and bulk_update_status, covering both
successful operations and error scenarios.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.db.repositories.user_repository.updates import UserUpdatesMixin
from app.db.errors import IntegrityError


class DummyUpdatesRepo(UserUpdatesMixin):
    """
    Dummy repository class for testing update operations.

    Attributes:
        db: Simulated asynchronous database session.
        _model: Dummy model containing a __table__ attribute.
        _logger: Dummy logger instance.
    """

    def __init__(self, db, model, logger):
        self.db = db
        self._model = model
        self._logger = logger


class DummyModel:
    """
    Dummy model class with an id attribute and __table__ attribute for update operations.

    The id attribute is a MagicMock that simulates a SQLAlchemy column expression,
    allowing the use of the in_() operator.
    """

    def __init__(self):
        self.id = MagicMock()
        self.__table__ = MagicMock()


class DummyLogger:
    """
    Dummy logger class that provides an error logging method.
    """

    def error(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_update_last_login_success(dummy_db, mock_user):
    """
    Test that update_last_login() successfully updates the login timestamp.
    """
    dummy_db.execute = AsyncMock(return_value=MagicMock())
    dummy_db.commit = AsyncMock()

    repo = DummyUpdatesRepo(dummy_db, DummyModel(), DummyLogger())
    await repo.update_last_login(mock_user.id, "2025-02-14T00:00:00Z")

    dummy_db.execute.assert_called_once()
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_last_login_failure(dummy_db, mock_user):
    """
    Test that update_last_login() raises an IntegrityError when a database error occurs.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("Error"))
    dummy_db.rollback = AsyncMock()

    repo = DummyUpdatesRepo(dummy_db, DummyModel(), DummyLogger())
    with pytest.raises(IntegrityError):
        await repo.update_last_login(mock_user.id, "2025-02-14T00:00:00Z")

    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_update_status_success(dummy_db, mock_user):
    """
    Test that update_status() successfully updates the user's active status.
    """
    dummy_db.execute = AsyncMock(return_value=MagicMock())
    dummy_db.commit = AsyncMock()

    repo = DummyUpdatesRepo(dummy_db, DummyModel(), DummyLogger())
    await repo.update_status(mock_user.id, False)

    dummy_db.execute.assert_called_once()
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_status_failure(dummy_db, mock_user):
    """
    Test that update_status() raises an IntegrityError when a database error occurs.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("Status update error"))
    dummy_db.rollback = AsyncMock()

    repo = DummyUpdatesRepo(dummy_db, DummyModel(), DummyLogger())
    with pytest.raises(IntegrityError):
        await repo.update_status(mock_user.id, False)

    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_update_status_success(dummy_db, mock_user):
    """
    Test that bulk_update_status() returns the correct number of updated rows.
    """
    result_mock = MagicMock()
    result_mock.rowcount = 2
    dummy_db.execute = AsyncMock(return_value=result_mock)
    dummy_db.commit = AsyncMock()

    repo = DummyUpdatesRepo(dummy_db, DummyModel(), DummyLogger())
    count = await repo.bulk_update_status([mock_user.id, 2], False)

    assert count == 2
    dummy_db.execute.assert_called_once()
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_update_status_failure(dummy_db, mock_user):
    """
    Test that bulk_update_status() raises an IntegrityError when a database error occurs.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("Bulk update error"))
    dummy_db.rollback = AsyncMock()

    repo = DummyUpdatesRepo(dummy_db, DummyModel(), DummyLogger())
    with pytest.raises(IntegrityError):
        await repo.bulk_update_status([mock_user.id], False)

    dummy_db.rollback.assert_called_once()
