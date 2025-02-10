"""
Membership management module for community service operations.

This module handles all membership-related operations for communities, including
invitations, approvals, rejections, and role management. It ensures proper
role assignments, enforces membership limits, and adheres to privacy rules.

Classes:
    - CommunityMembershipService: Manages membership operations for communities.

Dependencies:
    - SQLAlchemy ORM for database operations
    - CommunityService for core community operations
    - Constants module for predefined membership rules

Typical usage example:
    service = CommunityMembershipService(db)
    success = await service.manage_membership(community_id, user_id, "invite")
"""

from sqlalchemy.orm import Session
from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.user_model import User
from app.db.repositories.community_repository import CommunityRepository
from app.services.community_service.constants import (
    MemberRole,
    MAX_MEMBERS_FREE,
    MAX_MEMBERS_PREMIUM,
)
from app.services.service_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    QuotaExceededError,
)


class CommunityMembershipService:
    """
    Service class for managing community membership operations.

    This service handles all membership-related actions, such as inviting users,
    approving requests, rejecting requests, and managing roles within a community.

    Attributes:
        - repository (CommunityRepository): Data access layer for communities.
    """

    def __init__(self, db: Session):
        """
        Initialize the community membership service with a database session.

        Args:
            db (Session): SQLAlchemy session instance for database operations.
        """
        self.db = db
        self.repository = CommunityRepository(db)

    async def manage_membership(
        self,
        community_id: int,
        user_id: int,
        action: str,
        role: str = MemberRole.MEMBER.value,
    ) -> bool:
        """
        Manage membership operations such as inviting, approving, rejecting, or leaving a community.

        Args:
            community_id (int): The ID of the community.
            user_id (int): The ID of the user.
            action (str): The action to perform ("invite", "approve", "reject", "leave").
            role (str, optional): The role to assign upon approval. Defaults to "member".

        Returns:
            bool: True if the operation was successful, False otherwise.

        Raises:
            ValidationError: If the action is invalid.
            BusinessRuleViolationError: If membership rules are violated.
            QuotaExceededError: If the member limit is reached.
            AccessDeniedError: If the operation is not permitted.
        """
        community = await self.repository.get(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        user = await self.db.get(User, user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        if action not in {"invite", "approve", "reject", "leave"}:
            raise ValidationError(f"Invalid membership action: {action}")

        if role not in {r.value for r in MemberRole}:
            raise ValidationError(f"Invalid role: {role}")

        if action in {"invite", "approve"}:
            await self._check_member_limits(community)

        if community.privacy_level == PrivacyLevel.INVITATION_ONLY:
            return await self._handle_invitation_only_membership(
                community, user, action, role
            )
        elif community.privacy_level == PrivacyLevel.PRIVATE:
            return await self._handle_private_membership(community, user, action, role)
        else:  # PUBLIC
            return await self._handle_public_membership(community, user, action, role)

    async def _check_member_limits(self, community: Community) -> None:
        """
        Check if a community can accept new members based on its limits.

        Args:
            community (Community): The target community.

        Raises:
            QuotaExceededError: If the member limit has been reached.
        """
        member_limit = MAX_MEMBERS_PREMIUM if community.is_premium else MAX_MEMBERS_FREE
        if community.total_count >= member_limit:
            raise QuotaExceededError(
                f"Community has reached the member limit of {member_limit}"
            )
