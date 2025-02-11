"""
Community relationships management module.

This module handles the establishment and removal of relationships between communities,
including enforcing limits, managing linked communities, and ensuring valid transitions.

Classes:
    - CommunityRelationshipService: Manages inter-community relationships.

Dependencies:
    - SQLAlchemy ORM for database operations.
    - CommunityRepository for data access operations.
    - Constants module for predefined relationship limits.

Typical usage example:
    service = CommunityRelationshipService(db)
    success = await service.manage_relationship(community_id, related_community_id, "add")
"""

from sqlalchemy.orm import Session
from app.db.repositories.community_repository import CommunityRepository
from app.services.community_service.community_service_constants import MAX_RELATIONSHIPS
from app.services.service_exceptions import (
    ResourceNotFoundError,
    ValidationError,
    QuotaExceededError,
)


class CommunityRelationshipService:
    """
    Service class for managing relationships between communities.

    This service ensures that communities can establish or remove relationships
    while enforcing relationship limits and validation rules.

    Attributes:
        - repository (CommunityRepository): Data access layer for communities.
    """

    def __init__(self, db: Session):
        """
        Initialize the community relationship service with a database session.

        Args:
            db (Session): SQLAlchemy session instance for database operations.
        """
        self.db = db
        self.repository = CommunityRepository(db)

    async def manage_relationship(
        self, community_id: int, related_community_id: int, action: str
    ) -> bool:
        """
        Manage relationships between communities (add or remove).

        Args:
            community_id (int): ID of the primary community.
            related_community_id (int): ID of the related community.
            action (str): The action to perform ("add" or "remove").

        Returns:
            bool: True if the operation was successful, False otherwise.

        Raises:
            ResourceNotFoundError: If either community does not exist.
            ValidationError: If the action is invalid.
            QuotaExceededError: If the relationship limit is exceeded.
        """
        community = await self.repository.get(community_id)
        related_community = await self.repository.get(related_community_id)

        if not community or not related_community:
            raise ResourceNotFoundError("One or both communities not found.")

        if action not in {"add", "remove"}:
            raise ValidationError(f"Invalid relationship action: {action}")

        if action == "add":
            if len(community.related_communities) >= MAX_RELATIONSHIPS:
                raise QuotaExceededError(
                    "Maximum number of related communities reached."
                )
            community.related_communities.append(related_community)
        else:
            community.related_communities.remove(related_community)

        await self.db.commit()
        return True
