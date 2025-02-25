"""
Unit tests for CommunityService class.

This test module ensures that the CommunityService class correctly performs 
CRUD operations on community entities while following business rules.

Tested methods:
    - create_community
    - get_community
    - update_community
    - delete_community

Dependencies:
    - pytest
    - unittest.mock for mocking dependencies
"""

import pytest
from app.db.models.community_model import Community
from app.api.v1.schemas.community_schema import CommunityCreate, CommunityUpdate
from app.services.service_exceptions import ResourceNotFoundError, ValidationError


@pytest.mark.asyncio
async def test_create_community(community_service, mock_community_repository):
    """
    Test creating a new community successfully.

    Ensures that:
        - The repository's `create` method is called once with valid data.
        - The created community instance is returned correctly.
    """
    # Arrange
    mock_data = CommunityCreate(
        name="Test Community", description="A test community", owner_id=1
    )
    mock_community = Community(
        id=1, name="Test Community", description="A test community"
    )
    mock_community_repository.create.return_value = mock_community

    # Act
    result = await community_service.create_community(mock_data)

    # Assert
    mock_community_repository.create.assert_called_once_with(mock_data)
    assert result.name == "Test Community"
    assert result.description == "A test community"


@pytest.mark.asyncio
async def test_create_community_invalid_data(
    community_service, mock_community_repository
):
    """
    Test creating a community with invalid data raises a ValidationError.

    Ensures that:
        - A ValidationError is raised when invalid data is provided.
    """
    # Arrange
    invalid_data = CommunityCreate(name="", description="Invalid", owner_id=1)

    # Act & Assert
    with pytest.raises(ValidationError):
        await community_service.create_community(invalid_data)


@pytest.mark.asyncio
async def test_get_community_success(community_service, mock_community_repository):
    """
    Test retrieving an existing community by ID.

    Ensures that:
        - The repository's `get` method is called once with the correct ID.
        - The retrieved community instance is returned correctly.
    """
    # Arrange
    mock_community = Community(
        id=1, name="Test Community", description="A test community"
    )
    mock_community_repository.get.return_value = mock_community

    # Act
    result = await community_service.get_community(1)

    # Assert
    mock_community_repository.get.assert_called_once_with(
        1
    )  # Ensure method was called correctly
    assert result == mock_community  # Validate return value
    assert result.name == "Test Community"


@pytest.mark.asyncio
async def test_get_community_not_found(community_service, mock_community_repository):
    """
    Test retrieving a non-existent community raises ResourceNotFoundError.

    Ensures that:
        - If the community is not found, a ResourceNotFoundError is raised.
    """
    # Arrange
    mock_community_repository.get.return_value = (
        None  # This is not triggering the exception properly
    )

    # Act & Assert
    with pytest.raises(ResourceNotFoundError):
        await community_service.get_community(999)


@pytest.mark.asyncio
async def test_update_community_success(community_service, mock_community_repository):
    """
    Test updating an existing community.

    Ensures that:
        - The repository's `update` method is called once with valid data.
        - The updated community instance is returned correctly.
    """
    # Arrange
    mock_update_data = CommunityUpdate(
        description="Updated description", privacy_level="public", is_active=True
    )
    mock_community = Community(
        id=1, name="Test Community", description="Updated description"
    )
    mock_community_repository.update.return_value = mock_community

    # Act
    result = await community_service.update_community(1, mock_update_data)

    # Assert
    mock_community_repository.update.assert_called_once_with(
        id=1, schema=mock_update_data
    )
    assert result.description == "Updated description"


@pytest.mark.asyncio
async def test_update_community_not_found(community_service, mock_community_repository):
    """
    Test updating a non-existent community raises ResourceNotFoundError.

    Ensures that:
        - If the community is not found, a ResourceNotFoundError is raised.
    """
    # Arrange
    mock_update_data = CommunityUpdate(
        description="Updated description", privacy_level="public", is_active=True
    )
    mock_community_repository.update.return_value = None

    # Act & Assert
    with pytest.raises(ResourceNotFoundError):
        await community_service.update_community(999, mock_update_data)


@pytest.mark.asyncio
async def test_delete_community_success(community_service, mock_community_repository):
    """
    Test deleting an existing community.

    Ensures that:
        - The repository's `delete` method is called once with the correct ID.
    """
    # Act
    await community_service.delete_community(1)

    # Assert
    mock_community_repository.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_delete_community_not_found(community_service, mock_community_repository):
    """
    Test deleting a non-existent community raises ResourceNotFoundError.

    Ensures that:
        - If the community does not exist, a ResourceNotFoundError is raised.
    """
    # Arrange
    mock_community_repository.delete.side_effect = ResourceNotFoundError(
        "Community not found"
    )

    # Act & Assert
    with pytest.raises(ResourceNotFoundError):
        await community_service.delete_community(999)
