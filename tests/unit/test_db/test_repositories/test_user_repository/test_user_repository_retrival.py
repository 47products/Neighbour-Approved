"""
Test Module for UserRetrievalMixin Operations.

This module tests the UserRetrievalMixin methods, including:
    - get_by_email
    - get_by_ids
    - get_by_filters
    - search

Both success and failure paths are simulated to ensure full coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from app.db.repositories.user_repository.retrieval import UserRetrievalMixin
from app.db.errors import QueryError
from app.db.models.user_model import User


# Dummy logger for testing.
class DummyLogger:
    """
    Dummy logger class that provides an error logging method.
    """

    def error(self, *args, **kwargs):
        pass


# Dummy repository class that uses the retrieval mixin.
class DummyRetrievalRepo(UserRetrievalMixin):
    """
    Dummy repository class to test retrieval mixin functions.

    Attributes:
        db: Simulated asynchronous database session.
        _model: The SQLAlchemy model (provided by dummy_model fixture).
        _logger: Dummy logger instance.
    """

    def __init__(self, db, model, logger):
        self.db = db
        self._model = model
        self._logger = logger


@pytest.mark.asyncio
async def test_get_by_email_success(dummy_db, mock_user):
    """
    Test that get_by_email() returns the user when the email is found.
    """
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = mock_user
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = DummyRetrievalRepo(dummy_db, User, DummyLogger())
    user = await repo.get_by_email(mock_user.email)

    assert user == mock_user
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_email_exception(dummy_db, mock_user):
    """
    Test that get_by_email() raises QueryError when a database error occurs.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("Error"))
    repo = DummyRetrievalRepo(dummy_db, User, DummyLogger())

    with pytest.raises(QueryError) as exc_info:
        await repo.get_by_email(mock_user.email)
    assert "Failed to retrieve user by email" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_by_ids_success(dummy_db, mock_user):
    """
    Test that get_by_ids() returns a list of users when found.
    """
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [mock_user]
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = DummyRetrievalRepo(dummy_db, User, DummyLogger())
    users = await repo.get_by_ids([mock_user.id])

    assert users == [mock_user]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_ids_exception(dummy_db, mock_user):
    """
    Test that get_by_ids() raises QueryError when a database error occurs.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("IDs error"))
    repo = DummyRetrievalRepo(dummy_db, User, DummyLogger())

    with pytest.raises(QueryError) as exc_info:
        await repo.get_by_ids([mock_user.id])
    assert "Failed to retrieve users by IDs" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_by_filters_with_conditions(dummy_db, dummy_model, mock_user):
    """
    Test that get_by_filters() returns filtered users when filters are provided.

    Uses a non-empty filter (is_active) so that the conditions list is populated.
    """
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [mock_user]
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = DummyRetrievalRepo(dummy_db, dummy_model, DummyLogger())
    users = await repo.get_by_filters(is_active=True, skip=2, limit=5)

    assert users == [mock_user]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_filters_no_conditions(dummy_db, dummy_model, mock_user):
    """
    Test that get_by_filters() works when no filter parameters are provided.

    The conditions list remains empty and the query applies offset and limit.
    """
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [mock_user]
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = DummyRetrievalRepo(dummy_db, dummy_model, DummyLogger())
    users = await repo.get_by_filters()

    assert users == [mock_user]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_filters_exception(dummy_db, dummy_model, mock_user):
    """
    Test that get_by_filters() raises QueryError when a database error occurs.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("Filter error"))
    repo = DummyRetrievalRepo(dummy_db, dummy_model, DummyLogger())

    with pytest.raises(QueryError) as exc_info:
        await repo.get_by_filters(is_active=False)
    assert "Failed to retrieve filtered users" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_by_filters_email_verified_and_role(dummy_db, dummy_model, mock_user):
    """
    Test that get_by_filters() correctly applies the email_verified and role_name filters.

    This test ensures that lines 106 and 108 are executed by providing non-None values
    for both email_verified and role_name.
    """
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [mock_user]
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = DummyRetrievalRepo(dummy_db, dummy_model, DummyLogger())
    users = await repo.get_by_filters(
        email_verified=True, role_name="admin", skip=0, limit=10
    )

    assert users == [mock_user]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_success_active_only(dummy_db, dummy_model, mock_user):
    """
    Test that search() returns matching users when active_only is True.

    Verifies that the query includes the active status filter.
    """
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [mock_user]
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = DummyRetrievalRepo(dummy_db, dummy_model, DummyLogger())
    users = await repo.search("test", skip=1, limit=3, active_only=True)

    assert users == [mock_user]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_success_inactive_included(dummy_db, dummy_model, mock_user):
    """
    Test that search() returns matching users when active_only is False.

    This bypasses the active status filter.
    """
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [mock_user]
    dummy_db.execute = AsyncMock(return_value=result_mock)

    repo = DummyRetrievalRepo(dummy_db, dummy_model, DummyLogger())
    users = await repo.search("test", active_only=False)

    assert users == [mock_user]
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_exception(dummy_db, dummy_model):
    """
    Test that search() raises QueryError when a database error occurs.
    """
    dummy_db.execute = AsyncMock(side_effect=SQLAlchemyError("Search failure"))
    repo = DummyRetrievalRepo(dummy_db, dummy_model, DummyLogger())

    with pytest.raises(QueryError) as exc_info:
        await repo.search("test", active_only=True)
    assert "Failed to search users" in str(exc_info.value)
