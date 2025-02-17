"""
Unit tests for the CommunityMember model.

This module tests all aspects of the CommunityMember model, including:
- Object instantiation
- Relationship attributes
- Default values
- String representation

The tests leverage shared fixtures for mock database sessions, repositories, and test data.

Typical usage example:
    pytest tests/unit/test_db/test_models/test_community_member_model.py
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from app.db.models.community_member_model import CommunityMember


@pytest.fixture
def test_community_member():
    """
    Create a test CommunityMember instance.

    Returns:
        CommunityMember: A test community member instance.
    """
    return CommunityMember(
        community_id=1,
        user_id=100,
        role="admin",
        joined_at=datetime(2024, 1, 1, 12, 0, 0),
        role_assigned_at=datetime(2024, 1, 2, 15, 0, 0),
        role_assigned_by=200,
        is_active=True,
    )


def test_community_member_creation(test_community_member):
    """
    Test that a CommunityMember object is correctly instantiated.

    Args:
        test_community_member (CommunityMember): A test community member instance.
    """
    assert test_community_member.community_id == 1
    assert test_community_member.user_id == 100
    assert test_community_member.role == "admin"
    assert test_community_member.joined_at == datetime(2024, 1, 1, 12, 0, 0)
    assert test_community_member.role_assigned_at == datetime(2024, 1, 2, 15, 0, 0)
    assert test_community_member.role_assigned_by == 200
    assert test_community_member.is_active is True


def test_community_member_default_values():
    """
    Test that CommunityMember has correct default values.
    """
    member = CommunityMember(
        community_id=2,
        user_id=101,
    )

    assert member.role == "member"  # Default role
    assert member.is_active is True  # Default active status
    assert member.role_assigned_at is None  # No assigned role initially
    assert member.role_assigned_by is None  # No role assigner initially


def test_community_member_repr(test_community_member):
    """
    Test that the __repr__ method correctly formats the string representation.

    Args:
        test_community_member (CommunityMember): A test community member instance.
    """
    assert (
        repr(test_community_member)
        == "CommunityMember(community_id=1, user_id=100, role=admin)"
    )
