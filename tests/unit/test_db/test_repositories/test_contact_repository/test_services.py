"""
Unit tests for contact-service relationship operations.

This module tests methods to add and remove services from a contact.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.contact_repository.repository import ContactRepository
from app.db.errors import IntegrityError


# Dummy classes for contact and service
class DummyContact:
    def __init__(self, id):
        self.id = id
        self.services = []


class DummyService:
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
    Creates a ContactRepository instance for testing service operations.

    Overrides the `get` method to allow simulating contact retrieval.
    """
    repo = ContactRepository(dummy_db)
    repo._logger = MagicMock()
    repo.get = AsyncMock()  # Override get for our tests
    return repo


@pytest.mark.asyncio
async def test_add_service_success(repository, dummy_db):
    """Test successfully adding a service to a contact."""
    dummy_contact = DummyContact(id=1)
    dummy_service = DummyService(id=101)

    repository.get.return_value = dummy_contact
    dummy_db.get.return_value = dummy_service

    # Service is not in contact.services initially.
    result = await repository.add_service(1, 101)
    assert result is True
    assert dummy_service in dummy_contact.services
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_service_already_exists(repository, dummy_db):
    """Test that adding an already-associated service returns False."""
    dummy_contact = DummyContact(id=1)
    dummy_service = DummyService(id=101)
    dummy_contact.services.append(dummy_service)

    repository.get.return_value = dummy_contact
    dummy_db.get.return_value = dummy_service

    result = await repository.add_service(1, 101)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_add_service_failure(repository, dummy_db):
    """Test that a database error during add_service is handled correctly."""
    repository.get.side_effect = SQLAlchemyError("Test error")
    with pytest.raises(IntegrityError):
        await repository.add_service(1, 101)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_remove_service_success(repository, dummy_db):
    """Test successfully removing a service from a contact."""
    dummy_contact = DummyContact(id=1)
    dummy_service = DummyService(id=101)
    dummy_contact.services.append(dummy_service)

    repository.get.return_value = dummy_contact
    dummy_db.get.return_value = dummy_service

    result = await repository.remove_service(1, 101)
    assert result is True
    assert dummy_service not in dummy_contact.services
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_remove_service_not_found(repository, dummy_db):
    """Test that removing a service that is not associated returns False."""
    dummy_contact = DummyContact(id=1)
    dummy_service = DummyService(id=101)

    repository.get.return_value = dummy_contact
    dummy_db.get.return_value = dummy_service

    result = await repository.remove_service(1, 101)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_remove_service_failure(repository, dummy_db):
    """Test that a database error during remove_service is handled correctly."""
    repository.get.side_effect = SQLAlchemyError("Test error")
    with pytest.raises(IntegrityError):
        await repository.remove_service(1, 101)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_add_service_no_contact(repository, dummy_db):
    """
    Test that add_service returns False when the contact is not found.

    This covers the branch where:
        if not contact or not service:
            return False
    """
    # Simulate contact not found.
    repository.get.return_value = None
    # Simulate that the service exists.
    dummy_db.get.return_value = DummyService(id=101)

    result = await repository.add_service(1, 101)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_add_service_no_service(repository, dummy_db):
    """
    Test that add_service returns False when the service is not found.

    This covers the branch where a valid contact is retrieved but the service is missing.
    """
    # Simulate contact exists.
    repository.get.return_value = DummyContact(id=1)
    # Simulate that the service is not found.
    dummy_db.get.return_value = None

    result = await repository.add_service(1, 101)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_remove_service_no_contact(repository, dummy_db):
    """
    Test that remove_service returns False when the contact is not found.

    This covers the branch where the contact is not found.
    """
    # Simulate contact not found.
    repository.get.return_value = None
    # Simulate that the service exists.
    dummy_db.get.return_value = DummyService(id=101)

    result = await repository.remove_service(1, 101)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_remove_service_no_service(repository, dummy_db):
    """
    Test that remove_service returns False when the service is not found.

    This covers the branch where a valid contact is retrieved but the service is missing.
    """
    # Simulate contact exists.
    repository.get.return_value = DummyContact(id=1)
    # Simulate that the service is not found.
    dummy_db.get.return_value = None

    result = await repository.remove_service(1, 101)
    assert result is False
    dummy_db.commit.assert_not_called()
