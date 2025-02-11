"""
Unit tests for the RoleService module.

This module tests the RoleService class, which manages role assignments and removals
for users. It verifies the behavior of single and bulk role assignments and removals,
permission checking, and role compatibility and minimum requirements validations.

Key Methods Tested:
    - assign_role: Assign a single role.
    - assign_roles: Assign multiple roles.
    - remove_role: Remove a single role.
    - remove_roles: Remove multiple roles.
    - get_user_roles: Retrieve only active roles.
    - has_permission: Check if a user has a given permission.
    - _validate_role_compatibility: Verify that new roles are compatible with existing roles.
    - _validate_minimum_roles: Ensure that the user retains at least one active role.

To run the tests, use:
    pytest tests/unit/test_services/test_user_service/test_role_service.py

Dependencies:
    - pytest
    - unittest.mock for AsyncMock and MagicMock
    - RoleService and related exception classes
"""

import pytest
from unittest.mock import AsyncMock
from app.services.user_service.user_service_role import RoleService
from app.services.service_exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
    RoleAssignmentError,
)
from app.db.models.role_model import Role


@pytest.mark.asyncio
async def test_assign_role_success(dummy_db, mock_user):
    """
    Test that assign_role successfully assigns an active role to a user.

    The test simulates a user with no roles. When assign_role is called,
    it retrieves an active role and appends it to the user's roles, commits the change,
    and logs the assignment.
    """
    role = Role(id=1, name="member", is_active=True)
    mock_user.roles = []
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(return_value=role)
    dummy_db.commit = AsyncMock()

    result = await service.assign_role(mock_user.id, role.id)
    assert role in result.roles
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_assign_roles_with_existing_role(dummy_db, mock_user):
    """
    Test that assign_roles only assigns new roles and does not duplicate roles
    that are already assigned.

    This test simulates a scenario where the user already has one role (role1)
    and assign_roles is called with a list of role IDs including the existing role (1)
    and a new role (2). The method should only append the new role (role2) to the user's roles.

    Expected Outcome:
        - The user's roles list contains role1 (once) and role2.
        - The new role is assigned only if it is not already present.
    """
    # Create two roles: role1 (already assigned) and role2 (new).
    role1 = Role(id=1, name="member", is_active=True)
    role2 = Role(id=2, name="editor", is_active=True)
    # Pre-assign role1 to the mock user.
    mock_user.roles = [role1]

    # Instantiate the RoleService with the dummy database.
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    # Stub dummy_db.get to return role1 for id 1 and role2 for id 2.
    dummy_db.get = AsyncMock(side_effect=lambda model, id: role1 if id == 1 else role2)
    # Stub compatibility validation to pass.
    service._validate_role_compatibility = AsyncMock(return_value=True)
    dummy_db.commit = AsyncMock()

    # Call assign_roles with role IDs [1, 2]; role 1 is already assigned.
    result = await service.assign_roles(mock_user.id, [1, 2])

    # Verify that:
    #   - The user's roles list contains exactly two roles.
    #   - Role1 is not duplicated.
    #   - Role2 is successfully added.
    assert len(result.roles) == 2
    assert result.roles.count(role1) == 1
    assert role2 in result.roles


@pytest.mark.asyncio
async def test_assign_role_already_assigned(dummy_db, mock_user):
    """
    Test that assign_role returns the user unchanged if the role is already assigned.

    When the role is already in the user's roles, the method should return immediately
    without calling commit.
    """
    role = Role(id=1, name="member", is_active=True)
    mock_user.roles = [role]
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(return_value=role)
    dummy_db.commit = AsyncMock()

    result = await service.assign_role(mock_user.id, role.id)
    dummy_db.commit.assert_not_called()
    assert result == mock_user


@pytest.mark.asyncio
async def test_assign_role_role_not_found(dummy_db, mock_user):
    """
    Test that assign_role raises ResourceNotFoundError when the role is not found.

    The dummy_db.get call returns None, causing the method to raise an error.
    """
    mock_user.roles = []
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(return_value=None)

    with pytest.raises(ResourceNotFoundError, match="Role 1 not found"):
        await service.assign_role(mock_user.id, 1)


@pytest.mark.asyncio
async def test_assign_role_inactive_role(dummy_db, mock_user):
    """
    Test that assign_role raises ResourceNotFoundError when the role is inactive.

    An inactive role should be treated as not found.
    """
    role = Role(id=1, name="member", is_active=False)
    mock_user.roles = []
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(return_value=role)

    with pytest.raises(ResourceNotFoundError, match="Role 1 not found"):
        await service.assign_role(mock_user.id, role.id)


