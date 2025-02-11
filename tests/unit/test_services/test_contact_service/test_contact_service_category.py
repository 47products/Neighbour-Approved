"""
Unit tests for ContactServiceCategory.

This module tests category-related operations in ContactServiceCategory,
including adding and removing categories associated with a contact.

Fixtures required:
- dummy_db: A mocked asynchronous database session.
- mock_contact_repository: A mocked ContactRepository instance.
- contact_service_category: An instance of ContactServiceCategory with mocked dependencies.
- mock_contact: A dummy contact instance for testing.
- mock_category: A dummy category instance for testing.
"""

import pytest
from unittest.mock import AsyncMock
from app.services.service_exceptions import (
    ResourceNotFoundError,
)


@pytest.mark.asyncio
async def test_add_category_success(
    contact_service_category, mock_contact_repository, mock_contact, mock_category
):
    """Test successful addition of a category to a contact."""
    mock_contact_repository.get.return_value = mock_contact
    added = await contact_service_category.add_category(contact_id=1, category_id=5)
    assert added is True
    assert mock_category in mock_contact.categories


@pytest.mark.asyncio
async def test_add_category_not_found(
    contact_service_category, mock_contact_repository
):
    """Test adding a category to a non-existent contact should raise ResourceNotFoundError."""
    mock_contact_repository.get.return_value = None
    with pytest.raises(ResourceNotFoundError):
        await contact_service_category.add_category(contact_id=999, category_id=5)


@pytest.mark.asyncio
async def test_remove_category_success(
    contact_service_category, mock_contact_repository, mock_contact, mock_category
):
    """Test that removing an existing category from a contact should return True."""
    # Simulate the category being in the contact's categories
    mock_contact.categories.append(mock_category)
    mock_contact_repository.get.return_value = mock_contact

    # Try to remove the category
    removed = await contact_service_category.remove_category(
        contact_id=1, category_id=5
    )

    # Ensure it returns True and the category is removed
    assert removed is True
    assert (
        mock_category not in mock_contact.categories
    )  # Ensure the category is removed


@pytest.mark.asyncio
async def test_remove_category_not_found(
    contact_service_category, mock_contact_repository, mock_contact
):
    """Test that attempting to remove a category that doesn't exist should raise a ResourceNotFoundError."""
    mock_contact_repository.get.return_value = mock_contact

    with pytest.raises(ResourceNotFoundError):
        await contact_service_category.remove_category(contact_id=1, category_id=999)


@pytest.mark.asyncio
async def test_add_category_already_exists(
    contact_service_category, mock_contact_repository, mock_contact, mock_category
):
    """Test that adding an already existing category to a contact should return False."""
    # Simulate the category already being in the contact's categories
    mock_contact.categories.append(mock_category)
    mock_contact_repository.get.return_value = mock_contact

    # Try to add the category again
    added = await contact_service_category.add_category(contact_id=1, category_id=5)

    # Ensure it returns False (since the category is already in the contact's categories)
    assert added is False
    assert (
        mock_category in mock_contact.categories
    )  # Ensure the category wasn't added again


@pytest.mark.asyncio
async def test_add_category_category_not_found(
    contact_service_category, mock_contact_repository, mock_contact
):
    """Test that attempting to add a non-existent category raises ResourceNotFoundError."""
    mock_contact_repository.get.return_value = mock_contact
    contact_service_category.db.get = AsyncMock(
        return_value=None
    )  # Simulate category not found

    with pytest.raises(ResourceNotFoundError):
        await contact_service_category.add_category(contact_id=1, category_id=999)


@pytest.mark.asyncio
async def test_remove_category_contact_not_found(
    contact_service_category, mock_contact_repository, mock_category
):
    """Test that attempting to remove a category from a non-existent contact raises ResourceNotFoundError."""
    # Simulate the contact not being found
    mock_contact_repository.get.return_value = None

    with pytest.raises(ResourceNotFoundError):
        await contact_service_category.remove_category(contact_id=999, category_id=5)
