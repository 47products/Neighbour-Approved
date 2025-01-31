"""
Community service implementation module.

This module implements the complete community management service layer, handling all
community-related business logic including membership management, privacy controls,
and relationship management. It ensures proper separation of concerns by encapsulating
business rules and validation logic separate from data access.

The module provides comprehensive handling of:
- Community membership with role hierarchies
- Privacy level management and inheritance
- Inter-community relationships
- Resource quotas and limits
"""

from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional, Dict, Any, Set, Tuple, cast
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.services.service_interfaces import ICommunityService
from app.services.service_exceptions import (
    ValidationError,
    BusinessRuleViolationError,
    ResourceNotFoundError,
    AccessDeniedError,
    StateError,
    QuotaExceededError,
    RoleAssignmentError,
)
from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.user_model import User
from app.db.models.community_member_model import CommunityMember
from app.db.repositories.community_repository import CommunityRepository
from app.api.v1.schemas.community_schema import CommunityCreate, CommunityUpdate


class MemberRole(str, Enum):
    """Enumeration of possible community member roles."""

    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
    PENDING = "pending"


class CommunityService(
    BaseService[Community, CommunityCreate, CommunityUpdate], ICommunityService
):
    """
    Service for managing community-related operations and business logic.

    This service implements comprehensive community management operations including
    membership control, privacy management, and relationship handling. It encapsulates
    all community-related business rules and validation logic.

    Attributes:
        MAX_MEMBERS_FREE: Maximum members for free communities
        MAX_MEMBERS_PREMIUM: Maximum members for premium communities
        MAX_RELATIONSHIPS: Maximum number of related communities
        MAX_PENDING_INVITES: Maximum pending invitations
        RESTRICTED_NAMES: Names not allowed for communities
        ROLE_HIERARCHY: Role hierarchy definitions
        PRIVACY_TRANSITION_RULES: Allowed privacy level transitions
    """

    MAX_MEMBERS_FREE = 50
    MAX_MEMBERS_PREMIUM = 500
    MAX_RELATIONSHIPS = 10
    MAX_PENDING_INVITES = 100
    RESTRICTED_NAMES = {"admin", "system", "support", "test"}
    ROLE_HIERARCHY = {
        MemberRole.OWNER: {MemberRole.ADMIN, MemberRole.MODERATOR, MemberRole.MEMBER},
        MemberRole.ADMIN: {MemberRole.MODERATOR, MemberRole.MEMBER},
        MemberRole.MODERATOR: {MemberRole.MEMBER},
        MemberRole.MEMBER: set(),
    }
    PRIVACY_TRANSITION_RULES = {
        PrivacyLevel.PUBLIC: {PrivacyLevel.PRIVATE, PrivacyLevel.INVITATION_ONLY},
        PrivacyLevel.PRIVATE: {PrivacyLevel.PUBLIC, PrivacyLevel.INVITATION_ONLY},
        PrivacyLevel.INVITATION_ONLY: {PrivacyLevel.PRIVATE},
    }

    def __init__(self, db: Session):
        """Initialize the community service.

        Args:
            db: Database session for repository operations
        """
        super().__init__(
            model=Community,
            repository=CommunityRepository(db),
            logger_name="CommunityService",
        )

    async def create_community(self, data: CommunityCreate) -> Community:
        """Create a new community with validation.

        This method implements comprehensive validation including name restrictions,
        privacy level validation, and quota checks before creating a new community.

        Args:
            data: Validated community creation data

        Returns:
            Created community instance

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If creation violates business rules
            DuplicateResourceError: If community name already exists
        """
        try:
            # Validate community creation
            await self._validate_community_creation(data)

            # Create community
            community = await self.create(data)

            # Initialize owner membership
            owner_member = CommunityMember(
                community_id=community.id,
                user_id=data.owner_id,
                role=MemberRole.OWNER.value,
                is_active=True,
                role_assigned_at=datetime.now(UTC),
            )
            self.db.add(owner_member)
            await self.db.commit()

            self._logger.info(
                "community_created",
                community_id=community.id,
                owner_id=data.owner_id,
                name=data.name,
            )

            return community

        except Exception as e:
            self._logger.error(
                "community_creation_failed",
                error=str(e),
                owner_id=data.owner_id,
                name=data.name,
            )
            raise

    async def _validate_community_creation(self, data: CommunityCreate) -> None:
        """Validate community creation against business rules.

        Args:
            data: Community creation data

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If creation violates business rules
        """
        # Check restricted names
        if any(word in data.name.lower() for word in self.RESTRICTED_NAMES):
            raise ValidationError("Community name contains restricted words")

        # Check owner exists
        owner = await self.db.get(User, data.owner_id)
        if not owner or not owner.is_active:
            raise ValidationError(f"Owner {data.owner_id} not found or inactive")

        # Check owner's community quota
        owned_communities = await self._get_user_owned_communities(data.owner_id)
        if len(owned_communities) >= await self._get_user_community_limit(
            data.owner_id
        ):
            raise BusinessRuleViolationError(
                "User has reached maximum owned communities"
            )

        # Validate privacy level
        if data.privacy_level == PrivacyLevel.PRIVATE:
            if not await self._can_create_private_community(owner):
                raise BusinessRuleViolationError(
                    "Private communities require premium membership"
                )

    async def _can_create_private_community(self, user: User) -> bool:
        """Check if user can create private communities.

        Args:
            user: User to check

        Returns:
            Whether user can create private communities
        """
        return any(role.name == "premium_user" for role in user.roles if role.is_active)

    async def manage_membership(
        self,
        community_id: int,
        user_id: int,
        action: str,
        *,
        inviter_id: Optional[int] = None,
        role: str = MemberRole.MEMBER.value,
    ) -> bool:
        """Manage community membership operations.

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

            # Check role validity
            if role not in {r.value for r in MemberRole}:
                raise ValidationError(f"Invalid role: {role}")

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
        """Check if community can accept new members.

        Args:
            community: Community to check

        Raises:
            QuotaExceededError: If member limit reached
        """
        member_limit = await self._get_community_member_limit(community)
        if community.total_count >= member_limit:
            raise QuotaExceededError(
                f"Community has reached member limit of {member_limit}"
            )

    async def _handle_invitation_only_membership(
        self,
        community: Community,
        user: User,
        action: str,
        inviter_id: Optional[int],
        role: str,
    ) -> bool:
        """Handle membership for invitation-only communities.

        Args:
            community: Target community
            user: User to manage
            action: Membership action
            inviter_id: ID of inviting user
            role: Role to assign

        Returns:
            bool: True if operation was successful

        Raises:
            ValidationError: If operation is invalid
            BusinessRuleViolationError: If operation violates rules
        """
        action_handlers = {
            "invite": self._handle_invitation,
            "approve": self._handle_approval,
            "reject": self._handle_rejection,
            "leave": self._handle_member_leave,
        }

        handler = action_handlers.get(action)
        if not handler:
            return False

        return await handler(community, user, inviter_id, role)

    async def _handle_invitation(
        self,
        community: Community,
        user: User,
        inviter_id: Optional[int],
        role: str,
    ) -> bool:
        """Process a new member invitation.

        Args:
            community: Target community
            user: User to invite
            inviter_id: ID of inviting user
            role: Role to assign

        Returns:
            bool: True if invitation was successful

        Raises:
            ValidationError: If inviter information is invalid
            AccessDeniedError: If inviter lacks permission
            QuotaExceededError: If invitation quota exceeded
        """
        await self._validate_invitation_request(community, inviter_id)
        await self._check_invitation_quota(community)

        # Create and store the pending membership
        member = await self._create_pending_membership(
            community, user, cast(int, inviter_id), role
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

    async def _validate_invitation_request(
        self,
        community: Community,
        inviter_id: Optional[int],
    ) -> None:
        """Validate invitation request and permissions.

        Args:
            community: Target community
            inviter_id: ID of inviting user

        Raises:
            ValidationError: If inviter ID is missing
            ResourceNotFoundError: If inviter not found
            AccessDeniedError: If inviter lacks permission
        """
        if not inviter_id:
            raise ValidationError("Inviter ID required for invitations")

        inviter = await self.db.get(User, inviter_id)
        if not inviter:
            raise ResourceNotFoundError(f"Inviter {inviter_id} not found")

        inviter_member = await self._get_community_member(community, inviter)
        if not inviter_member or inviter_member.role not in {
            MemberRole.OWNER.value,
            MemberRole.ADMIN.value,
        }:
            raise AccessDeniedError("Insufficient permission to invite members")

    async def _check_invitation_quota(self, community: Community) -> None:
        """Check if community has reached invitation quota.

        Args:
            community: Target community

        Raises:
            QuotaExceededError: If quota exceeded
        """
        pending_count = await self._get_pending_invitations_count(community)
        if pending_count >= self.MAX_PENDING_INVITES:
            raise QuotaExceededError("Maximum pending invitations reached")

    async def _create_pending_membership(
        self,
        community: Community,
        user: User,
        inviter_id: int,
        role: str,
    ) -> CommunityMember:
        """Create a pending membership record.

        Args:
            community: Target community
            user: User to invite
            inviter_id: ID of inviting user
            role: Role to assign

        Returns:
            CommunityMember: Created membership record
        """
        member = CommunityMember(
            community_id=community.id,
            user_id=user.id,
            role=role,
            is_active=False,
            role_assigned_by=inviter_id,
        )
        self.db.add(member)
        return member

    async def _handle_approval(
        self,
        community: Community,
        user: User,
        inviter_id: Optional[int],
        role: str,
    ) -> bool:
        """Handle invitation approval.

        Args:
            community: Target community
            user: User to approve
            inviter_id: Not used for approval
            role: Not used for approval

        Returns:
            bool: True if approval was successful
        """
        member = await self._get_pending_membership(community, user)

        member.is_active = True
        member.role_assigned_at = datetime.now(UTC)
        community.total_count += 1
        community.active_count += 1

        await self.db.commit()
        self._log_invitation_action(community, user, "approved")
        return True

    async def _handle_rejection(
        self,
        community: Community,
        user: User,
        inviter_id: Optional[int],
        role: str,
    ) -> bool:
        """Handle invitation rejection.

        Args:
            community: Target community
            user: User to reject
            inviter_id: Not used for rejection
            role: Not used for rejection

        Returns:
            bool: True if rejection was successful
        """
        member = await self._get_pending_membership(community, user)
        self.db.delete(member)
        await self.db.commit()

        self._log_invitation_action(community, user, "rejected")
        return True

    async def _get_pending_membership(
        self,
        community: Community,
        user: User,
    ) -> CommunityMember:
        """Get pending membership record.

        Args:
            community: Target community
            user: User to check

        Returns:
            CommunityMember: Pending membership record

        Raises:
            BusinessRuleViolationError: If no pending invitation exists
        """
        member = await self._get_community_member(community, user)
        if not member or member.is_active:
            raise BusinessRuleViolationError("No pending invitation found")
        return member

    def _log_invitation_action(
        self,
        community: Community,
        user: User,
        action: str,
    ) -> None:
        """Log invitation-related action.

        Args:
            community: Target community
            user: Affected user
            action: Action performed
        """
        self._logger.info(
            f"invitation_{action}",
            community_id=community.id,
            user_id=user.id,
        )

    async def _handle_private_membership(
        self,
        community: Community,
        user: User,
        action: str,
        role: str,
    ) -> bool:
        """Handle membership for private communities.

        Args:
            community: Target community
            user: User to manage
            action: Membership action
            role: Role to assign

        Returns:
            bool: True if operation was successful

        Raises:
            BusinessRuleViolationError: If operation violates rules
        """
        if action == "leave":
            return await self._handle_member_leave(community, user)

        if action == "approve":
            # Verify premium requirement
            if not any(
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

    async def _handle_public_membership(
        self,
        community: Community,
        user: User,
        action: str,
        role: str,
    ) -> bool:
        """Handle membership for public communities.

        Args:
            community: Target community
            user: User to manage
            action: Membership action
            role: Role to assign

        Returns:
            bool: True if operation was successful

        Raises:
            BusinessRuleViolationError: If operation violates rules
        """
        if action == "leave":
            return await self._handle_member_leave(community, user)

        if action == "approve":
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

    async def _handle_member_leave(self, community: Community, user: User) -> bool:
        """Handle member leaving a community.

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

        if member.role == MemberRole.OWNER.value:
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
        """Get effective member limit for community.

        Args:
            community: Community to check

        Returns:
            int: Maximum allowed members
        """
        owner = await self.db.get(User, community.owner_id)
        if owner and any(
            role.name == "premium_user" for role in owner.roles if role.is_active
        ):
            return self.MAX_MEMBERS_PREMIUM
        return self.MAX_MEMBERS_FREE

    async def manage_community_relationships(
        self,
        community_id: int,
        related_community_id: int,
        action: str,
    ) -> bool:
        """Manage relationships between communities.

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
        """Add a bidirectional relationship between communities.

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
        """Validate rules for community relationships.

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
        inherited = await self.get_inherited_relationships(community.id)
        if any(r["community_id"] == related_community.id for r in inherited):
            raise BusinessRuleViolationError(
                "Cannot create explicit relationship with inherited community"
            )

    async def _would_create_circular_relationship(
        self,
        community: Community,
        related_community: Community,
    ) -> bool:
        """Check if adding a relationship would create a circular reference.

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

        # Add temporary relationship for checking
        community.related_communities.append(related_community)
        has_circular = check_circular(community)
        community.related_communities.remove(related_community)

        return has_circular

    async def _remove_community_relationship(
        self,
        community: Community,
        related_community: Community,
    ) -> None:
        """Remove a bidirectional relationship between communities.

        Args:
            community: Primary community
            related_community: Community to remove relationship with

        Raises:
            BusinessRuleViolationError: If relationship cannot be removed
        """
        if related_community not in community.related_communities:
            return

        # Validate removal
        await self._validate_relationship_removal(community, related_community)

        # Remove bidirectional relationship
        community.related_communities.remove(related_community)
        related_community.related_communities.remove(community)

        self._logger.info(
            "relationship_removed",
            community_id=community.id,
            related_community_id=related_community.id,
        )

    async def _validate_relationship_removal(
        self,
        community: Community,
        related_community: Community,
    ) -> None:
        """Validate if a relationship can be safely removed.

        Args:
            community: Primary community
            related_community: Community to remove relationship with

        Raises:
            BusinessRuleViolationError: If removal would break dependencies
        """
        # Check for active shared resources
        if await self._has_active_shared_resources(community, related_community):
            raise BusinessRuleViolationError(
                "Cannot remove relationship with active shared resources"
            )

        # Check if removal would break inheritance chain
        dependent_communities = await self._get_dependent_communities(
            community, related_community
        )
        if dependent_communities:
            communities_str = ", ".join(str(c.id) for c in dependent_communities)
            raise BusinessRuleViolationError(
                f"Communities depend on this relationship: {communities_str}"
            )

    async def _has_active_shared_resources(
        self,
        community: Community,
        related_community: Community,
    ) -> bool:
        """Check for active shared resources between communities.

        Args:
            community: Primary community
            related_community: Related community

        Returns:
            bool: Whether active shared resources exist
        """
        # Check for shared contacts
        shared_contacts = set(community.contacts) & set(related_community.contacts)
        if any(contact.is_active for contact in shared_contacts):
            return True

        # Check for shared members
        shared_members = set(community.members) & set(related_community.members)
        if any(
            await self._get_member_role(community, member)
            in {
                MemberRole.ADMIN.value,
                MemberRole.MODERATOR.value,
            }
            for member in shared_members
        ):
            return True

        return False

    async def _get_dependent_communities(
        self,
        community: Community,
        related_community: Community,
    ) -> List[Community]:
        """Get communities that depend on relationship.

        Args:
            community: Primary community
            related_community: Related community

        Returns:
            List[Community]: List of dependent communities
        """
        dependents = []
        visited = set()

        def traverse_dependents(current: Community) -> None:
            if current.id in visited:
                return
            visited.add(current.id)

            for rel_community in current.related_communities:
                if rel_community.id == related_community.id:
                    dependents.append(current)
                traverse_dependents(rel_community)

        for member in community.members:
            for member_community in member.communities:
                traverse_dependents(member_community)

        return [
            d for d in dependents if d.id not in {community.id, related_community.id}
        ]

    async def manage_privacy_level(
        self,
        community_id: int,
        new_level: PrivacyLevel,
        updated_by: int,
    ) -> Community:
        """Change community privacy level.

        Args:
            community_id: Community's unique identifier
            new_level: New privacy level to set
            updated_by: User ID making the change

        Returns:
            Updated community instance

        Raises:
            ValidationError: If privacy level transition is invalid
            AccessDeniedError: If user cannot change privacy level
            BusinessRuleViolationError: If change violates business rules
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        # Validate update permission
        updater = await self.db.get(User, updated_by)
        if not updater:
            raise ResourceNotFoundError(f"User {updated_by} not found")

        member = await self._get_community_member(community, updater)
        if not member or member.role not in {
            MemberRole.OWNER.value,
            MemberRole.ADMIN.value,
        }:
            raise AccessDeniedError("Insufficient permission to change privacy level")

        # Validate privacy level transition
        current_level = community.privacy_level
        if new_level not in self.PRIVACY_TRANSITION_RULES.get(current_level, set()):
            raise ValidationError(
                f"Invalid privacy level transition: {current_level} -> {new_level}"
            )

        try:
            # Validate new level requirements
            if new_level == PrivacyLevel.PRIVATE:
                if not await self._can_be_private_community(community):
                    raise BusinessRuleViolationError(
                        "Private communities require premium ownership"
                    )

            # Update privacy level
            community.privacy_level = new_level
            await self.db.commit()

            self._logger.info(
                "privacy_level_updated",
                community_id=community_id,
                old_level=current_level,
                new_level=new_level,
                updated_by=updated_by,
            )

            return community

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "privacy_level_update_failed",
                community_id=community_id,
                error=str(e),
            )
            raise

    async def _can_be_private_community(self, community: Community) -> bool:
        """Check if community can be private.

        Args:
            community: Community to check

        Returns:
            bool: Whether community can be private
        """
        owner = await self.db.get(User, community.owner_id)
        return owner and any(
            role.name == "premium_user" for role in owner.roles if role.is_active
        )

    async def manage_member_roles(
        self,
        community_id: int,
        user_id: int,
        role: str,
        assigned_by: Optional[int] = None,
    ) -> bool:
        """Manage member roles within a community.

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
            # Validate role
            if role not in {r.value for r in MemberRole}:
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
                member = CommunityMember(
                    community_id=community.id,
                    user_id=user.id,
                    role=role,
                    role_assigned_at=datetime.now(UTC),
                    role_assigned_by=assigned_by,
                    is_active=True,
                )
                self.db.add(member)
                community.total_count += 1
                community.active_count += 1
            else:
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

    async def bulk_update_member_roles(
        self,
        community_id: int,
        role_updates: List[Tuple[int, str]],
        updated_by: int,
    ) -> bool:
        """Bulk update member roles within a community.

        Args:
            community_id: Community's unique identifier
            role_updates: List of (user_id, new_role) tuples
            updated_by: ID of user making the updates

        Returns:
            bool: True if all updates were successful

        Raises:
            ResourceNotFoundError: If community not found
            ValidationError: If any role is invalid
            AccessDeniedError: If user cannot update roles
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        try:
            for user_id, new_role in role_updates:
                await self.manage_member_roles(
                    community_id=community_id,
                    user_id=user_id,
                    role=new_role,
                    assigned_by=updated_by,
                )
            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "bulk_role_update_failed",
                community_id=community_id,
                error=str(e),
            )
            raise

    async def _validate_role_assignment_permission(
        self,
        community: Community,
        assigner: User,
        role: str,
    ) -> None:
        """Validate if user has permission to assign a role.

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
        assignable_roles = self.ROLE_HIERARCHY[MemberRole(assigner_role)]
        if MemberRole(role) not in assignable_roles:
            raise AccessDeniedError(f"Role '{assigner_role}' cannot assign '{role}'")

    async def get_member_roles(
        self,
        community_id: int,
        *,
        role_filter: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Tuple[int, str]]:
        """Get community members and their roles.

        Args:
            community_id: Community's unique identifier
            role_filter: Optional role to filter by
            active_only: Whether to include only active members

        Returns:
            List[Tuple[int, str]]: List of (user_id, role) tuples

        Raises:
            ResourceNotFoundError: If community not found
            ValidationError: If role filter is invalid
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        query = self.db.query(CommunityMember).filter(
            CommunityMember.community_id == community_id
        )

        if role_filter:
            if role_filter not in {r.value for r in MemberRole}:
                raise ValidationError(f"Invalid role filter: {role_filter}")
            query = query.filter(CommunityMember.role == role_filter)

        if active_only:
            query = query.filter(CommunityMember.is_active.is_(True))

        members = await query.all()
        return [(member.user_id, member.role) for member in members]

    async def get_inherited_relationships(
        self,
        community_id: int,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get inherited community relationships.

        This method retrieves relationships inherited through the community
        hierarchy, including relationship metadata and inheritance path.

        Args:
            community_id: Community's unique identifier
            include_inactive: Whether to include inactive relationships

        Returns:
            List[Dict[str, Any]]: List of relationship data dictionaries

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

    async def get_member_activity(
        self,
        community_id: int,
        user_id: int,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get member's activity history in community.

        Args:
            community_id: Community's unique identifier
            user_id: Member's user ID
            start_date: Optional start date for activity range
            end_date: Optional end date for activity range

        Returns:
            Dict[str, Any]: Member activity statistics

        Raises:
            ResourceNotFoundError: If community or member not found
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        member = await self._get_community_member(community, User(id=user_id))
        if not member:
            raise ResourceNotFoundError(f"Member {user_id} not found")

        # Build date range filter
        date_filter = []
        if start_date:
            date_filter.append(CommunityMember.joined_at >= start_date)
        if end_date:
            date_filter.append(CommunityMember.joined_at <= end_date)

        activity = {
            "member_since": member.joined_at,
            "current_role": member.role,
            "role_history": await self._get_member_role_history(member),
            "is_active": member.is_active,
            "last_activity": await self._get_member_last_activity(member),
        }

        if member.role in {MemberRole.ADMIN.value, MemberRole.MODERATOR.value}:
            activity.update(await self._get_moderator_activity(member))

        return activity

    async def _get_member_role_history(
        self, member: CommunityMember
    ) -> List[Dict[str, Any]]:
        """Get member's role assignment history.

        Args:
            member: Community member

        Returns:
            List[Dict[str, Any]]: List of role changes with metadata
        """
        # This would typically query a role_history table
        # For now, we return just the current role info
        return [
            {
                "role": member.role,
                "assigned_at": member.role_assigned_at,
                "assigned_by": member.role_assigned_by,
            }
        ]

    async def _get_member_last_activity(
        self, member: CommunityMember
    ) -> Optional[datetime]:
        """Get member's last activity timestamp.

        Args:
            member: Community member

        Returns:
            Optional[datetime]: Last activity timestamp or None
        """
        # This would typically query activity logs
        # For now, return role assignment as last activity
        return member.role_assigned_at

    async def _get_moderator_activity(self, member: CommunityMember) -> Dict[str, Any]:
        """Get moderator-specific activity metrics.

        Args:
            member: Community member with moderator role

        Returns:
            Dict[str, Any]: Moderator activity statistics
        """
        # This would typically aggregate moderation actions
        return {
            "total_actions": 0,
            "recent_actions": [],
            "managed_members": 0,
        }

    async def update_member_status(
        self,
        community_id: int,
        user_id: int,
        is_active: bool,
        updated_by: Optional[int] = None,
    ) -> bool:
        """Update a member's active status.

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
                member.role == MemberRole.OWNER.value
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
        """Validate if user can update a member's status.

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

        updater_role = MemberRole(updater_member.role)
        target_role = MemberRole(target_member.role)

        # Check role hierarchy
        if target_role not in self.ROLE_HIERARCHY.get(updater_role, set()):
            raise AccessDeniedError(
                f"Role '{updater_role.value}' cannot modify '{target_role.value}'"
            )

    async def _get_community_member(
        self, community: Community, user: User
    ) -> Optional[CommunityMember]:
        """Get community member association.

        Args:
            community: Target community
            user: User to check

        Returns:
            Optional[CommunityMember]: Member association if found
        """
        return (
            await self.db.query(CommunityMember)
            .filter(
                CommunityMember.community_id == community.id,
                CommunityMember.user_id == user.id,
            )
            .first()
        )

    async def _get_pending_invitations_count(self, community: Community) -> int:
        """Get count of pending invitations.

        Args:
            community: Community to check

        Returns:
            int: Number of pending invitations
        """
        return (
            await self.db.query(CommunityMember)
            .filter(
                CommunityMember.community_id == community.id,
                CommunityMember.is_active.is_(False),
            )
            .count()
        )

    async def _get_user_owned_communities(self, user_id: int) -> List[Community]:
        """Get communities owned by user.

        Args:
            user_id: User's unique identifier

        Returns:
            List[Community]: List of owned communities
        """
        return (
            await self.db.query(Community)
            .filter(
                Community.owner_id == user_id,
                Community.is_active.is_(True),
            )
            .all()
        )

    async def _get_user_community_limit(self, user_id: int) -> int:
        """Get maximum number of communities user can own.

        Args:
            user_id: User's unique identifier

        Returns:
            int: Maximum allowed owned communities
        """
        user = await self.db.get(User, user_id)
        if user and any(
            role.name == "premium_user" for role in user.roles if role.is_active
        ):
            return 10  # Premium limit
        return 3  # Free tier limit
