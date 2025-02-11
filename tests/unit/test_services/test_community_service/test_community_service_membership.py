"""
Unit tests for `membership.py` in the community service module.

This module ensures that all membership-related operations function correctly,
including role management, membership approvals, and invitations.

Tested Methods:
    - manage_membership

Dependencies:
    - pytest
    - unittest.mock for mocking dependencies
"""

from unittest.mock import AsyncMock
import pytest
from app.db.models.community_model import Community, PrivacyLevel
from app.services.community_service.constants import MAX_MEMBERS_FREE
from app.services.service_exceptions import (
    ResourceNotFoundError,
    ValidationError,
    QuotaExceededError,
)


@pytest.mark.asyncio
async def test_manage_membership_invite_success(
    community_service_membership, mock_community_repository, mock_user
):
    """
    Test inviting a user to a community successfully.
    """
    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.id = 1
    mock_community.name = "Test Community"
    mock_community.privacy_level = PrivacyLevel.PUBLIC
    mock_community.is_premium = False
    mock_community.total_count = 10  # Ensure total_count is an integer
    mock_community_repository.get.return_value = mock_community

    # Act
    result = await community_service_membership.manage_membership(
        1, mock_user.id, "invite"
    )

    # Assert
    assert result is True
    mock_community_repository.get.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_manage_membership_community_not_found(
    community_service_membership, mock_community_repository
):
    """
    Test that trying to manage membership in a non-existent community raises ResourceNotFoundError.
    """
    # Arrange
    mock_community_repository.get.return_value = None

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match="Community 1 not found"):
        await community_service_membership.manage_membership(1, 2, "invite")


@pytest.mark.asyncio
async def test_manage_membership_user_not_found(
    community_service_membership, mock_community_repository, dummy_db
):
    """
    Test that trying to manage membership for a non-existent user raises ResourceNotFoundError.
    """
    # Arrange
    mock_community = Community(
        id=1, name="Test Community", privacy_level=PrivacyLevel.PUBLIC
    )
    mock_community_repository.get.return_value = mock_community
    dummy_db.get.return_value = None  # Simulating user not found

    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match="User 2 not found"):
        await community_service_membership.manage_membership(1, 2, "invite")


@pytest.mark.asyncio
async def test_manage_membership_invalid_action(
    community_service_membership, mock_community_repository, mock_user
):
    """
    Test that passing an invalid action raises ValidationError.
    """
    # Arrange
    mock_community = Community(
        id=1, name="Test Community", privacy_level=PrivacyLevel.PUBLIC
    )
    mock_community_repository.get.return_value = mock_community

    # Act & Assert
    with pytest.raises(
        ValidationError, match="Invalid membership action: invalid_action"
    ):
        await community_service_membership.manage_membership(
            1, mock_user.id, "invalid_action"
        )


@pytest.mark.asyncio
async def test_manage_membership_invalid_role(
    community_service_membership, mock_community_repository, mock_user
):
    """
    Test that passing an invalid role raises ValidationError.
    """
    # Arrange
    mock_community = Community(
        id=1, name="Test Community", privacy_level=PrivacyLevel.PUBLIC
    )
    mock_community_repository.get.return_value = mock_community

    # Act & Assert
    with pytest.raises(ValidationError, match="Invalid role: invalid_role"):
        await community_service_membership.manage_membership(
            1, mock_user.id, "invite", role="invalid_role"
        )


@pytest.mark.asyncio
async def test_manage_membership_quota_exceeded(
    community_service_membership, mock_community_repository, mock_user
):
    """
    Test that trying to invite or approve a user when the community has reached its limit raises QuotaExceededError.
    """
    # Arrange
    mock_community = Community(
        id=1, name="Test Community", privacy_level=PrivacyLevel.PUBLIC
    )
    mock_community.total_count = MAX_MEMBERS_FREE  # Set to max limit
    mock_community.is_premium = False  # Simulating a free-tier community
    mock_community_repository.get.return_value = mock_community

    # Act & Assert
    with pytest.raises(
        QuotaExceededError, match="Community has reached the member limit of 50"
    ):
        await community_service_membership.manage_membership(1, mock_user.id, "invite")


