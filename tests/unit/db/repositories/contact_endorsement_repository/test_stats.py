"""
Unit tests for the Contact Endorsement Repository Statistics Mixin.

This module tests the get_stats method, which aggregates endorsement statistics.
Both positive and negative branches are covered.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.contact_endorsement_repository.repository import (
    ContactEndorsementRepository,
)
from app.db.errors import QueryError
from app.db.models.contact_endorsement_model import ContactEndorsement


class DummyStats:
    """
    Dummy class to simulate a row returned by SQLAlchemy with aggregated stats.
    """

    def __init__(self, total, verified, average_rating):
        self.total = total
        self.verified = verified
        self.average_rating = average_rating


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

    A dummy logger is attached and _model is set for testing.
    """
    repo = ContactEndorsementRepository(dummy_db)
    repo._logger = MagicMock()
    repo._model = ContactEndorsement
    return repo


@pytest.mark.asyncio
async def test_get_stats_success(repository, dummy_db):
    """
    Test that get_stats returns correct aggregated statistics for a contact.
    """
    # Create a dummy stats object.
    dummy_stats = DummyStats(total=5, verified=3, average_rating=4.2)
    dummy_result = MagicMock()
    dummy_result.one.return_value = dummy_stats
    dummy_db.execute.return_value = dummy_result

    stats = await repository.get_stats(contact_id=1)
    assert stats["total"] == 5
    assert stats["verified"] == 3
    assert stats["average_rating"] == 4.2
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_stats_success_no_average(repository, dummy_db):
    """
    Test that get_stats returns None for average_rating when no rating is present.
    """
    dummy_stats = DummyStats(total=2, verified=1, average_rating=None)
    dummy_result = MagicMock()
    dummy_result.one.return_value = dummy_stats
    dummy_db.execute.return_value = dummy_result

    stats = await repository.get_stats(contact_id=1)
    assert stats["total"] == 2
    assert stats["verified"] == 1
    assert stats["average_rating"] is None
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_stats_failure(repository, dummy_db):
    """
    Test that get_stats raises a QueryError when a SQLAlchemyError occurs.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("Test error in get_stats")
    with pytest.raises(QueryError) as exc_info:
        await repository.get_stats(contact_id=1)
    assert "Failed to retrieve contact endorsement stats" in str(exc_info.value)
    dummy_db.execute.assert_called_once()