@pytest.mark.asyncio
async def test_assign_roles_success(dummy_db, mock_user):
    """
    Test that assign_roles successfully assigns multiple roles to a user.

    For valid role IDs, the method should retrieve and validate roles, check compatibility,
    assign roles that are not already present, and commit the changes.
    """
    role1 = Role(id=1, name="member", is_active=True)
    role2 = Role(id=2, name="editor", is_active=True)
    mock_user.roles = []
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    # Dummy db.get returns role1 for id 1 and role2 for id 2.
    dummy_db.get = AsyncMock(side_effect=lambda model, id: role1 if id == 1 else role2)
    # Force compatibility validation to pass.
    service._validate_role_compatibility = AsyncMock(return_value=True)
    dummy_db.commit = AsyncMock()

    result = await service.assign_roles(mock_user.id, [1, 2])
    assert role1 in result.roles
    assert role2 in result.roles
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_assign_roles_incompatible(dummy_db, mock_user):
    """
    Test that assign_roles raises RoleAssignmentError when the new roles are incompatible.

    The _validate_role_compatibility method is patched to return False.
    """
    role1 = Role(id=1, name="admin", is_active=True)
    role2 = Role(id=2, name="basic_user", is_active=True)
    mock_user.roles = []
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(side_effect=lambda model, id: role1 if id == 1 else role2)
    service._validate_role_compatibility = AsyncMock(return_value=False)

    with pytest.raises(RoleAssignmentError, match="Incompatible role combination"):
        await service.assign_roles(mock_user.id, [1, 2])


@pytest.mark.asyncio
async def test_assign_roles_role_not_found(dummy_db, mock_user):
    """
    Test that assign_roles raises ResourceNotFoundError when one of the roles is not found or inactive.

    For one of the role IDs, dummy_db.get returns None.
    """
    role1 = Role(id=1, name="member", is_active=True)
    mock_user.roles = []
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(side_effect=lambda model, id: role1 if id == 1 else None)

    with pytest.raises(ResourceNotFoundError, match="Role 2 not found or inactive"):
        await service.assign_roles(mock_user.id, [1, 2])


@pytest.mark.asyncio
async def test_remove_role_success(dummy_db, mock_user):
    """
    Test that remove_role successfully removes a role from the user when minimum requirements are met.

    The method removes the role from the user's roles, commits the change, and logs the removal.
    """
    role = Role(id=1, name="member", is_active=True)
    mock_user.roles = [role]
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(return_value=role)
    service._validate_minimum_roles = AsyncMock(return_value=True)
    dummy_db.commit = AsyncMock()

    result = await service.remove_role(mock_user.id, role.id)
    assert role not in result.roles
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_remove_role_not_assigned(dummy_db, mock_user):
    """
    Test that remove_role returns the user unchanged if the role is not assigned.

    No removal or commit should occur if the user does not have the role.
    """
    role = Role(id=1, name="member", is_active=True)
    mock_user.roles = []
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(return_value=role)
    dummy_db.commit = AsyncMock()

    result = await service.remove_role(mock_user.id, role.id)
    assert result == mock_user
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_remove_role_not_found(dummy_db, mock_user):
    """
    Test that remove_role raises ResourceNotFoundError when the role is not found.

    dummy_db.get returns None, causing the method to raise an error.
    """
    mock_user.roles = []
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(return_value=None)

    with pytest.raises(ResourceNotFoundError, match="Role 1 not found"):
        await service.remove_role(mock_user.id, 1)


@pytest.mark.asyncio
async def test_remove_role_minimum_violation(dummy_db, mock_user):
    """
    Test that remove_role raises BusinessRuleViolationError when removal violates minimum role requirements.

    If removing the role would leave the user with no active roles, the method should raise an error.
    """
    role = Role(id=1, name="member", is_active=True)
    mock_user.roles = [role]
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.get = AsyncMock(return_value=role)
    service._validate_minimum_roles = AsyncMock(return_value=False)

    with pytest.raises(
        BusinessRuleViolationError, match="User must maintain at least one active role"
    ):
        await service.remove_role(mock_user.id, role.id)


