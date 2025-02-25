"""
Unit tests for contact endorsement operations.

This module tests methods to retrieve endorsement statistics and update
a contact's endorsement metrics.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.contact_repository.repository import ContactRepository
from app.db.errors import QueryError, IntegrityError


@pytest.fixture
def dummy_db():
    """Returns a dummy DB session with async methods."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def repository(dummy_db):
    """
    Creates a ContactRepository instance for endorsement operations testing.

    Assigns a dummy logger.
    """
    repo = ContactRepository(dummy_db)
    repo._logger = MagicMock()
    return repo


# A simple dummy row class to simulate SQLAlchemy row objects
class DummyRow:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.mark.asyncio
async def test_get_endorsement_stats_success(repository, dummy_db):
    """
    Test that get_endorsement_stats returns correct statistics.

    Simulates two queries: one for basic stats and one for rating distribution.
    """
    # Dummy result for the basic stats query.
    dummy_stats = DummyRow(total=5, verified=3, average_rating=4.2)
    dummy_result_stats = MagicMock()
    dummy_result_stats.one.return_value = dummy_stats

    # Dummy rating row.
    dummy_rating_row = DummyRow(rating=5, count=3)
    # Simulate that the second execute returns an iterable (list) of dummy rows.
    dummy_result_ratings = [dummy_rating_row]

    # Set side effects for successive calls to db.execute.
    dummy_db.execute.side_effect = [dummy_result_stats, dummy_result_ratings]

    stats = await repository.get_endorsement_stats(1)
    assert stats["total_endorsements"] == 5
    assert stats["verified_endorsements"] == 3
    assert stats["average_rating"] == 4.2
    assert stats["rating_distribution"] == {5: 3}
    assert dummy_db.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_endorsement_stats_failure(repository, dummy_db):
    """Test that a failure in get_endorsement_stats raises a QueryError."""
    dummy_db.execute.side_effect = SQLAlchemyError("Test error")
    with pytest.raises(QueryError):
        await repository.get_endorsement_stats(1)


@pytest.mark.asyncio
async def test_update_endorsement_metrics_success(repository, dummy_db):
    """Test that update_endorsement_metrics commits successfully."""
    # Simulate get_endorsement_stats returning valid data.
    repository.get_endorsement_stats = AsyncMock(
        return_value={
            "total_endorsements": 5,
            "verified_endorsements": 3,
            "average_rating": 4.2,
            "rating_distribution": {5: 3},
        }
    )
    await repository.update_endorsement_metrics(1)
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_endorsement_metrics_failure(repository, dummy_db):
    """Test that a failure during update_endorsement_metrics triggers a rollback."""
    repository.get_endorsement_stats = AsyncMock(
        side_effect=SQLAlchemyError("Test error")
    )
    with pytest.raises(IntegrityError):
        await repository.update_endorsement_metrics(1)
    dummy_db.rollback.assert_called_once()
