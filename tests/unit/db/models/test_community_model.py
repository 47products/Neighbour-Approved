"""
Unit tests for the Community model.

This module tests all aspects of the Community model, including:
- Object instantiation
- Relationship handling
- Property methods
- Instance methods
- Class methods
- Privacy level checks
- Membership management

The tests leverage shared fixtures for mock database sessions, repositories, and test data.

Typical usage example:
    pytest tests/unit/test_db/test_models/test_community_model.py
"""

import pytest
from unittest.mock import MagicMock
from app.db.models.community_model import Community, CommunityCreate, PrivacyLevel


@pytest.fixture
def test_community():
    """
    Create a test Community instance.

    Returns:
        Community: A Community instance with test data.
    """
    return Community(
        id=1,
        name="Test Community",
        owner_id=100,
        privacy_level=PrivacyLevel.PRIVATE,
        total_count=5,
        active_count=3,
        is_active=True,
    )


def test_community_creation(test_community):
    """
    Test that a Community object is correctly instantiated.

    Args:
        test_community (Community): A test community instance.
    """
    assert test_community.id == 1
    assert test_community.name == "Test Community"
    assert test_community.owner_id == 100
    assert test_community.privacy_level == PrivacyLevel.PRIVATE
    assert test_community.total_count == 5
    assert test_community.active_count == 3
    assert test_community.is_active is True


def test_community_create():
    """
    Test that the create class method correctly instantiates a Community from CommunityCreate.

    This test ensures that data is correctly mapped from the DTO to the Community model.
    """
    community_data = CommunityCreate(
        name="New Community",
        owner_id=200,
        description="A new test community",
        privacy_level=PrivacyLevel.PUBLIC,
    )
    new_community = Community.create(community_data)

    assert new_community.name == "New Community"
    assert new_community.owner_id == 200
    assert new_community.privacy_level == PrivacyLevel.PUBLIC


def test_community_add_member(test_community):
    """
    Test that add_member correctly adds a user.

    Args:
        test_community (Community): A test community instance.
    """
    mock_user = MagicMock()
    mock_user.id = 300
    mock_user.is_active = True

    initial_total = test_community.total_count
    initial_active = test_community.active_count

    test_community.members = []  # Ensure fresh members list
    test_community.add_member(mock_user)

    assert mock_user in test_community.members
    assert test_community.total_count == initial_total + 1
    assert test_community.active_count == initial_active + 1


def test_community_add_member_already_exists(test_community):
    """
    Test that add_member raises an error if the user is already a member.

    Args:
        test_community (Community): A test community instance.
    """
    mock_user = MagicMock()
    mock_user.id = 300

    test_community.members = [mock_user]

    with pytest.raises(ValueError, match="User 300 is already a member"):
        test_community.add_member(mock_user)


def test_community_remove_member(test_community):
    """
    Test that remove_member correctly removes a user.

    Args:
        test_community (Community): A test community instance.
    """
    mock_user = MagicMock()
    mock_user.id = 300
    mock_user.is_active = True

    test_community.members = [mock_user]
    test_community.total_count = 5
    test_community.active_count = 3

    test_community.remove_member(mock_user)

    assert mock_user not in test_community.members
    assert test_community.total_count == 4
    assert test_community.active_count == 2


def test_community_remove_member_not_exists(test_community):
    """
    Test that remove_member raises an error if the user is not a member.

    Args:
        test_community (Community): A test community instance.
    """
    mock_user = MagicMock()
    mock_user.id = 300

    test_community.members = []  # Ensure no members

    with pytest.raises(ValueError, match="User 300 is not a member"):
        test_community.remove_member(mock_user)


def test_community_add_related_community(test_community):
    """
    Test that add_related_community correctly establishes a relationship.

    Args:
        test_community (Community): A test community instance.
    """
    mock_community = MagicMock()
    mock_community.id = 400

    test_community.related_communities = []  # Ensure fresh relationships list
    test_community.add_related_community(mock_community)

    assert mock_community in test_community.related_communities


def test_community_add_related_community_already_exists(test_community):
    """
    Test that add_related_community raises an error if already related.

    Args:
        test_community (Community): A test community instance.
    """
    mock_community = MagicMock()
    mock_community.id = 400

    test_community.related_communities = [mock_community]

    with pytest.raises(ValueError, match="Already related to community 400"):
        test_community.add_related_community(mock_community)


def test_community_can_user_access_public(test_community):
    """
    Test that can_user_access returns True for public communities.

    Args:
        test_community (Community): A test community instance.
    """
    test_community.privacy_level = PrivacyLevel.PUBLIC
    assert test_community.can_user_access(None) is True


def test_community_can_user_access_private(test_community):
    """
    Test that can_user_access returns False if user is not provided for private communities.

    Args:
        test_community (Community): A test community instance.
    """
    test_community.privacy_level = PrivacyLevel.PRIVATE
    assert test_community.can_user_access(None) is False


def test_community_can_user_access_owner(test_community):
    """
    Test that can_user_access returns True for the community owner.

    Args:
        test_community (Community): A test community instance.
    """
    mock_user = MagicMock()
    mock_user.id = 100  # Matches owner_id
    assert test_community.can_user_access(mock_user) is True


def test_community_can_user_access_member(test_community):
    """
    Test that can_user_access returns True if user is a member.

    Args:
        test_community (Community): A test community instance.
    """
    mock_user = MagicMock()
    mock_user.id = 300

    test_community.members = [mock_user]
    assert test_community.can_user_access(mock_user) is True


def test_community_can_user_access_not_member(test_community):
    """
    Test that can_user_access returns False if user is not a member.

    Args:
        test_community (Community): A test community instance.
    """
    mock_user = MagicMock()
    mock_user.id = 400

    test_community.members = []  # No members
    assert test_community.can_user_access(mock_user) is False


def test_community_repr(test_community):
    """
    Test that the __repr__ method correctly formats the string representation.

    Args:
        test_community (Community): A test community instance.
    """
    assert repr(test_community) == "Community(id=1, name=Test Community)"