@pytest.mark.asyncio
async def test_manage_membership_invitation_only(
    community_service_membership, mock_community_repository, mock_user
):
    """
    Test that the correct handler is called when a community has an INVITATION_ONLY privacy level.
    """
    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.id = 1
    mock_community.name = "Test Community"
    mock_community.privacy_level = PrivacyLevel.INVITATION_ONLY
    mock_community.is_premium = False
    mock_community.total_count = 10
    mock_community_repository.get.return_value = mock_community
    community_service_membership._handle_invitation_only_membership = AsyncMock(
        return_value=True
    )

    # Act
    result = await community_service_membership.manage_membership(
        1, mock_user.id, "invite"
    )

    # Assert
    community_service_membership._handle_invitation_only_membership.assert_called_once_with(
        mock_community,
        mock_user,
        "invite",
        "member",  # Fix: Ensure `mock_user` is correctly passed
    )
    assert result is True


@pytest.mark.asyncio
async def test_manage_membership_private(
    community_service_membership, mock_community_repository, mock_user
):
    """
    Test that the correct handler is called when a community has a PRIVATE privacy level.
    """
    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.id = 1
    mock_community.name = "Test Community"
    mock_community.privacy_level = PrivacyLevel.PRIVATE
    mock_community.is_premium = False
    mock_community.total_count = 10
    mock_community_repository.get.return_value = mock_community
    community_service_membership._handle_private_membership = AsyncMock(
        return_value=True
    )

    # Act
    result = await community_service_membership.manage_membership(
        1, mock_user.id, "approve"
    )

    # Assert
    community_service_membership._handle_private_membership.assert_called_once_with(
        mock_community,
        mock_user,
        "approve",
        "member",  # Fix: Ensure `mock_user` is correctly passed
    )
    assert result is True


@pytest.mark.asyncio
async def test_manage_membership_public(
    community_service_membership, mock_community_repository, mock_user
):
    """
    Test that the correct handler is called when a community has a PUBLIC privacy level.
    """
    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.id = 1
    mock_community.name = "Test Community"
    mock_community.privacy_level = PrivacyLevel.PUBLIC
    mock_community.is_premium = False
    mock_community.total_count = 10
    mock_community_repository.get.return_value = mock_community
    community_service_membership._handle_public_membership = AsyncMock(
        return_value=True
    )

    # Act
    result = await community_service_membership.manage_membership(
        1, mock_user.id, "approve"
    )

    # Assert
    community_service_membership._handle_public_membership.assert_called_once_with(
        mock_community,
        mock_user,
        "approve",
        "member",  # Fix: Ensure `mock_user` is correctly passed
    )
    assert result is True


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["reject", "leave"])
async def test_manage_membership_no_member_limit_check(
    community_service_membership, mock_community_repository, mock_user, action
):
    """
    Ensure _check_member_limits is NOT called for actions that do not require member limit checks.
    """

    # Arrange
    mock_community = AsyncMock(spec=Community)
    mock_community.id = 1
    mock_community.name = "Test Community"
    mock_community.privacy_level = PrivacyLevel.PUBLIC
    mock_community.is_premium = False  # Required for membership checks
    mock_community.total_count = 10
    mock_community_repository.get.return_value = mock_community

    # Mock service behavior
    community_service_membership._check_member_limits = AsyncMock()
    community_service_membership._handle_public_membership = AsyncMock(
        return_value=True
    )

    # Act
    result = await community_service_membership.manage_membership(
        1, mock_user.id, action
    )

    # Assert
    community_service_membership._check_member_limits.assert_not_called()
    community_service_membership._handle_public_membership.assert_called_once_with(
        mock_community, mock_user, action, "member"
    )
    assert result is True
