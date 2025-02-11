"""
Unit tests for CommunityValidationService.

These tests cover the validation logic for community-related operations,
ensuring compliance with business rules such as name restrictions, membership
limits, privacy level changes, and user ownership constraints.

Tests:
    - test_validate_community_creation_success: Ensures a valid community can be created.
    - test_validate_community_creation_restricted_name: Ensures restricted names are blocked.
    - test_validate_community_creation_owner_not_found: Ensures an error is raised if the owner does not exist.
    - test_validate_community_creation_max_limit_exceeded: Ensures an error is raised if the owner exceeds the community limit.
    - test_validate_privacy_change_success: Ensures a valid privacy change is accepted.
    - test_validate_privacy_change_invalid_transition: Ensures an invalid privacy transition is rejected.

Dependencies:
    - pytest
    - unittest.mock for mocking database calls
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.community_service.validation import CommunityValidationService
from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.user_model import User
from app.services.service_exceptions import ValidationError, BusinessRuleViolationError
from app.services.community_service.constants import (
    RESTRICTED_NAMES,
    MAX_COMMUNITIES_FREE,
)


@pytest.mark.asyncio
async def test_validate_community_creation_success(dummy_db, mock_community_repository):
    """
    Test successful community creation validation.

    Ensures that if all conditions are met, the community creation validation
    does not raise any exceptions.
    """
    # Arrange
    mock_user = AsyncMock(spec=User)
    mock_user.is_active = True
    mock_user.is_premium = False
    mock_community_repository.get_user_communities.return_value = []
    dummy_db.get = AsyncMock(return_value=mock_user)

    service = CommunityValidationService(dummy_db)
    service.repository = mock_community_repository

    data = {"name": "Valid Community", "owner_id": 1}

    # Act & Assert
    await service.validate_community_creation(data)


@pytest.mark.asyncio
async def test_validate_community_creation_restricted_name(dummy_db):
    """
    Test that a community with a restricted name raises a ValidationError.
    """
    # Arrange
    service = CommunityValidationService(dummy_db)
    restricted_name = list(RESTRICTED_NAMES)[
        0
    ]  # Convert set to list to access elements
    data = {"name": restricted_name, "owner_id": 1}

    # Act & Assert
    with pytest.raises(
        ValidationError, match="Community name contains restricted words."
    ):
        await service.validate_community_creation(data)


@pytest.mark.asyncio
async def test_validate_community_creation_owner_not_found(
    dummy_db, mock_community_repository
):
    """
    Test that if the owner is not found, a ValidationError is raised.
    """
    # Arrange
    dummy_db.get = AsyncMock(return_value=None)  # Simulating owner not found
    service = CommunityValidationService(dummy_db)
    service.repository = mock_community_repository

    data = {"name": "Valid Name", "owner_id": 1}

    # Act & Assert
    with pytest.raises(ValidationError, match="Owner 1 not found or inactive."):
        await service.validate_community_creation(data)


@pytest.mark.asyncio
async def test_validate_community_creation_max_limit_exceeded(
    dummy_db, mock_community_repository
):
    """
    Test that exceeding the max limit of owned communities raises a BusinessRuleViolationError.
    """
    # Arrange
    mock_user = AsyncMock(spec=User)
    mock_user.is_active = True
    mock_user.is_premium = False  # Free-tier user

    # Simulating a user who has already reached the max limit
    mock_community_repository.get_user_communities = AsyncMock(
        return_value=[MagicMock()] * MAX_COMMUNITIES_FREE
    )

    dummy_db.get = AsyncMock(return_value=mock_user)

    service = CommunityValidationService(dummy_db)
    service.repository = mock_community_repository

    data = {"name": "Valid Name", "owner_id": 1}

    # Act & Assert
    with pytest.raises(
        BusinessRuleViolationError, match="User has reached maximum owned communities."
    ):
        await service.validate_community_creation(data)


@pytest.mark.asyncio
async def test_validate_privacy_change_success(dummy_db):
    """
    Test that a valid privacy change is accepted without error.
    """
    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.allowed_privacy_transitions = {PrivacyLevel.PRIVATE}
    service = CommunityValidationService(dummy_db)

    # Act & Assert
    await service.validate_privacy_change(mock_community, PrivacyLevel.PRIVATE)


@pytest.mark.asyncio
async def test_validate_privacy_change_invalid_transition(dummy_db):
    """
    Test that an invalid privacy change raises a BusinessRuleViolationError.
    """
    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.allowed_privacy_transitions = {
        PrivacyLevel.PRIVATE
    }  # Cannot transition to PUBLIC
    service = CommunityValidationService(dummy_db)

    # Act & Assert
    with pytest.raises(BusinessRuleViolationError, match="Invalid privacy transition"):
        await service.validate_privacy_change(mock_community, PrivacyLevel.PUBLIC)
