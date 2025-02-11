"""
Unit tests for the CommunityRelationshipService.

These tests cover the functionality of managing relationships between communities,
including adding and removing relationships while enforcing limits and validation rules.

Test cases:
    - test_manage_relationship_add_success: Successfully adds a relationship.
    - test_manage_relationship_remove_success: Successfully removes a relationship.
    - test_manage_relationship_invalid_action: Raises ValidationError for invalid actions.
    - test_manage_relationship_community_not_found: Raises ResourceNotFoundError if a community does not exist.
    - test_manage_relationship_quota_exceeded: Raises QuotaExceededError when the relationship limit is exceeded.

Dependencies:
    - pytest
    - unittest.mock for mocking database operations.
"""

import pytest
from unittest.mock import AsyncMock
from app.services.community_service.relationships import CommunityRelationshipService
from app.services.service_exceptions import (
    ResourceNotFoundError,
    ValidationError,
    QuotaExceededError,
)
from app.db.models.community_model import Community
from app.services.community_service.constants import MAX_RELATIONSHIPS


@pytest.mark.asyncio
async def test_manage_relationship_add_success(mock_community_repository, dummy_db):
    """
    Test successfully adding a community relationship.

    Given:
        - Two existing communities.
        - The relationship limit is not exceeded.

    When:
        - The `manage_relationship` method is called with the "add" action.

    Then:
        - The related community is added.
        - The database commit method is called once.
        - The method returns True.
    """
    # Arrange
    community = AsyncMock(spec=Community)
    community.id = 1
    community.related_communities = []

    related_community = AsyncMock(spec=Community)
    related_community.id = 2

    mock_community_repository.get.side_effect = [community, related_community]
    dummy_db.commit = AsyncMock()

    service = CommunityRelationshipService(dummy_db)
    service.repository = mock_community_repository

    # Act
    result = await service.manage_relationship(1, 2, "add")

    # Assert
    assert related_community in community.related_communities
    dummy_db.commit.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_manage_relationship_remove_success(mock_community_repository, dummy_db):
    """
    Test successfully removing a community relationship.

    Given:
        - Two existing communities.
        - The related community is already linked.

    When:
        - The `manage_relationship` method is called with the "remove" action.

    Then:
        - The related community is removed.
        - The database commit method is called once.
        - The method returns True.
    """
    # Arrange
    related_community = AsyncMock(spec=Community)
    related_community.id = 2

    community = AsyncMock(spec=Community)
    community.id = 1
    community.related_communities = [related_community]

    mock_community_repository.get.side_effect = [community, related_community]
    dummy_db.commit = AsyncMock()

    service = CommunityRelationshipService(dummy_db)
    service.repository = mock_community_repository

    # Act
    result = await service.manage_relationship(1, 2, "remove")

    # Assert
    assert related_community not in community.related_communities
    dummy_db.commit.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_manage_relationship_invalid_action(mock_community_repository, dummy_db):
    """
    Test invalid relationship action.

    Given:
        - Two existing communities.

    When:
        - The `manage_relationship` method is called with an invalid action.

    Then:
        - A ValidationError is raised.
    """
    # Arrange
    community = AsyncMock(spec=Community)
    community.id = 1

    related_community = AsyncMock(spec=Community)
    related_community.id = 2

    mock_community_repository.get.side_effect = [community, related_community]
    service = CommunityRelationshipService(dummy_db)
    service.repository = mock_community_repository

    # Act & Assert
    with pytest.raises(ValidationError, match="Invalid relationship action"):
        await service.manage_relationship(1, 2, "invalid_action")


@pytest.mark.asyncio
async def test_manage_relationship_community_not_found(
    mock_community_repository, dummy_db
):
    """
    Test handling when a community does not exist.

    Given:
        - One or both of the communities do not exist.

    When:
        - The `manage_relationship` method is called.

    Then:
        - A ResourceNotFoundError is raised.
    """
    # Arrange
    mock_community_repository.get.side_effect = [None, AsyncMock(spec=Community)]
    service = CommunityRelationshipService(dummy_db)
    service.repository = mock_community_repository

    # Act & Assert
    with pytest.raises(
        ResourceNotFoundError, match="One or both communities not found"
    ):
        await service.manage_relationship(1, 2, "add")


@pytest.mark.asyncio
async def test_manage_relationship_quota_exceeded(mock_community_repository, dummy_db):
    """
    Test handling when the relationship limit is exceeded.

    Given:
        - A community has reached the maximum number of relationships.

    When:
        - The `manage_relationship` method is called with the "add" action.

    Then:
        - A QuotaExceededError is raised.
    """
    # Arrange
    community = AsyncMock(spec=Community)
    community.id = 1
    community.related_communities = [AsyncMock(spec=Community)] * MAX_RELATIONSHIPS

    related_community = AsyncMock(spec=Community)
    related_community.id = 2

    mock_community_repository.get.side_effect = [community, related_community]
    service = CommunityRelationshipService(dummy_db)
    service.repository = mock_community_repository

    # Act & Assert
    with pytest.raises(
        QuotaExceededError, match="Maximum number of related communities reached"
    ):
        await service.manage_relationship(1, 2, "add")
