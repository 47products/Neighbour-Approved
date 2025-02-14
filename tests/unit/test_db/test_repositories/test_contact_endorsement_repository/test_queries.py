"""
Unit tests for the Contact Endorsement Repository Queries Mixin.

This module tests the query methods:
    - get_by_contact_and_user
    - get_by_community

Both positive (successful retrieval) and negative (error handling) branches are covered.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.contact_endorsement_repository.repository import (
    ContactEndorsementRepository,
)
from app.db.errors import QueryError
from app.db.models.contact_endorsement_model import ContactEndorsement


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

    A dummy logger is attached and the _model is set to ContactEndorsement.
    """
    repo = ContactEndorsementRepository(dummy_db)
    repo._logger = MagicMock()
    repo._model = ContactEndorsement
    return repo


@pytest.mark.asyncio
async def test_get_by_contact_and_user_success(repository, dummy_db):
    """
    Test successful retrieval of an endorsement by contact and user.
    """
    # Create a dummy endorsement instance.
    dummy_endorsement = ContactEndorsement()
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = dummy_endorsement
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_by_contact_and_user(contact_id=1, user_id=2)
    assert result == dummy_endorsement
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_contact_and_user_failure(repository, dummy_db):
    """
    Test that get_by_contact_and_user raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError(
        "Test error in get_by_contact_and_user"
    )
    with pytest.raises(QueryError) as exc_info:
        await repository.get_by_contact_and_user(contact_id=1, user_id=2)
    assert "Failed to retrieve endorsement by contact and user" in str(exc_info.value)
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_community_success(repository, dummy_db):
    """
    Test successful retrieval of endorsements by community.
    """
    # Create a list of dummy endorsement instances.
    dummy_endorsements = [ContactEndorsement(), ContactEndorsement()]
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = dummy_endorsements
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_by_community(community_id=10, skip=0, limit=10)
    assert isinstance(result, list)
    assert len(result) == len(dummy_endorsements)
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_community_failure(repository, dummy_db):
    """
    Test that get_by_community raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("Test error in get_by_community")
    with pytest.raises(QueryError) as exc_info:
        await repository.get_by_community(community_id=10, skip=0, limit=10)
    assert "Failed to retrieve endorsements by community" in str(exc_info.value)
    dummy_db.execute.assert_called_once()
