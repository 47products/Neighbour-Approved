"""
Privacy management module for community service operations.

This module handles all privacy-related operations for communities, ensuring 
proper privacy level transitions, access controls, and enforcement of business rules.

Classes:
    - CommunityPrivacyService: Manages privacy operations for communities.

Dependencies:
    - SQLAlchemy ORM for database operations
    - CommunityService for core community operations
    - Constants module for predefined privacy rules

Typical usage example:
    service = CommunityPrivacyService(db)
    success = await service.change_privacy_level(community_id, PrivacyLevel.PRIVATE)
"""

from sqlalchemy.orm import Session
from app.db.models.community_model import Community, PrivacyLevel
from app.db.repositories.community_repository import CommunityRepository
from app.services.community_service.constants import (
    PRIVACY_TRANSITION_RULES,
)
from app.services.service_exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


class CommunityPrivacyService:
    """
    Service class for managing community privacy settings.

    This service ensures proper privacy level transitions and enforces
    business rules around privacy settings.

    Attributes:
        - repository (CommunityRepository): Data access layer for communities.
    """

    def __init__(self, db: Session):
        """
        Initialize the community privacy service with a database session.

        Args:
            db (Session): SQLAlchemy session instance for database operations.
        """
        self.db = db
        self.repository = CommunityRepository(db)

    async def change_privacy_level(
        self, community_id: int, new_level: PrivacyLevel
    ) -> Community:
        """
        Change the privacy level of a community with validation.

        Args:
            community_id (int): The ID of the community to modify.
            new_level (PrivacyLevel): The new privacy level to apply.

        Returns:
            Community: The updated community instance.

        Raises:
            ResourceNotFoundError: If the community does not exist.
            BusinessRuleViolationError: If the privacy level transition is invalid.
        """
        community = await self.repository.get(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        if new_level not in PRIVACY_TRANSITION_RULES.get(community.privacy_level, {}):
            raise BusinessRuleViolationError(
                f"Invalid privacy transition from {community.privacy_level} to {new_level}"
            )

        community.privacy_level = new_level
        await self.db.commit()
        return community
