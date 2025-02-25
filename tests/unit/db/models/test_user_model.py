"""
Unit tests for the User model.

This module tests all aspects of the User model, including:
- Object instantiation
- Relationship handling
- Property methods
- Instance methods
- Class methods
- Constraint validation

The tests leverage shared fixtures for mock database sessions, repositories, and
test users.

Typical usage example:
    pytest tests/unit/test_db/test_models/test_user_model.py
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from app.db.models.user_model import User, UserCreate


@pytest.fixture
def test_user():
    """
    Create a test User instance.

    Returns:
        User: A User instance with test data.
    """
    return User(
        id=1,
        email="test@example.com",
        password="hashedpassword",
        first_name="Test",
        last_name="User",
        mobile_number="1234567890",
        postal_address="123 Test St",
        physical_address="456 Example Rd",
        country="Testland",
        email_verified=False,
        last_login=None,
    )


def test_user_creation(test_user):
    """
    Test that a User object is correctly instantiated.

    Args:
        test_user (User): A test user instance.
    """
    assert test_user.id == 1
    assert test_user.email == "test@example.com"
    assert test_user.password == "hashedpassword"
    assert test_user.first_name == "Test"
    assert test_user.last_name == "User"
    assert test_user.mobile_number == "1234567890"
    assert test_user.postal_address == "123 Test St"
    assert test_user.physical_address == "456 Example Rd"
    assert test_user.country == "Testland"
    assert not test_user.email_verified
    assert test_user.last_login is None


def test_user_full_name(test_user):
    """
    Test that the full_name property returns the correct format.

    Args:
        test_user (User): A test user instance.
    """
    assert test_user.full_name == "Test User"


def test_user_record_login(test_user):
    """
    Test that the record_login method correctly updates last_login.

    Args:
        test_user (User): A test user instance.
    """
    assert test_user.last_login is None
    test_user.record_login()
    assert isinstance(test_user.last_login, datetime)


def test_user_verify_email(test_user):
    """
    Test that the verify_email method correctly updates email_verified.

    Args:
        test_user (User): A test user instance.
    """
    assert not test_user.email_verified
    test_user.verify_email()
    assert test_user.email_verified


def test_user_create():
    """
    Test that the create class method correctly instantiates a User from UserCreate.

    This test ensures that data is correctly mapped from the DTO to the User model.
    """
    user_data = UserCreate(
        email="new@example.com",
        password="securepassword",
        first_name="New",
        last_name="User",
        mobile_number="9876543210",
        postal_address="789 Test Blvd",
        physical_address="101 Sample Ave",
        country="Exampleland",
    )
    new_user = User.create(user_data)

    assert new_user.email == "new@example.com"
    assert new_user.password == "securepassword"
    assert new_user.first_name == "New"
    assert new_user.last_name == "User"
    assert new_user.mobile_number == "9876543210"
    assert new_user.postal_address == "789 Test Blvd"
    assert new_user.physical_address == "101 Sample Ave"
    assert new_user.country == "Exampleland"


def test_user_has_permission():
    """
    Test that the has_permission method correctly evaluates user permissions.

    Uses a mock Role instance to simulate permission checking.
    """
    mock_role = MagicMock()
    mock_role.is_active = True
    mock_role.has_permission.return_value = True

    user = User(id=2, email="roleuser@example.com", password="pass")
    user.roles = [mock_role]

    assert user.has_permission("edit_profile") is True
    mock_role.has_permission.assert_called_once_with("edit_profile")


def test_user_is_member_of():
    """
    Test that the is_member_of method correctly checks community membership.
    """
    mock_community = MagicMock()
    mock_community.id = 1

    user = User(id=3, email="member@example.com", password="pass")
    user.communities = [mock_community]

    assert user.is_member_of(1) is True
    assert user.is_member_of(2) is False


def test_user_owns_community():
    """
    Test that the owns_community method correctly checks if the user owns a community.
    """
    mock_community = MagicMock()
    mock_community.id = 2

    user = User(id=4, email="owner@example.com", password="pass")
    user.owned_communities = [mock_community]

    assert user.owns_community(2) is True
    assert user.owns_community(3) is False


def test_user_has_role():
    """
    Test that the has_role method correctly checks assigned roles.
    """
    mock_role = MagicMock()
    mock_role.name = "admin"
    mock_role.is_active = True

    user = User(id=5, email="rolecheck@example.com", password="pass")
    user.roles = [mock_role]

    assert user.has_role("admin") is True
    assert user.has_role("user") is False


def test_user_repr(test_user):
    """
    Test that the __repr__ method correctly formats the string representation.

    Args:
        test_user (User): A test user instance.
    """
    assert repr(test_user) == "User(id=1, email=test@example.com)"
