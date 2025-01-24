"""
Community service implementation module.

This module implements the core business logic for community management, including
relationship handling, role management, and ownership transfers. It ensures proper
separation of concerns by encapsulating business rules separate from data access.

The module provides comprehensive handling of:
- Community relationships with privacy compatibility checks
- Role assignments and hierarchies
- Ownership transfers with validation
- Audit logging and error tracking
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Set, Tuple, Any
from sqlalchemy.orm import Session
import structlog

from app.services.base import BaseService
from app.services.service_interfaces import ICommunityService
from app.services.service_exceptions import (
    ValidationError,
    AccessDeniedError,
    ResourceNotFoundError,
    BusinessRuleViolationError,
    QuotaExceededError,
    RoleAssignmentError,
    StateError,
)
from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.user_model import User
from app.db.models.community_member_model import CommunityMember
from app.db.repositories.community_repository import CommunityRepository
from app.api.v1.schemas.community_schema import CommunityCreate, CommunityUpdate


class CommunityService(
    BaseService[Community, CommunityCreate, CommunityUpdate], ICommunityService
):
    """
    Service for managing community-related operations and business logic.

    This service implements comprehensive community management operations including
    membership control, relationship management, role assignments, and ownership
    transfers. It encapsulates all community-related business rules and validation
    logic.

    Attributes:
        MAX_MEMBERS_FREE (int): Maximum members for free communities
        MAX_RELATIONSHIPS (int): Maximum number of related communities
        RESTRICTED_NAMES (set): Names not allowed for communities
        VALID_ROLES (set): Valid community member roles
        ROLE_HIERARCHY (dict): Role hierarchy definitions
    """

    MAX_MEMBERS_FREE = 50
    MAX_RELATIONSHIPS = 10
    RESTRICTED_NAMES = {"admin", "system", "support", "test"}
    VALID_ROLES = {"owner", "admin", "moderator", "member"}
    ROLE_HIERARCHY = {
        "owner": ["admin", "moderator", "member"],
        "admin": ["moderator", "member"],
        "moderator": ["member"],
        "member": [],
    }

    def __init__(self, db: Session):
        """
        Initialize the community service.

        Args:
            db: Database session for repository operations
        """
        super().__init__(
            model=Community,
            repository=CommunityRepository(db),
            logger_name="CommunityService",
        )

    async def transfer_ownership(
        self,
        community_id: int,
        new_owner_id: int,
        current_owner_id: int,
    ) -> Community:
        """
        Transfer ownership of a community to a new user.

        This method implements the complete ownership transfer workflow,
        including validation, role updates, and audit logging.

        Args:
            community_id: Community's unique identifier
            new_owner_id: User ID of the new owner
            current_owner_id: User ID of the current owner

        Returns:
            Updated community instance

        Raises:
            ResourceNotFoundError: If community or users not found
            AccessDeniedError: If transfer is not authorized
            BusinessRuleViolationError: If transfer violates rules
            StateError: If community is in invalid state for transfer
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        if community.owner_id != current_owner_id:
            raise AccessDeniedError("Only the current owner can transfer ownership")

        if not community.is_active:
            raise StateError("Cannot transfer ownership of inactive community")

        new_owner = await self.db.get(User, new_owner_id)
        if not new_owner:
            raise ResourceNotFoundError(f"New owner {new_owner_id} not found")

        try:
            # Validate transfer
            await self._validate_ownership_transfer(community, new_owner)

            # Store old owner info for role updates
            old_owner_id = community.owner_id

            # Update ownership
            community.owner_id = new_owner_id

            # Update member roles and associations
            await self._update_roles_after_transfer(
                community, old_owner_id, new_owner_id
            )

            await self.db.commit()

            self._logger.info(
                "ownership_transferred",
                community_id=community_id,
                old_owner_id=old_owner_id,
                new_owner_id=new_owner_id,
            )

            return community

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "ownership_transfer_failed",
                community_id=community_id,
                new_owner_id=new_owner_id,
                error=str(e),
            )
            raise

    async def _validate_ownership_transfer(
        self,
        community: Community,
        new_owner: User,
    ) -> None:
        """
        Validate community ownership transfer against business rules.

        Args:
            community: Community being transferred
            new_owner: Prospective new owner

        Raises:
            BusinessRuleViolationError: If transfer violates rules
            ValidationError: If validation fails
        """
        if not new_owner.is_active:
            raise BusinessRuleViolationError("New owner account must be active")

        if not new_owner.email_verified:
            raise BusinessRuleViolationError(
                "New owner must have a verified email address"
            )

        # Check ownership limits
        owned_communities = await self._get_user_owned_communities(new_owner.id)
        if len(owned_communities) >= await self._get_user_community_limit(new_owner.id):
            raise BusinessRuleViolationError(
                "New owner has reached maximum number of owned communities"
            )

        # Check privacy level compatibility
        if community.privacy_level == PrivacyLevel.PRIVATE and not any(
            role.name == "premium_user" for role in new_owner.roles if role.is_active
        ):
            raise BusinessRuleViolationError(
                "Private communities require premium membership"
            )

        # Validate existing role assignments
        member_role = await self._get_member_role(community, new_owner)
        if member_role and member_role not in {"admin", "moderator"}:
            raise ValidationError(
                "New owner must be an admin or moderator before transfer"
            )

    async def _update_roles_after_transfer(
        self,
        community: Community,
        old_owner_id: int,
        new_owner_id: int,
    ) -> None:
        """
        Update roles and permissions after ownership transfer.

        Args:
            community: Community being transferred
            old_owner_id: Previous owner's user ID
            new_owner_id: New owner's user ID

        Raises:
            StateError: If role updates fail
        """
        try:
            # Update old owner's role to admin
            old_owner_member = await self._get_community_member(
                community, User(id=old_owner_id)
            )
            if old_owner_member:
                old_owner_member.role = "admin"
                old_owner_member.role_assigned_at = datetime.now(UTC)
                old_owner_member.role_assigned_by = new_owner_id

            # Update new owner's role
            new_owner_member = await self._get_community_member(
                community, User(id=new_owner_id)
            )
            if new_owner_member:
                new_owner_member.role = "owner"
                new_owner_member.role_assigned_at = datetime.now(UTC)
            else:
                # Create new owner membership if not exists
                new_owner_member = CommunityMember(
                    community_id=community.id,
                    user_id=new_owner_id,
                    role="owner",
                    role_assigned_at=datetime.now(UTC),
                    is_active=True,
                )
                self.db.add(new_owner_member)

            await self.db.commit()

        except Exception as e:
            self._logger.error(
                "role_update_failed",
                community_id=community.id,
                old_owner_id=old_owner_id,
                new_owner_id=new_owner_id,
                error=str(e),
            )
            raise StateError("Failed to update roles after transfer") from e

    async def manage_community_relationships(
        self,
        community_id: int,
        related_community_id: int,
        action: str,
    ) -> bool:
        """
        Manage relationships between communities.

        This method handles the creation and management of bidirectional
        relationships between communities, including validation of relationship
        rules and maintenance of relationship integrity.

        Args:
            community_id: ID of the primary community
            related_community_id: ID of the community to relate to
            action: Relationship action ("add" or "remove")

        Returns:
            bool: True if relationship was successfully managed

        Raises:
            ResourceNotFoundError: If either community is not found
            ValidationError: If relationship action is invalid
            BusinessRuleViolationError: If relationship violates rules
            QuotaExceededError: If relationship limit is exceeded
        """
        community = await self.get_community(community_id)
        related_community = await self.get_community(related_community_id)

        if not community or not related_community:
            raise ResourceNotFoundError("One or both communities not found")

        if action not in {"add", "remove"}:
            raise ValidationError(f"Invalid relationship action: {action}")

        try:
            if action == "add":
                await self._add_community_relationship(community, related_community)
            else:
                await self._remove_community_relationship(community, related_community)

            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "relationship_management_failed",
                community_id=community_id,
                related_community_id=related_community_id,
                action=action,
                error=str(e),
            )
            raise

    async def _add_community_relationship(
        self,
        community: Community,
        related_community: Community,
    ) -> None:
        """
        Add a bidirectional relationship between communities.

        Args:
            community: Primary community
            related_community: Community to relate to

        Raises:
            BusinessRuleViolationError: If relationship cannot be created
            QuotaExceededError: If relationship limit reached
        """
        if related_community in community.related_communities:
            return

        if len(community.related_communities) >= self.MAX_RELATIONSHIPS:
            raise QuotaExceededError(
                f"Community has reached maximum relationships ({self.MAX_RELATIONSHIPS})"
            )

        await self._validate_relationship_rules(community, related_community)

        # Create bidirectional relationship
        community.related_communities.append(related_community)
        related_community.related_communities.append(community)

        self._logger.info(
            "relationship_added",
            community_id=community.id,
            related_community_id=related_community.id,
        )

    async def _validate_relationship_rules(
        self,
        community: Community,
        related_community: Community,
    ) -> None:
        """
        Validate rules for community relationships.

        Args:
            community: Primary community
            related_community: Community to relate to

        Raises:
            BusinessRuleViolationError: If relationship violates rules
        """
        # Prevent self-relationships
        if community.id == related_community.id:
            raise BusinessRuleViolationError("Community cannot relate to itself")

        # Check privacy level compatibility
        if community.privacy_level == PrivacyLevel.PRIVATE:
            if related_community.privacy_level == PrivacyLevel.PUBLIC:
                raise BusinessRuleViolationError(
                    "Private communities cannot relate to public communities"
                )

        # Check for circular relationships
        if await self._would_create_circular_relationship(community, related_community):
            raise BusinessRuleViolationError(
                "Relationship would create circular reference"
            )

        # Validate inherited relationships
        parent_relationships = await self._get_inherited_relationships(community)
        if related_community in parent_relationships:
            raise BusinessRuleViolationError(
                "Cannot create explicit relationship with inherited community"
            )

    async def _would_create_circular_relationship(
        self,
        community: Community,
        related_community: Community,
    ) -> bool:
        """
        Check if adding a relationship would create a circular reference.

        Args:
            community: Primary community
            related_community: Community to relate to

        Returns:
            bool: Whether relationship would create circular reference
        """
        visited: Set[int] = set()

        def check_circular(current: Community) -> bool:
            if current.id in visited:
                return True
            visited.add(current.id)
            for related in current.related_communities:
                if check_circular(related):
                    return True
            visited.remove(current.id)
            return False

    async def manage_membership(
        self,
        community_id: int,
        user_id: int,
        action: str,
        *,
        inviter_id: Optional[int] = None,
        role: str = "member",
    ) -> bool:
        """
        Manage community membership operations.

        This method handles all membership-related operations including invitations,
        approvals, and membership status changes. It enforces membership limits and
        privacy rules.

        Args:
            community_id: Community's unique identifier
            user_id: User ID to manage
            action: Membership action ("invite", "approve", "reject", "leave")
            inviter_id: Optional ID of user initiating invitation
            role: Role to assign (defaults to "member")

        Returns:
            bool: True if operation was successful

        Raises:
            ValidationError: If action is invalid
            BusinessRuleViolationError: If operation violates rules
            QuotaExceededError: If member limit reached
            AccessDeniedError: If operation not permitted
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        user = await self.db.get(User, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        try:
            # Validate action
            if action not in {"invite", "approve", "reject", "leave"}:
                raise ValidationError(f"Invalid membership action: {action}")

            # Check member limits for new members
            if action in {"invite", "approve"}:
                await self._check_member_limits(community)

            # Process based on privacy level and action
            if community.privacy_level == PrivacyLevel.INVITATION_ONLY:
                return await self._handle_invitation_only_membership(
                    community, user, action, inviter_id, role
                )
            elif community.privacy_level == PrivacyLevel.PRIVATE:
                return await self._handle_private_membership(
                    community, user, action, role
                )
            else:  # PUBLIC
                return await self._handle_public_membership(
                    community, user, action, role
                )

        except Exception as e:
            self._logger.error(
                "membership_management_failed",
                community_id=community_id,
                user_id=user_id,
                action=action,
                error=str(e),
            )
            raise

    async def _check_member_limits(self, community: Community) -> None:
        """
        Check if community can accept new members.

        Args:
            community: Community to check

        Raises:
            QuotaExceededError: If member limit reached
        """
        # Get effective member limit
        member_limit = await self._get_community_member_limit(community)
        if community.total_count >= member_limit:
            raise QuotaExceededError(
                f"Community has reached member limit of {member_limit}"
            )

    async def _process_invitation(
        self,
        community: Community,
        user: User,
        inviter_id: Optional[int],
        role: str,
    ) -> bool:
        """Process a new member invitation."""
        if not inviter_id:
            raise ValidationError("Inviter ID required for invitations")

        inviter = await self.db.get(User, inviter_id)
        if not inviter:
            raise ResourceNotFoundError(f"Inviter {inviter_id} not found")

        await self._validate_inviter_permission(community, inviter)

        member = CommunityMember(
            community_id=community.id,
            user_id=user.id,
            role=role,
            is_active=False,
            role_assigned_by=inviter_id,
        )
        self.db.add(member)
        await self.db.commit()

        self._logger.info(
            "member_invited",
            community_id=community.id,
            user_id=user.id,
            inviter_id=inviter_id,
        )
        return True

    async def _validate_inviter_permission(
        self, community: Community, inviter: User
    ) -> None:
        """Validate if user has permission to invite members."""
        inviter_member = await self._get_community_member(community, inviter)
        if not inviter_member or inviter_member.role not in {
            "owner",
            "admin",
            "moderator",
        }:
            raise AccessDeniedError("Insufficient permission to invite members")

    async def _process_invitation_response(
        self,
        community: Community,
        user: User,
        action: str,
    ) -> bool:
        """Process an invitation approval or rejection."""
        member = await self._get_community_member(community, user)
        if not member or member.is_active:
            raise BusinessRuleViolationError("No pending invitation found")

        if action == "approve":
            await self._activate_membership(member, community)
        else:  # reject
            self.db.delete(member)

        await self.db.commit()

        self._logger.info(
            f"invitation_{action}ed",
            community_id=community.id,
            user_id=user.id,
        )
        return True

    async def _activate_membership(
        self,
        member: CommunityMember,
        community: Community,
    ) -> None:
        """Activate a pending membership."""
        member.is_active = True
        member.role_assigned_at = datetime.now(UTC)
        community.total_count += 1
        community.active_count += 1

    async def _handle_membership_by_privacy(
        self,
        community: Community,
        user: User,
        action: str,
        inviter_id: Optional[int] = None,
        role: str = "member",
    ) -> bool:
        """Handle membership based on community privacy level."""
        if action == "leave":
            return await self._handle_member_leave(community, user)

        if (
            action == "invite"
            and community.privacy_level == PrivacyLevel.INVITATION_ONLY
        ):
            return await self._process_invitation(community, user, inviter_id, role)

        if (
            action in {"approve", "reject"}
            and community.privacy_level == PrivacyLevel.INVITATION_ONLY
        ):
            return await self._process_invitation_response(community, user, action)

        if action == "approve":
            # Verify premium requirement for private communities
            if community.privacy_level == PrivacyLevel.PRIVATE and not any(
                role.name == "premium_user" for role in user.roles if role.is_active
            ):
                raise BusinessRuleViolationError(
                    "Private communities require premium membership"
                )

            member = CommunityMember(
                community_id=community.id,
                user_id=user.id,
                role=role,
                is_active=True,
                role_assigned_at=datetime.now(UTC),
            )
            self.db.add(member)
            community.total_count += 1
            community.active_count += 1
            await self.db.commit()

            self._logger.info(
                "member_added",
                community_id=community.id,
                user_id=user.id,
                role=role,
            )
            return True

        return False

    async def _handle_member_leave(
        self,
        community: Community,
        user: User,
    ) -> bool:
        """
        Handle member leaving a community.

        Args:
            community: Community being left
            user: Departing user

        Returns:
            bool: True if leave successful

        Raises:
            BusinessRuleViolationError: If leave not allowed
        """
        member = await self._get_community_member(community, user)
        if not member or not member.is_active:
            return False

        if member.role == "owner":
            raise BusinessRuleViolationError("Owner cannot leave community")

        member.is_active = False
        community.active_count -= 1
        await self.db.commit()

        self._logger.info(
            "member_left",
            community_id=community.id,
            user_id=user.id,
        )
        return True

    async def _get_community_member_limit(self, community: Community) -> int:
        """
        Get effective member limit for community.

        This method determines the maximum allowed members based on
        community settings and subscription tier.

        Args:
            community: Community to check

        Returns:
            int: Maximum allowed members
        """
        # Check for premium features
        owner = await self.db.get(User, community.owner_id)
        if owner and any(
            role.name == "premium_user" for role in owner.roles if role.is_active
        ):
            return 500  # Premium limit
        return self.MAX_MEMBERS_FREE

    async def manage_member_roles(
        self,
        community_id: int,
        user_id: int,
        role: str,
        assigned_by: Optional[int] = None,
    ) -> bool:
        """
        Manage member roles within a community.

        This method handles role assignment and updates for community members,
        including validation of role assignments and proper audit logging.

        Args:
            community_id: Community's unique identifier
            user_id: User receiving the role
            role: Role to assign
            assigned_by: ID of user making the assignment

        Returns:
            bool: True if role was successfully managed

        Raises:
            ResourceNotFoundError: If community or user not found
            ValidationError: If role is invalid
            BusinessRuleViolationError: If role assignment violates rules
            RoleAssignmentError: If role assignment fails
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        user = await self.db.get(User, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        try:
            # Validate role assignment
            if role not in self.VALID_ROLES:
                raise ValidationError(f"Invalid role: {role}")

            # Validate assignment permissions
            if assigned_by:
                assigner = await self.db.get(User, assigned_by)
                if not assigner:
                    raise ResourceNotFoundError(
                        f"Assigning user {assigned_by} not found"
                    )
                await self._validate_role_assignment_permission(
                    community, assigner, role
                )

            # Get or create member association
            member = await self._get_community_member(community, user)
            if not member:
                # Create new member association
                member = CommunityMember(
                    community_id=community.id,
                    user_id=user.id,
                    role=role,
                    role_assigned_at=datetime.now(UTC),
                    role_assigned_by=assigned_by,
                    is_active=True,
                )
                self.db.add(member)
            else:
                # Update existing member's role
                member.role = role
                member.role_assigned_at = datetime.now(UTC)
                member.role_assigned_by = assigned_by

            await self.db.commit()

            self._logger.info(
                "member_role_managed",
                community_id=community_id,
                user_id=user_id,
                role=role,
                assigned_by=assigned_by,
                action="created" if not member else "updated",
            )
            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "member_role_management_failed",
                community_id=community_id,
                user_id=user_id,
                role=role,
                error=str(e),
            )
            raise RoleAssignmentError(f"Failed to manage role: {str(e)}")

    async def _validate_role_assignment_permission(
        self,
        community: Community,
        assigner: User,
        role: str,
    ) -> None:
        """
        Validate if user has permission to assign a role.

        Args:
            community: Target community
            assigner: User attempting to assign role
            role: Role to assign

        Raises:
            AccessDeniedError: If user cannot assign role
            BusinessRuleViolationError: If role assignment violates rules
        """
        if assigner.id == community.owner_id:
            return

        assigner_member = await self._get_community_member(community, assigner)
        if not assigner_member:
            raise AccessDeniedError("Assigner is not a community member")

        assigner_role = assigner_member.role
        if assigner_role not in self.ROLE_HIERARCHY:
            raise AccessDeniedError("Invalid assigner role")

        # Check if assigner can assign this role
        assignable_roles = self.ROLE_HIERARCHY[assigner_role]
        if role not in assignable_roles:
            raise AccessDeniedError(f"Role '{assigner_role}' cannot assign '{role}'")

    async def get_member_roles(
        self,
        community_id: int,
        *,
        role_filter: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Tuple[int, str]]:
        """
        Get community members and their roles.

        Args:
            community_id: Community's unique identifier
            role_filter: Optional role to filter by
            active_only: Whether to include only active members

        Returns:
            List of tuples containing user ID and role

        Raises:
            ResourceNotFoundError: If community not found
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        query = self.db.query(CommunityMember).filter(
            CommunityMember.community_id == community_id
        )

        if role_filter:
            if role_filter not in self.VALID_ROLES:
                raise ValidationError(f"Invalid role filter: {role_filter}")
            query = query.filter(CommunityMember.role == role_filter)

        if active_only:
            query = query.filter(CommunityMember.is_active.is_(True))

        members = await query.all()
        return [(member.user_id, member.role) for member in members]

    async def update_member_status(
        self,
        community_id: int,
        user_id: int,
        is_active: bool,
        updated_by: Optional[int] = None,
    ) -> bool:
        """
        Update a member's active status.

        Args:
            community_id: Community's unique identifier
            user_id: Member's user ID
            is_active: New active status
            updated_by: ID of user making the update

        Returns:
            bool: True if status was updated

        Raises:
            ResourceNotFoundError: If community or member not found
            AccessDeniedError: If update not allowed
            StateError: If update fails
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        member = await self._get_community_member(community, User(id=user_id))
        if not member:
            raise ResourceNotFoundError(f"Member {user_id} not found")

        try:
            # Validate update permission
            if updated_by:
                await self._validate_member_update_permission(
                    community, member, updated_by
                )

            # Cannot deactivate owner
            if (
                member.role == "owner"
                and not is_active
                and member.user_id == community.owner_id
            ):
                raise BusinessRuleViolationError("Cannot deactivate community owner")

            old_status = member.is_active
            member.is_active = is_active

            if old_status != is_active:
                # Update community member counts
                if is_active:
                    community.active_count += 1
                else:
                    community.active_count -= 1

            await self.db.commit()

            self._logger.info(
                "member_status_updated",
                community_id=community_id,
                user_id=user_id,
                is_active=is_active,
                updated_by=updated_by,
            )
            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "member_status_update_failed",
                community_id=community_id,
                user_id=user_id,
                error=str(e),
            )
            raise StateError(f"Failed to update member status: {str(e)}")

    async def _validate_member_update_permission(
        self,
        community: Community,
        target_member: CommunityMember,
        updater_id: int,
    ) -> None:
        """
        Validate if user can update a member's status.

        Args:
            community: Target community
            target_member: Member being updated
            updater_id: ID of user attempting update

        Raises:
            AccessDeniedError: If update not allowed
        """
        if updater_id == community.owner_id:
            return

        updater_member = await self._get_community_member(
            community, User(id=updater_id)
        )
        if not updater_member:
            raise AccessDeniedError("Updater is not a community member")

        updater_role = updater_member.role
        target_role = target_member.role

        # Check role hierarchy
        if target_role not in self.ROLE_HIERARCHY.get(updater_role, []):
            raise AccessDeniedError(
                f"Role '{updater_role}' cannot modify '{target_role}'"
            )

    async def get_inherited_relationships(
        self,
        community_id: int,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get inherited community relationships.

        This method retrieves relationships inherited through the community
        hierarchy, including relationship metadata and inheritance path.

        Args:
            community_id: Community's unique identifier
            include_inactive: Whether to include inactive relationships

        Returns:
            List of dictionaries containing relationship data

        Raises:
            ResourceNotFoundError: If community not found
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        inherited = []
        visited = set()

        async def traverse_relationships(current: Community, path: List[int]) -> None:
            if current.id in visited:
                return
            visited.add(current.id)

            for related in current.related_communities:
                if related.id == community_id:
                    continue

                if not include_inactive and not related.is_active:
                    continue

                inherited.append(
                    {
                        "community_id": related.id,
                        "name": related.name,
                        "inheritance_path": path.copy(),
                        "privacy_level": related.privacy_level.value,
                        "is_active": related.is_active,
                    }
                )

                await traverse_relationships(related, path + [related.id])

        await traverse_relationships(community, [community_id])
        return inherited

    async def validate_relationship_removal(
        self,
        community_id: int,
        related_id: int,
    ) -> None:
        """
        Validate if a relationship can be safely removed.

        This method checks for dependencies and constraints that might
        prevent relationship removal.

        Args:
            community_id: Primary community ID
            related_id: Related community ID

        Raises:
            BusinessRuleViolationError: If removal not allowed
            ValidationError: If validation fails
        """
        community = await self.get_community(community_id)
        related = await self.get_community(related_id)

        if not community or not related:
            raise ResourceNotFoundError("One or both communities not found")

        # Check for active shared resources
        if await self._has_active_shared_resources(community, related):
            raise BusinessRuleViolationError(
                "Cannot remove relationship with active shared resources"
            )

        # Check if removal would break inheritance chain
        dependent_communities = await self._get_dependent_communities(
            community, related
        )
        if dependent_communities:
            communities_str = ", ".join(str(c.id) for c in dependent_communities)
            raise BusinessRuleViolationError(
                f"Communities depend on this relationship: {communities_str}"
            )

    async def _get_dependent_communities(
        self,
        community: Community,
        related: Community,
    ) -> List[Community]:
        """
        Get communities that depend on a relationship.

        Args:
            community: Primary community
            related: Related community

        Returns:
            List of dependent communities
        """
        dependents = []
        visited = set()

        def traverse_dependents(current: Community) -> None:
            if current.id in visited:
                return
            visited.add(current.id)

            for related_community in current.related_communities:
                if related_community.id == related.id:
                    dependents.append(current)
                traverse_dependents(related_community)

        for member in community.members:
            for member_community in member.communities:
                traverse_dependents(member_community)

        return [d for d in dependents if d.id not in {community.id, related.id}]

    async def _has_active_shared_resources(
        self,
        community: Community,
        related: Community,
    ) -> bool:
        """
        Check for active shared resources between communities.

        Args:
            community: Primary community
            related: Related community

        Returns:
            bool: Whether active shared resources exist
        """
        # Check for shared contacts
        shared_contacts = set(community.contacts) & set(related.contacts)
        if any(contact.is_active for contact in shared_contacts):
            return True

        # Check for shared members
        shared_members = set(community.members) & set(related.members)
        if any(
            member.is_active
            for member in shared_members
            if await self._get_member_role(community, member) in {"admin", "moderator"}
        ):
            return True

        return False
