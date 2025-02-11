"""
Role Service Module.

This module provides the RoleService class, responsible for managing
user role assignments and removals within the application.

Classes:
    RoleService: Handles the assignment and removal of roles for users.
"""

import asyncio
from typing import List
import structlog
from sqlalchemy.orm import Session

from app.db.models.user_model import User
from app.db.models.role_model import Role
from app.services.service_exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
    RoleAssignmentError,
)
from app.services.user_service.user_service_base_user import BaseUserService


class RoleService(BaseUserService):
    """Service for managing user role assignments and removals.

    This service handles all aspects of role management including single and
    bulk role assignments, role compatibility checking, and permission verification.

    Inherits from:
        BaseUserService: Provides core user retrieval and update operations.
    """

    def __init__(self, db: Session) -> None:
        """Initialize the role service.

        Args:
            db: Database session for repository operations
        """
        super().__init__(db)
        self._logger = structlog.get_logger(__name__)

    async def assign_role(self, user_id: int, role_id: int) -> User:
        """Assign a role to a user.

        Args:
            user_id: The unique identifier of the user
            role_id: The unique identifier of the role

        Returns:
            Updated User object with the new role assigned

        Raises:
            ResourceNotFoundError: If user or role not found
            RoleAssignmentError: If role assignment violates rules
        """
        user = await self.get_user(user_id)
        role = await self.db.get(Role, role_id)

        if not role or not role.is_active:
            raise ResourceNotFoundError(f"Role {role_id} not found")

        if role in user.roles:
            return user

        user.roles.append(role)
        await self.db.commit()

        self._logger.info(
            "role_assigned",
            user_id=user_id,
            role_id=role_id,
            role_name=role.name,
        )
        return user

    async def assign_roles(self, user_id: int, role_ids: List[int]) -> User:
        """Assign multiple roles to a user.

        Args:
            user_id: The unique identifier of the user
            role_ids: List of role IDs to assign

        Returns:
            Updated User object with the new roles assigned

        Raises:
            ResourceNotFoundError: If user not found
            RoleAssignmentError: If role assignment violates business rules
        """
        user = await self.get_user(user_id)

        # Validate and retrieve all roles
        roles = []
        for role_id in role_ids:
            role = await self.db.get(Role, role_id)
            if not role or not role.is_active:
                raise ResourceNotFoundError(f"Role {role_id} not found or inactive")
            roles.append(role)

        # Check role compatibility
        if not await self._validate_role_compatibility(user, roles):
            raise RoleAssignmentError("Incompatible role combination")

        # Perform role assignment
        for role in roles:
            if role not in user.roles:
                user.roles.append(role)
                self._logger.info(
                    "role_assigned",
                    user_id=user_id,
                    role_id=role.id,
                    role_name=role.name,
                )

        await self.db.commit()
        return user

    async def remove_role(self, user_id: int, role_id: int) -> User:
        """Remove a role from a user.

        Args:
            user_id: The unique identifier of the user
            role_id: The unique identifier of the role

        Returns:
            Updated User object with the role removed

        Raises:
            ResourceNotFoundError: If user or role not found
            BusinessRuleViolationError: If role removal violates minimum requirements
        """
        user = await self.get_user(user_id)
        role = await self.db.get(Role, role_id)

        if not role:
            raise ResourceNotFoundError(f"Role {role_id} not found")

        if role not in user.roles:
            return user

        # Check minimum role requirements
        remaining_roles = [r for r in user.roles if r.id != role_id]
        if not await self._validate_minimum_roles(remaining_roles):
            raise BusinessRuleViolationError(
                "User must maintain at least one active role"
            )

        user.roles.remove(role)
        await self.db.commit()

        self._logger.info(
            "role_removed",
            user_id=user_id,
            role_id=role_id,
            role_name=role.name,
        )
        return user

    async def remove_roles(self, user_id: int, role_ids: List[int]) -> User:
        """Remove multiple roles from a user.

        Args:
            user_id: The unique identifier of the user
            role_ids: List of role IDs to remove

        Returns:
            Updated User object

        Raises:
            ResourceNotFoundError: If user not found
            BusinessRuleViolationError: If removal violates minimum requirements
        """
        user = await self.get_user(user_id)
        roles_to_remove = [role for role in user.roles if role.id in role_ids]

        # Check minimum role requirements
        remaining_roles = [role for role in user.roles if role.id not in role_ids]
        if not await self._validate_minimum_roles(remaining_roles):
            raise BusinessRuleViolationError(
                "User must maintain at least one active role"
            )

        # Perform role removal
        for role in roles_to_remove:
            user.roles.remove(role)
            self._logger.info(
                "role_removed",
                user_id=user_id,
                role_id=role.id,
                role_name=role.name,
            )

        await self.db.commit()
        return user

    async def get_user_roles(self, user_id: int) -> List[Role]:
        """Retrieve all active roles assigned to a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            List of active roles assigned to user

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        return [role for role in user.roles if role.is_active]

    async def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has a specific permission through any role.

        Args:
            user_id: The unique identifier of the user
            permission: Permission to check

        Returns:
            Whether user has the specified permission
        """
        user = await self.get_user(user_id)
        if not user:
            return False

        return any(
            await asyncio.gather(
                *(
                    role.has_permission(permission)
                    for role in user.roles
                    if role.is_active
                )
            )
        )

    async def _validate_role_compatibility(
        self, user: User, new_roles: List[Role]
    ) -> bool:
        """Validate compatibility between existing and new roles.

        Args:
            user: User receiving new roles
            new_roles: Roles to be assigned

        Returns:
            Whether role combination is valid
        """
        existing_role_names = {role.name for role in user.roles}
        new_role_names = {role.name for role in new_roles}

        # Example compatibility rules
        incompatible_pairs = {
            frozenset({"admin", "basic_user"}),
            frozenset({"moderator", "restricted_user"}),
        }

        combined_roles = existing_role_names.union(new_role_names)
        for role_pair in incompatible_pairs:
            if len(role_pair.intersection(combined_roles)) > 1:
                return False

        return True

    async def _validate_minimum_roles(self, roles: List[Role]) -> bool:
        """Validate that role set meets minimum requirements.

        Args:
            roles: List of roles to validate

        Returns:
            Whether role set meets requirements
        """
        active_roles = [role for role in roles if role.is_active]
        if not active_roles:
            return False

        return True
