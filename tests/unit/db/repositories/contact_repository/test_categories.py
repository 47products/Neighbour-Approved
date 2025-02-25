"""
Unit tests for contact-category relationship operations.

This module tests methods to add and remove categories from a contact.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.contact_repository.repository import ContactRepository
from app.db.errors import IntegrityError


# Dummy classes for contact and category
class DummyContact:
    def __init__(self, id):
        self.id = id
        self.categories = []


class DummyCategory:
    def __init__(self, id):
        self.id = id


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
    Creates a ContactRepository instance for testing category operations.

    Overrides the `get` method to simulate contact retrieval.
    """
    repo = ContactRepository(dummy_db)
    repo._logger = MagicMock()
    repo.get = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_add_category_success(repository, dummy_db):
    """Test successfully adding a category to a contact."""
    dummy_contact = DummyContact(id=1)
    dummy_category = DummyCategory(id=201)

    repository.get.return_value = dummy_contact
    dummy_db.get.return_value = dummy_category

    result = await repository.add_category(1, 201)
    assert result is True
    assert dummy_category in dummy_contact.categories
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_category_already_exists(repository, dummy_db):
    """Test that adding an already-associated category returns False."""
    dummy_contact = DummyContact(id=1)
    dummy_category = DummyCategory(id=201)
    dummy_contact.categories.append(dummy_category)

    repository.get.return_value = dummy_contact
    dummy_db.get.return_value = dummy_category

    result = await repository.add_category(1, 201)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_add_category_failure(repository, dummy_db):
    """Test that a database error during add_category is handled correctly."""
    repository.get.side_effect = SQLAlchemyError("Test error")
    with pytest.raises(IntegrityError):
        await repository.add_category(1, 201)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_remove_category_success(repository, dummy_db):
    """Test successfully removing a category from a contact."""
    dummy_contact = DummyContact(id=1)
    dummy_category = DummyCategory(id=201)
    dummy_contact.categories.append(dummy_category)

    repository.get.return_value = dummy_contact
    dummy_db.get.return_value = dummy_category

    result = await repository.remove_category(1, 201)
    assert result is True
    assert dummy_category not in dummy_contact.categories
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_remove_category_not_found(repository, dummy_db):
    """Test that removing a non-associated category returns False."""
    dummy_contact = DummyContact(id=1)
    dummy_category = DummyCategory(id=201)

    repository.get.return_value = dummy_contact
    dummy_db.get.return_value = dummy_category

    result = await repository.remove_category(1, 201)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_remove_category_failure(repository, dummy_db):
    """Test that a database error during remove_category is handled correctly."""
    repository.get.side_effect = SQLAlchemyError("Test error")
    with pytest.raises(IntegrityError):
        await repository.remove_category(1, 201)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_add_category_no_contact(repository, dummy_db):
    """
    Test that add_category returns False when the contact is not found.

    This covers the branch where 'if not contact or not category:' returns False.
    """
    # Simulate contact not found.
    repository.get.return_value = None
    # Simulate that the category is found.
    dummy_db.get.return_value = DummyCategory(id=201)

    result = await repository.add_category(1, 201)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_add_category_no_category(repository, dummy_db):
    """
    Test that add_category returns False when the category is not found.

    This covers the branch where a valid contact is retrieved but the category is missing.
    """
    dummy_contact = DummyContact(id=1)
    repository.get.return_value = dummy_contact  # Contact exists.
    dummy_db.get.return_value = None  # Category not found.

    result = await repository.add_category(1, 201)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_remove_category_no_contact(repository, dummy_db):
    """
    Test that remove_category returns False when the contact is not found.

    This covers the branch where the contact does not exist.
    """
    # Simulate contact not found.
    repository.get.return_value = None
    dummy_db.get.return_value = DummyCategory(id=201)

    result = await repository.remove_category(1, 201)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_remove_category_no_category(repository, dummy_db):
    """
    Test that remove_category returns False when the category is not found.

    This covers the branch where a valid contact is retrieved but the category is missing.
    """
    dummy_contact = DummyContact(id=1)
    repository.get.return_value = dummy_contact  # Contact exists.
    dummy_db.get.return_value = None  # Category not found.

    result = await repository.remove_category(1, 201)
    assert result is False
    dummy_db.commit.assert_not_called()