@pytest.mark.asyncio
async def test_remove_roles_success(dummy_db, mock_user):
    """
    Test that remove_roles successfully removes multiple roles from the user.

    Roles that match the provided IDs should be removed, the changes committed, and the updated user returned.
    """
    role1 = Role(id=1, name="member", is_active=True)
    role2 = Role(id=2, name="editor", is_active=True)
    mock_user.roles = [role1, role2]
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    service._validate_minimum_roles = AsyncMock(return_value=True)
    dummy_db.commit = AsyncMock()

    result = await service.remove_roles(mock_user.id, [1])
    assert role1 not in result.roles
    assert role2 in result.roles
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_remove_roles_minimum_violation(dummy_db, mock_user):
    """
    Test that remove_roles raises BusinessRuleViolationError when removal violates minimum role requirements.

    If removal of the specified roles would leave the user without any active roles, an error should be raised.
    """
    role1 = Role(id=1, name="member", is_active=True)
    role2 = Role(id=2, name="editor", is_active=True)
    mock_user.roles = [role1, role2]
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    service._validate_minimum_roles = AsyncMock(return_value=False)

    with pytest.raises(
        BusinessRuleViolationError, match="User must maintain at least one active role"
    ):
        await service.remove_roles(mock_user.id, [1, 2])


@pytest.mark.asyncio
async def test_get_user_roles(dummy_db, mock_user):
    """
    Test that get_user_roles returns only the active roles assigned to the user.

    Inactive roles should be filtered out.
    """
    active_role = Role(id=1, name="member", is_active=True)
    inactive_role = Role(id=2, name="editor", is_active=False)
    mock_user.roles = [active_role, inactive_role]
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)

    result = await service.get_user_roles(mock_user.id)
    assert active_role in result
    assert inactive_role not in result


@pytest.mark.asyncio
async def test_has_permission_no_user(dummy_db):
    """
    Test that has_permission returns False when the user is not found.
    """
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=None)
    result = await service.has_permission(1, "edit")
    assert result is False


@pytest.mark.asyncio
async def test_has_permission_success(dummy_db, mock_user):
    """
    Test that has_permission returns True when at least one active role grants the permission.

    Each role's has_permission method is simulated to return True for the requested permission.
    """

    async def has_perm(permission: str) -> bool:
        return permission == "edit"

    role = Role(id=1, name="member", is_active=True)
    role.has_permission = has_perm
    mock_user.roles = [role]
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)

    result = await service.has_permission(mock_user.id, "edit")
    assert result is True


@pytest.mark.asyncio
async def test_has_permission_none_grants(dummy_db, mock_user):
    """
    Test that has_permission returns False when no active role grants the permission.
    """

    async def has_perm(permission: str) -> bool:
        return False

    role = Role(id=1, name="member", is_active=True)
    role.has_permission = has_perm
    mock_user.roles = [role]
    service = RoleService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)

    result = await service.has_permission(mock_user.id, "delete")
    assert result is False


@pytest.mark.asyncio
async def test_validate_role_compatibility_incompatible(dummy_db, mock_user):
    """
    Test that _validate_role_compatibility returns False when there is an incompatible role combination.

    For example, if the user already has an 'admin' role and a new role 'basic_user' is to be assigned,
    the combination is incompatible.
    """
    admin_role = Role(id=1, name="admin", is_active=True)
    basic_role = Role(id=2, name="basic_user", is_active=True)
    mock_user.roles = [admin_role]
    service = RoleService(dummy_db)
    result = await service._validate_role_compatibility(mock_user, [basic_role])
    assert result is False


@pytest.mark.asyncio
async def test_validate_role_compatibility_compatible(dummy_db, mock_user):
    """
    Test that _validate_role_compatibility returns True when the combination of roles is compatible.
    """
    member_role = Role(id=1, name="member", is_active=True)
    editor_role = Role(id=2, name="editor", is_active=True)
    mock_user.roles = [member_role]
    service = RoleService(dummy_db)
    result = await service._validate_role_compatibility(mock_user, [editor_role])
    assert result is True


@pytest.mark.asyncio
async def test_validate_minimum_roles_no_active():
    """
    Test that _validate_minimum_roles returns False when no active roles are present.
    """
    service = RoleService(AsyncMock())
    roles = [
        Role(id=1, name="member", is_active=False),
        Role(id=2, name="editor", is_active=False),
    ]
    result = await service._validate_minimum_roles(roles)
    assert result is False


@pytest.mark.asyncio
async def test_validate_minimum_roles_with_active():
    """
    Test that _validate_minimum_roles returns True when at least one active role is present.
    """
    service = RoleService(AsyncMock())
    roles = [
        Role(id=1, name="member", is_active=False),
        Role(id=2, name="editor", is_active=True),
    ]
    result = await service._validate_minimum_roles(roles)
    assert result is True
