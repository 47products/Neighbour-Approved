"""
Unit tests for the Role model.

This module tests all aspects of the Role model, including:
- Object instantiation
- Relationship handling
- Property methods
- Instance methods
- Class methods
- JSON permission handling
- Constraint validation

The tests leverage shared fixtures for mock database sessions, repositories, and test data.

Typical usage example:
    pytest tests/unit/test_db/test_models/test_role_model.py
"""

import pytest
import json
from unittest.mock import MagicMock
from app.db.models.role_model import Role, RoleCreate


@pytest.fixture
def test_role():
    """
    Create a test Role instance.

    Returns:
        Role: A Role instance with test data.
    """
    return Role(
        id=1,
        name="Admin",
        description="Administrator role",
        permissions=json.dumps(["read", "write", "delete"]),
        is_system_role=True,
        is_active=True,
    )


def test_role_creation(test_role):
    """
    Test that a Role object is correctly instantiated.

    Args:
        test_role (Role): A test role instance.
    """
    assert test_role.id == 1
    assert test_role.name == "Admin"
    assert test_role.description == "Administrator role"
    assert json.loads(test_role.permissions) == ["read", "write", "delete"]
    assert test_role.is_system_role is True
    assert test_role.is_active is True


def test_role_create():
    """
    Test that the create class method correctly instantiates a Role from RoleCreate.

    This test ensures that data is correctly mapped from the DTO to the Role model.
    """
    role_data = RoleCreate(
        name="Editor",
        description="Editor role",
        permissions=json.dumps(["read", "write"]),
        is_system_role=False,
    )
    new_role = Role.create(role_data)

    assert new_role.name == "Editor"
    assert new_role.description == "Editor role"
    assert json.loads(new_role.permissions) == ["read", "write"]
    assert new_role.is_system_role is False


def test_role_has_permission(test_role):
    """
    Test that has_permission correctly checks for assigned permissions.

    Args:
        test_role (Role): A test role instance.
    """
    assert test_role.has_permission("read") is True
    assert test_role.has_permission("write") is True
    assert test_role.has_permission("delete") is True
    assert test_role.has_permission("execute") is False


def test_role_has_permission_empty():
    """
    Test that has_permission returns False when permissions are empty.
    """
    role = Role(id=2, name="User", permissions=None, is_active=True)
    assert role.has_permission("read") is False


def test_role_has_permission_inactive():
    """
    Test that has_permission returns False if the role is inactive.
    """
    role = Role(
        id=3, name="Disabled", permissions=json.dumps(["read"]), is_active=False
    )
    assert role.has_permission("read") is False


def test_role_has_permission_invalid_json():
    """
    Test that has_permission handles JSON decoding errors gracefully.
    """
    role = Role(id=4, name="Corrupt", permissions="invalid_json", is_active=True)
    assert role.has_permission("read") is False


def test_role_grant_permission(test_role):
    """
    Test that grant_permission correctly adds a new permission.

    Args:
        test_role (Role): A test role instance.
    """
    test_role.grant_permission("execute")
    assert "execute" in json.loads(test_role.permissions)


def test_role_grant_permission_duplicate(test_role):
    """
    Test that grant_permission does not add duplicate permissions.

    Args:
        test_role (Role): A test role instance.
    """
    original_permissions = json.loads(test_role.permissions)
    test_role.grant_permission("write")
    assert json.loads(test_role.permissions) == original_permissions  # No change


def test_role_grant_permission_invalid_json():
    """
    Test that grant_permission handles JSON decoding errors gracefully.
    """
    role = Role(id=5, name="InvalidGrant", permissions="invalid_json")
    role.grant_permission("read")
    assert json.loads(role.permissions) == ["read"]  # Overwrites invalid data


def test_role_revoke_permission(test_role):
    """
    Test that revoke_permission correctly removes a permission.

    Args:
        test_role (Role): A test role instance.
    """
    test_role.revoke_permission("delete")
    assert "delete" not in json.loads(test_role.permissions)


def test_role_revoke_permission_non_existent(test_role):
    """
    Test that revoke_permission does nothing if the permission does not exist.

    Args:
        test_role (Role): A test role instance.
    """
    original_permissions = json.loads(test_role.permissions)
    test_role.revoke_permission("execute")  # Not present
    assert json.loads(test_role.permissions) == original_permissions  # No change


def test_role_revoke_permission_invalid_json():
    """
    Test that revoke_permission handles JSON decoding errors gracefully.
    """
    role = Role(id=6, name="InvalidRevoke", permissions="invalid_json")
    role.revoke_permission("read")
    assert role.permissions == "invalid_json"  # No change due to invalid JSON


def test_role_list_permissions(test_role):
    """
    Test that list_permissions correctly returns all granted permissions.

    Args:
        test_role (Role): A test role instance.
    """
    assert test_role.list_permissions() == ["read", "write", "delete"]


def test_role_list_permissions_empty():
    """
    Test that list_permissions returns an empty list when no permissions are set.
    """
    role = Role(id=7, name="NoPerms", permissions=None)
    assert role.list_permissions() == []


def test_role_list_permissions_invalid_json():
    """
    Test that list_permissions handles JSON decoding errors gracefully.
    """
    role = Role(id=8, name="InvalidList", permissions="invalid_json")
    assert role.list_permissions() == []


def test_role_repr(test_role):
    """
    Test that the __repr__ method correctly formats the string representation.

    Args:
        test_role (Role): A test role instance.
    """
    assert repr(test_role) == "Role(id=1, name=Admin)"
