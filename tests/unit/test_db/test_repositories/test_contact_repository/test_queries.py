"""
Unit tests for contact query operations.

This module tests the query-related mixin methods:
    - get_by_email
    - get_with_relationships
    - get_by_user
    - search_contacts
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.contact_repository.repository import ContactRepository
from app.db.errors import QueryError


# Dummy contact model for testing purposes
class DummyContact:
    def __init__(self, id, email, contact_name="Test Contact"):
        self.id = id
        self.email = email
        self.contact_name = contact_name
        self.primary_contact_first_name = "First"
        self.primary_contact_last_name = "Last"
        self.is_active = True


@pytest.fixture
def dummy_db():
    """Fixture that returns a dummy database session with async methods."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def repository(dummy_db):
    """
    Fixture that creates a ContactRepository instance with a dummy DB session.

    Also assigns a dummy logger to capture log calls.
    """
    repo = ContactRepository(dummy_db)
    repo._logger = MagicMock()
    return repo


@pytest.mark.asyncio
async def test_get_by_email_success(repository, dummy_db):
    """Test successful retrieval of a contact by email."""
    dummy_contact = DummyContact(id=1, email="test@example.com")
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = dummy_contact
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_by_email("test@example.com")
    assert result == dummy_contact
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_email_failure(repository, dummy_db):
    """Test that a SQLAlchemyError is caught and re-raised as a QueryError."""
    dummy_db.execute.side_effect = SQLAlchemyError("Test error")
    with pytest.raises(QueryError) as exc_info:
        await repository.get_by_email("fail@example.com")
    assert "Failed to retrieve contact by email" in str(exc_info.value)
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_with_relationships_success(repository, dummy_db):
    """Test successful retrieval of a contact with relationships loaded."""
    dummy_contact = DummyContact(id=2, email="rel@example.com")
    dummy_result = MagicMock()
    dummy_result.scalar_one_or_none.return_value = dummy_contact
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_with_relationships(2)
    assert result == dummy_contact
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_user_success(repository, dummy_db):
    """Test retrieval of contacts for a given user ID."""
    dummy_contact1 = DummyContact(id=1, email="user1@example.com")
    dummy_contact2 = DummyContact(id=2, email="user2@example.com")
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [
        dummy_contact1,
        dummy_contact2,
    ]
    dummy_db.execute.return_value = dummy_result

    result = await repository.get_by_user(123)
    assert isinstance(result, list)
    assert len(result) == 2
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_contacts_success(repository, dummy_db):
    """Test that searching contacts returns a list of matching contacts."""
    dummy_contact = DummyContact(id=3, email="search@example.com")
    dummy_result = MagicMock()
    dummy_result.scalars.return_value.all.return_value = [dummy_contact]
    dummy_db.execute.return_value = dummy_result

    result = await repository.search_contacts("search", skip=0, limit=10)
    assert isinstance(result, list)
    assert len(result) == 1
    dummy_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_with_relationships_failure(repository, dummy_db):
    """
    Test that get_with_relationships raises a QueryError when a SQLAlchemyError occurs.

    This covers the error branch (lines ~121–123) in get_with_relationships.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("Test error in relationships")
    with pytest.raises(QueryError) as exc_info:
        await repository.get_with_relationships(42)
    assert "Failed to retrieve contact with relationships" in str(exc_info.value)
    repository._logger.error.assert_called_once_with(
        "get_with_relationships_failed",
        contact_id=42,
        error="Test error in relationships",
    )


@pytest.mark.asyncio
async def test_get_by_user_failure(repository, dummy_db):
    """
    Test that get_by_user raises a QueryError when a SQLAlchemyError occurs.

    This covers the error branch in get_by_user.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("Test error in get_by_user")
    with pytest.raises(QueryError) as exc_info:
        await repository.get_by_user(99)
    assert "Failed to retrieve user contacts" in str(exc_info.value)
    repository._logger.error.assert_called_once_with(
        "get_by_user_failed", user_id=99, error="Test error in get_by_user"
    )


@pytest.mark.asyncio
async def test_search_contacts_failure_with_filters(repository, dummy_db):
    """
    Test that search_contacts raises a QueryError when a SQLAlchemyError occurs
    while using optional filters.

    This covers the building of conditions (lines ~170–177) and the error branch (lines 188–192).
    """
    # Configure the dummy DB to raise an error on execute.
    dummy_db.execute.side_effect = SQLAlchemyError("Test error in search_contacts")

    with pytest.raises(QueryError) as exc_info:
        # Call search_contacts with several filters (active_only is True by default)
        await repository.search_contacts(
            "test", category_id=1, service_id=2, community_id=3
        )

    assert "Failed to search contacts" in str(exc_info.value)
    repository._logger.error.assert_called_once_with(
        "search_contacts_failed",
        search_term="test",
        error="Test error in search_contacts",
    )


@pytest.mark.asyncio
async def test_search_contacts_failure_active_only_false(repository, dummy_db):
    """
    Test that search_contacts raises a QueryError when a SQLAlchemyError occurs
    even if active_only is set to False.

    This ensures that the error branch is reached regardless of the active_only flag.
    """
    dummy_db.execute.side_effect = SQLAlchemyError("Test error with active_only False")

    with pytest.raises(QueryError) as exc_info:
        await repository.search_contacts("sample", active_only=False)

    assert "Failed to search contacts" in str(exc_info.value)
    repository._logger.error.assert_called_once_with(
        "search_contacts_failed",
        search_term="sample",
        error="Test error with active_only False",
    )
