"""
Unit tests for ContactServiceBase.

This module tests the core CRUD operations of ContactServiceBase, ensuring proper
functionality for contact retrieval and deletion.

Fixtures required:
- dummy_db: A mocked asynchronous database session.
- mock_contact_repository: A mocked ContactRepository instance.
- contact_service: An instance of ContactService with mocked dependencies.
- mock_contact: A dummy contact instance for testing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.contact_service.base import ContactService
from app.db.models.contact_model import Contact
from app.services.service_exceptions import ResourceNotFoundError


@pytest.fixture
def mock_contact():
    """Create a dummy contact instance for testing."""
    return Contact(id=1, contact_name="Test Contact", is_active=True)


@pytest.fixture
def mock_contact_repository(dummy_db):
    """Create a mock ContactRepository for simulating database operations."""
    repository = MagicMock()
    repository.get = AsyncMock()
    repository.delete = AsyncMock(return_value=True)
    return repository


@pytest.fixture
def contact_service(dummy_db, mock_contact_repository):
    """Create an instance of ContactService with mocked dependencies."""
    service = ContactService(db=dummy_db)
    service._repository = mock_contact_repository
    return service


@pytest.mark.asyncio
async def test_get_contact_found(
    contact_service, mock_contact_repository, mock_contact
):
    """Test retrieving an existing contact by ID."""
    mock_contact_repository.get.return_value = mock_contact
    contact = await contact_service.get_contact(contact_id=1)
    assert contact == mock_contact


@pytest.mark.asyncio
async def test_get_contact_not_found(contact_service, mock_contact_repository):
    """Test retrieving a non-existent contact should raise ResourceNotFoundError."""
    mock_contact_repository.get.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await contact_service.get_contact(contact_id=999)


@pytest.mark.asyncio
async def test_delete_contact_success(
    contact_service, mock_contact_repository, mock_contact
):
    """Test successful deletion of a contact."""
    mock_contact_repository.get.return_value = mock_contact
    deleted = await contact_service.delete_contact(contact_id=1)
    assert deleted is True


@pytest.mark.asyncio
async def test_delete_contact_not_found(contact_service, mock_contact_repository):
    """Test deleting a non-existent contact should raise ResourceNotFoundError."""
    mock_contact_repository.get.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await contact_service.delete_contact(contact_id=999)
