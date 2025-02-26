"""
Unit tests for the CommunityPrivacyService.

This module tests the change_privacy_level method of the CommunityPrivacyService,
ensuring correct privacy transitions, enforcement of business rules, and 
handling of missing communities.

Tests:
    - test_change_privacy_level_success: Verifies a valid privacy transition.
    - test_change_privacy_level_invalid_transition: Ensures invalid transitions raise errors.
    - test_change_privacy_level_community_not_found: Confirms that a missing community raises an error.

Dependencies:
    - pytest
    - unittest.mock (AsyncMock, MagicMock)
    - app.services.community_service.privacy.CommunityPrivacyService
    - app.services.service_exceptions (ResourceNotFoundError, BusinessRuleViolationError)
    - app.db.models.community_model (Community, PrivacyLevel)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.community_service.constants import (
    PRIVACY_TRANSITION_RULES,
)
from app.services.community_service.privacy import (
    CommunityPrivacyService,
)
from app.services.service_exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)
from app.db.models.community_model import Community, PrivacyLevel


@pytest.mark.asyncio
async def test_change_privacy_level_success(mock_community_repository, dummy_db):
    """
    Test successful privacy level change.

    Ensures that when a valid privacy transition is performed, the
    community's privacy level is updated and the database commit is called.

    Given:
        - A community with a current privacy level.
        - A valid transition to a new privacy level.

    When:
        - The `change_privacy_level` method is called with a valid transition.

    Then:
        - The community's privacy level is updated.
        - The database commit method is called once.
    """
    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.id = 1
    mock_community.privacy_level = PrivacyLevel.PUBLIC
    mock_community_repository.get.return_value = mock_community
    dummy_db.commit = AsyncMock()  # Fix: Use AsyncMock for `await db.commit()`

    service = CommunityPrivacyService(dummy_db)
    service.repository = mock_community_repository

    # Act
    result = await service.change_privacy_level(1, PrivacyLevel.PRIVATE)

    # Assert
    assert result.privacy_level == PrivacyLevel.PRIVATE
    dummy_db.commit.assert_awaited_once()  # Fix: Use `assert_awaited_once()` for async calls


@pytest.mark.asyncio
async def test_change_privacy_level_invalid_transition(
    mock_community_repository, dummy_db
):
    """
    Test invalid privacy level transition.

    Ensures that attempting to change a community's privacy level to an
    invalid state raises a BusinessRuleViolationError.

    Given:
        - A community with a current privacy level.
        - An attempted transition that violates predefined rules.

    When:
        - The `change_privacy_level` method is called with an invalid transition.

    Then:
        - A BusinessRuleViolationError is raised.
    """
    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.id = 1
    mock_community.privacy_level = PrivacyLevel.PRIVATE
    mock_community_repository.get.return_value = mock_community
    dummy_db.commit = AsyncMock()

    service = CommunityPrivacyService(dummy_db)
    service.repository = mock_community_repository

    # **Mock `PRIVACY_TRANSITION_RULES` to disallow the transition**
    with patch.dict(PRIVACY_TRANSITION_RULES, {PrivacyLevel.PRIVATE: {}}):
        # Act & Assert
        with pytest.raises(
            BusinessRuleViolationError, match="Invalid privacy transition"
        ):
            await service.change_privacy_level(1, PrivacyLevel.PUBLIC)

    dummy_db.commit.assert_not_awaited()  # Ensure commit is NOT called on failure


@pytest.mark.asyncio
async def test_change_privacy_level_community_not_found(
    mock_community_repository, dummy_db
):
    """
    Test privacy level change for a non-existent community.

    Ensures that attempting to change the privacy level of a missing
    community results in a ResourceNotFoundError.

    Given:
        - A non-existent community ID.

    When:
        - The `change_privacy_level` method is called.

    Then:
        - A ResourceNotFoundError is raised.
    """
    # Arrange
    mock_community_repository.get.return_value = None
    dummy_db.commit = AsyncMock()

    service = CommunityPrivacyService(dummy_db)
    service.repository = mock_community_repository

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match="Community 1 not found"):
        await service.change_privacy_level(1, PrivacyLevel.PRIVATE)

    dummy_db.commit.assert_not_awaited()  # Ensure commit is NOT called on failure
