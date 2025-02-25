"""
Unit tests for the Contact Endorsement Repository Deletion Mixin.

This module tests the delete_by_contact_and_user method, which deletes an endorsement.
Both positive (successful deletion) and negative (error handling) branches are covered.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import column

from app.db.repositories.contact_endorsement_repository.repository import (
    ContactEndorsementRepository,
)
from app.db.errors import IntegrityError


class DummyTable:
    """
    Dummy table class to simulate a SQLAlchemy Table.
    """

    def delete(self):
        # Return a dummy statement object that supports .where()
        stmt = MagicMock(name="stmt")
        stmt.where = MagicMock(return_value=stmt)
        return stmt


class DummyModel:
    """
    Dummy model class to simulate a SQLAlchemy model with proper columns.
    """

    # Use SQLAlchemy's column() to create ColumnElement objects.
    contact_id = column("contact_id")
    user_id = column("user_id")
    __table__ = DummyTable()


@pytest.fixture
def dummy_db():
    """
    Fixture that returns a dummy database session with async methods.
    """
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def repository(dummy_db):
    """
    Fixture that returns a ContactEndorsementRepository instance with a dummy DB session.

    A dummy logger is attached and _model is set to DummyModel.
    """
    repo = ContactEndorsementRepository(dummy_db)
    repo._logger = MagicMock()
    repo._model = DummyModel
    return repo


@pytest.mark.asyncio
async def test_delete_by_contact_and_user_success(repository, dummy_db):
    """
    Test that delete_by_contact_and_user returns True when deletion is successful.
    """
    # Create a dummy result with rowcount > 0.
    dummy_result = MagicMock()
    dummy_result.rowcount = 1
    dummy_db.execute.return_value = dummy_result

    result = await repository.delete_by_contact_and_user(contact_id=1, user_id=2)
    assert result is True
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_by_contact_and_user_no_rows(repository, dummy_db):
    """
    Test that delete_by_contact_and_user returns False when no rows are deleted.
    """
    dummy_result = MagicMock()
    dummy_result.rowcount = 0
    dummy_db.execute.return_value = dummy_result

    result = await repository.delete_by_contact_and_user(contact_id=1, user_id=2)
    assert result is False
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_by_contact_and_user_failure(repository, dummy_db):
    """
    Test that delete_by_contact_and_user raises an IntegrityError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("Test deletion error")
    with pytest.raises(IntegrityError) as exc_info:
        await repository.delete_by_contact_and_user(contact_id=1, user_id=2)
    assert "Failed to delete endorsement" in str(exc_info.value)
    dummy_db.rollback.assert_called_once()
