"""
Community validation module.

This module provides validation logic for community-related operations,
including name restrictions, membership limits, privacy checks, and role validations.

Classes:
    - CommunityValidationService: Handles all validation for community operations.

Dependencies:
    - SQLAlchemy ORM for database operations.
    - CommunityRepository for data access operations.
    - Constants module for predefined validation rules.

Typical usage example:
    service = CommunityValidationService(db)
    service.validate_community_creation(data)
"""

from sqlalchemy.orm import Session
from app.db.models.community_model import Community, PrivacyLevel
from app.db.models.user_model import User
from app.db.repositories.community_repository import CommunityRepository
from app.services.community_service.constants import (
    RESTRICTED_NAMES,
    MAX_MEMBERS_FREE,
    MAX_MEMBERS_PREMIUM,
    MAX_COMMUNITIES_FREE,
    MAX_COMMUNITIES_PREMIUM,
)
from app.services.service_exceptions import (
    ValidationError,
    BusinessRuleViolationError,
)


class CommunityValidationService:
    """
    Service class for validating community-related operations.

    This service ensures that communities adhere to business rules, including
    name restrictions, privacy validations, and membership constraints.

    Attributes:
        - repository (CommunityRepository): Data access layer for communities.
    """

    def __init__(self, db: Session):
        """
        Initialize the community validation service with a database session.

        Args:
            db (Session): SQLAlchemy session instance for database operations.
        """
        self.db = db
        self.repository = CommunityRepository(db)

    async def validate_community_creation(self, data: dict) -> None:
        """
        Validate the creation of a new community.

        Args:
            data (dict): Community creation data.

        Raises:
            ValidationError: If validation fails.
            BusinessRuleViolationError: If creation violates business rules.
        """
        if any(word in data["name"].lower() for word in RESTRICTED_NAMES):
            raise ValidationError("Community name contains restricted words.")

        owner = await self.db.get(User, data["owner_id"])
        if not owner or not owner.is_active:
            raise ValidationError(f"Owner {data['owner_id']} not found or inactive.")

        owned_communities = await self.repository.get_user_communities(data["owner_id"])
        max_limit = (
            MAX_COMMUNITIES_PREMIUM if owner.is_premium else MAX_COMMUNITIES_FREE
        )

        if len(owned_communities) >= max_limit:
            raise BusinessRuleViolationError(
                "User has reached maximum owned communities."
            )

    async def validate_privacy_change(
        self, community: Community, new_privacy: PrivacyLevel
    ) -> None:
        """
        Validate a privacy level change for a community.

        Args:
            community (Community): The community instance.
            new_privacy (PrivacyLevel): The new privacy level to apply.

        Raises:
            BusinessRuleViolationError: If the privacy level transition is not allowed.
        """
        if new_privacy not in community.allowed_privacy_transitions:
            raise BusinessRuleViolationError(
                f"Invalid privacy transition from {community.privacy_level} to {new_privacy}."
            )
