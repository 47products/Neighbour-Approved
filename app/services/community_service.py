"""
Community service implementation module.

This module implements the core business logic for community management, including
membership handling, privacy controls, and relationship management between communities.
It ensures proper separation of concerns by encapsulating business rules separate
from data access.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import structlog

from app.services.base import BaseService
from app.services.interfaces import ICommunityService
from app.services.exceptions import (
    ValidationError,
    AccessDeniedError,
    ResourceNotFoundError,
    BusinessRuleViolationError,
    QuotaExceededError,
)
from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.user_model import User
from app.db.models.contact_model import Contact
from app.db.repositories.community_repository import CommunityRepository
from app.api.v1.schemas.community_schema import CommunityCreate, CommunityUpdate


class CommunityService(
    BaseService[Community, CommunityCreate, CommunityUpdate], ICommunityService
):
    """
    Service for managing community-related operations and business logic.

    This service implements community management operations including membership
    control, privacy settings, and community relationships. It encapsulates all
    community-related business rules and validation logic.

    Attributes:
        MAX_MEMBERS_FREE: Maximum members for free communities
        MAX_RELATIONSHIPS: Maximum number of related communities
        RESTRICTED_NAMES: Names not allowed for communities
    """

    MAX_MEMBERS_FREE = 50
    MAX_RELATIONSHIPS = 10
    RESTRICTED_NAMES = {"admin", "system", "support", "test"}

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

        Args:
            data: Community creation data

        Returns:
            Created community instance

        Raises:
            ValidationError: If validation fails
            QuotaExceededError: If user has reached community limit
        """
        if data.name.lower() in self.RESTRICTED_NAMES:
            raise ValidationError(f"Name '{data.name}' is not allowed")

        # Check if owner has reached community limit
        owner_communities = await self._get_user_owned_communities(data.owner_id)
        if len(owner_communities) >= await self._get_user_community_limit(
            data.owner_id
        ):
            raise QuotaExceededError("User has reached maximum number of communities")

        return await self.create(data)

    async def validate_create(self, data: CommunityCreate) -> None:
        """Validate community creation data.

        Args:
            data: Creation data to validate

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If business rules are violated
        """
        if len(data.name) < 3:
            raise ValidationError("Community name must be at least 3 characters")

        if data.privacy_level not in {level.value for level in PrivacyLevel}:
            raise ValidationError(f"Invalid privacy level: {data.privacy_level}")

        await super().validate_create(data)

    async def update_community(
        self, community_id: int, data: CommunityUpdate
    ) -> Optional[Community]:
        """Update community information.

        Args:
            community_id: Community's unique identifier
            data: Update data

        Returns:
            Updated community instance

        Raises:
            ResourceNotFoundError: If community not found
            ValidationError: If validation fails
            BusinessRuleViolationError: If update violates business rules
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        if data.privacy_level and data.privacy_level != community.privacy_level:
            await self._validate_privacy_change(community, data.privacy_level)

        return await self.update(id=community_id, data=data)

    async def get_community(self, community_id: int) -> Optional[Community]:
        """Retrieve a community by its identifier.

        This method fetches a community and validates basic access permissions.

        Args:
            community_id: Community's unique identifier

        Returns:
            Optional[Community]: The community if found and accessible, None otherwise

        Raises:
            ResourceNotFoundError: If community is not found
            AccessDeniedError: If community access is restricted
        """
        community = await self.get(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        if not await self.can_access(community):
            raise AccessDeniedError("Access to this community is restricted")

        return community

    async def _validate_privacy_change(
        self, community: Community, new_level: PrivacyLevel
    ) -> None:
        """Validate privacy level change.

        Args:
            community: Community to update
            new_level: New privacy level

        Raises:
            BusinessRuleViolationError: If change violates rules
        """
        if (
            new_level == PrivacyLevel.PRIVATE
            and len(community.members) > self.MAX_MEMBERS_FREE
        ):
            raise BusinessRuleViolationError(
                "Cannot change to private with more than "
                f"{self.MAX_MEMBERS_FREE} members"
            )

        # Add additional privacy change validation rules here

    async def add_member(self, community_id: int, user_id: int) -> bool:
        """Add a user to the community.

        Args:
            community_id: Community's unique identifier
            user_id: User to add

        Returns:
            bool: True if user was added or is already a member,
                False if the operation failed

        Raises:
            ResourceNotFoundError: If community or user not found
            AccessDeniedError: If user cannot join
            QuotaExceededError: If community at capacity
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        user = await self.db.get(User, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        if user in community.members:
            return True

        try:
            if not await self._can_join_community(user, community):
                raise AccessDeniedError("User cannot join this community")

            if len(community.members) >= await self._get_community_member_limit(
                community
            ):
                raise QuotaExceededError(
                    "Community has reached maximum member capacity"
                )

            community.add_member(user)
            await self.db.commit()

            self._logger.info(
                "member_added",
                community_id=community_id,
                user_id=user_id,
                member_count=len(community.members),
            )
            return True
        except (AccessDeniedError, QuotaExceededError) as e:
            self._logger.warning(
                "member_add_failed",
                community_id=community_id,
                user_id=user_id,
                error=str(e),
            )
            return False

    async def remove_member(self, community_id: int, user_id: int) -> bool:
        """Remove a user from the community.

        Args:
            community_id: Community's unique identifier
            user_id: User to remove

        Returns:
            True if user was removed

        Raises:
            ResourceNotFoundError: If community or user not found
            BusinessRuleViolationError: If user cannot be removed
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        user = await self.db.get(User, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        if user.id == community.owner_id:
            raise BusinessRuleViolationError("Cannot remove community owner")

        if user not in community.members:
            return False

        community.remove_member(user)
        await self.db.commit()

        self._logger.info(
            "member_removed",
            community_id=community_id,
            user_id=user_id,
            member_count=len(community.members),
        )
        return True

    async def get_community_contacts(self, community_id: int) -> List[Contact]:
        """Get contacts associated with community.

        Args:
            community_id: Community's unique identifier

        Returns:
            List of community contacts

        Raises:
            ResourceNotFoundError: If community not found
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        return [contact for contact in community.contacts if contact.is_active]

    async def get_community_members(self, community_id: int) -> List[User]:
        """Get members of the community.

        Args:
            community_id: Community's unique identifier

        Returns:
            List of community members

        Raises:
            ResourceNotFoundError: If community not found
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        return [member for member in community.members if member.is_active]

    async def manage_membership(
        self, community_id: int, user_id: int, role: str, action: str
    ) -> bool:
        """Manage community membership with role assignment.

        This method provides comprehensive membership management including role
        assignment and status tracking. It handles all membership state transitions
        and ensures proper validation of operations.

        Args:
            community_id: Community's unique identifier
            user_id: User's unique identifier
            role: Role to assign to the member
            action: Membership action to perform ('add', 'update', 'remove')

        Returns:
            bool: True if operation was successful, False otherwise

        Raises:
            ResourceNotFoundError: If community or user not found
            AccessDeniedError: If operation is not permitted
            ValidationError: If role or action is invalid
            BusinessRuleViolationError: If operation violates membership rules
        """
        community = await self.get_community(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        user = await self.db.get(User, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        try:
            # Validate the action and role
            await self._validate_membership_operation(community, user, role, action)

            # Perform the membership operation
            if action == "add":
                return await self._add_member_with_role(community, user, role)
            elif action == "update":
                return await self._update_member_role(community, user, role)
            elif action == "remove":
                return await self._remove_member_with_cleanup(community, user)

            raise ValidationError(f"Invalid membership action: {action}")

        except Exception as e:
            self._logger.error(
                "membership_operation_failed",
                community_id=community_id,
                user_id=user_id,
                role=role,
                action=action,
                error=str(e),
            )
            await self.db.rollback()
            return False

    async def _assign_member_role(
        self, community: Community, user: User, role: str
    ) -> None:
        """Assign a role to a community member.

        This method handles the assignment of roles within a community context,
        including necessary permission checks and state updates.

        Args:
            community: Target community
            user: User to assign role to
            role: Role to assign

        Raises:
            ValidationError: If role assignment is invalid
            BusinessRuleViolationError: If assignment violates community rules
        """
        # Validate role assignment permissions
        if not await self._can_manage_roles(community, user):
            raise BusinessRuleViolationError("Insufficient permissions to manage roles")

        try:
            # Update user's community role
            community_member = await self._get_community_member(community, user)
            if not community_member:
                raise BusinessRuleViolationError("User is not a community member")

            community_member.role = role
            await self.db.commit()

            self._logger.info(
                "role_assigned",
                community_id=community.id,
                user_id=user.id,
                role=role,
            )
        except Exception as e:
            self._logger.error(
                "role_assignment_failed",
                community_id=community.id,
                user_id=user.id,
                role=role,
                error=str(e),
            )
            await self.db.rollback()
            raise

    async def _get_member_role(self, community: Community, user: User) -> Optional[str]:
        """Get a member's current role in the community.

        Args:
            community: Target community
            user: User to check

        Returns:
            Optional[str]: User's current role or None if not a member
        """
        community_member = await self._get_community_member(community, user)
        return community_member.role if community_member else None

    async def _validate_membership_operation(
        self, community: Community, user: User, role: str, action: str
    ) -> None:
        """Validate membership operation against business rules.

        Args:
            community: Target community
            user: User to perform operation on
            role: Role to assign
            action: Operation to perform

        Raises:
            ValidationError: If operation parameters are invalid
            BusinessRuleViolationError: If operation violates rules
        """
        valid_actions = {"add", "update", "remove"}
        if action not in valid_actions:
            raise ValidationError(f"Invalid action: {action}")

        if action in {"add", "update"}:
            await self._validate_role_assignment(community, user, role)

        if action == "add" and user in community.members:
            raise BusinessRuleViolationError("User is already a member")

        if action != "add" and user not in community.members:
            raise BusinessRuleViolationError("User is not a member")

    async def _validate_role_assignment(
        self, community: Community, user: User, role: str
    ) -> None:
        """Validate role assignment for community membership.

        Args:
            community: Target community
            user: User to assign role to
            role: Role to assign

        Raises:
            ValidationError: If role is invalid
            BusinessRuleViolationError: If assignment violates rules
        """
        valid_roles = {"admin", "moderator", "member"}
        if role not in valid_roles:
            raise ValidationError(f"Invalid role: {role}")

        # Check if user has necessary permissions for role
        if role == "admin" and not user.has_permission("community_admin"):
            raise BusinessRuleViolationError("User cannot be assigned admin role")

    async def _add_member_with_role(
        self, community: Community, user: User, role: str
    ) -> bool:
        """Add a new member with specified role.

        Args:
            community: Target community
            user: User to add
            role: Role to assign

        Returns:
            bool: True if member was added successfully
        """
        if len(community.members) >= await self._get_community_member_limit(community):
            raise QuotaExceededError("Community has reached maximum member capacity")

        community.add_member(user)
        await self._assign_member_role(community, user, role)
        await self.db.commit()

        self._logger.info(
            "member_added",
            community_id=community.id,
            user_id=user.id,
            role=role,
        )
        return True

    async def _update_member_role(
        self, community: Community, user: User, new_role: str
    ) -> bool:
        """Update an existing member's role.

        Args:
            community: Target community
            user: User to update
            new_role: New role to assign

        Returns:
            bool: True if role was updated successfully
        """
        current_role = await self._get_member_role(community, user)
        if current_role == new_role:
            return False

        await self._assign_member_role(community, user, new_role)
        await self.db.commit()

        self._logger.info(
            "member_role_updated",
            community_id=community.id,
            user_id=user.id,
            old_role=current_role,
            new_role=new_role,
        )
        return True

    async def _remove_member_with_cleanup(
        self, community: Community, user: User
    ) -> bool:
        """Remove a member and perform necessary cleanup.

        Args:
            community: Target community
            user: User to remove

        Returns:
            bool: True if member was removed successfully
        """
        if user.id == community.owner_id:
            raise BusinessRuleViolationError("Cannot remove community owner")

        # Perform pre-removal cleanup
        await self._cleanup_member_data(community, user)

        community.remove_member(user)
        await self.db.commit()

        self._logger.info(
            "member_removed",
            community_id=community.id,
            user_id=user.id,
        )
        return True

    async def _cleanup_member_data(self, community: Community, user: User) -> None:
        """Perform cleanup operations when removing a member.

        This method handles all necessary data cleanup tasks when a member
        is removed from a community, ensuring data consistency.

        Args:
            community: Target community
            user: User being removed
        """
        try:
            # Remove member's content
            await self._cleanup_member_content(community, user)

            # Remove member's roles
            await self._cleanup_member_roles(community, user)

            # Remove member's permissions
            await self._cleanup_member_permissions(community, user)

            self._logger.info(
                "member_cleanup_completed",
                community_id=community.id,
                user_id=user.id,
            )
        except Exception as e:
            self._logger.error(
                "member_cleanup_failed",
                community_id=community.id,
                user_id=user.id,
                error=str(e),
            )
            raise

    async def _cleanup_member_content(self, community: Community, user: User) -> None:
        """Clean up member's content in the community.

        Args:
            community: Target community
            user: User being removed
        """
        # Implement content cleanup logic
        pass

    async def _cleanup_member_roles(self, community: Community, user: User) -> None:
        """Clean up member's roles in the community.

        Args:
            community: Target community
            user: User being removed
        """
        # Implement role cleanup logic
        pass

    async def _cleanup_member_permissions(
        self, community: Community, user: User
    ) -> None:
        """Clean up member's permissions in the community.

        Args:
            community: Target community
            user: User being removed
        """
        # Implement permission cleanup logic
        pass

    async def _can_join_community(self, user: User, community: Community) -> bool:
        """Check if user can join community.

        Args:
            user: User attempting to join
            community: Target community

        Returns:
            Whether user can join
        """
        if not user.is_active or not community.is_active:
            return False

        if community.privacy_level == PrivacyLevel.PUBLIC:
            return True

        if community.privacy_level == PrivacyLevel.PRIVATE:
            # Check if user has been invited or meets other criteria
            return await self._has_community_invite(user.id, community.id)

        # Add additional join validation logic here
        return False

    async def _has_community_invite(self, user_id: int, community_id: int) -> bool:
        """Check if user has been invited to community.

        Args:
            user_id: User to check
            community_id: Community to check

        Returns:
            Whether user has active invite
        """
        # Implement invitation checking logic
        return False

    async def _get_community_member(self, community: Community, user: User) -> Any:
        """Get the community member association record.

        Args:
            community: Target community
            user: Target user

        Returns:
            Any: Community member record if found, None otherwise
        """
        return await self.db.query(community.members).filter_by(user_id=user.id).first()

    async def _can_manage_roles(self, community: Community, user: User) -> bool:
        """Check if user can manage roles in the community.

        Args:
            community: Target community
            user: User to check

        Returns:
            bool: Whether user can manage roles
        """
        if user.id == community.owner_id:
            return True

        member_role = await self._get_member_role(community, user)
        return member_role in {"admin", "moderator"}

    async def _get_community_member_limit(self, community: Community) -> int:
        """Get maximum allowed members for community.

        Args:
            community: Community to check

        Returns:
            Maximum member limit
        """
        if community.privacy_level == PrivacyLevel.PUBLIC:
            return int("inf")
        return self.MAX_MEMBERS_FREE

    async def _get_user_owned_communities(self, user_id: int) -> List[Community]:
        """Get communities owned by user.

        Args:
            user_id: User's unique identifier

        Returns:
            List of owned communities
        """
        user = await self.db.get(User, user_id)
        if not user:
            return []
        return user.owned_communities

    async def _get_user_community_limit(self, user_id: int) -> int:
        """Get maximum communities user can own.

        Args:
            user_id: User's unique identifier

        Returns:
            Maximum community limit
        """
        # Implement limit logic based on user role/subscription
        return 5  # Default limit

    async def can_access(self, community: Community) -> bool:
        """Check if community can be accessed in current context.

        Args:
            community: Community to check

        Returns:
            Whether community is accessible
        """
        if not community.is_active:
            return False

        if community.privacy_level == PrivacyLevel.PUBLIC:
            return True

        # Add additional access control logic
        return True

    async def process_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate filter criteria.

        Args:
            filters: Raw filter criteria

        Returns:
            Processed filter criteria
        """
        processed = filters.copy()

        # Always filter out inactive communities unless explicitly requested
        if "is_active" not in processed:
            processed["is_active"] = True

        # Process privacy level filter
        if "privacy_level" in processed and processed["privacy_level"] not in {
            level.value for level in PrivacyLevel
        }:
            raise ValidationError(
                f"Invalid privacy level: {processed['privacy_level']}"
            )

        return processed
