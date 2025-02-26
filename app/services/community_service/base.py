"""
Base module for community service operations.

This module defines the core CommunityService class, providing the fundamental 
CRUD operations and initialization logic for community management. It acts as 
the foundation for other community-related functionalities, ensuring modularity 
and separation of concerns.

Classes:
    - CommunityService: Handles the core CRUD operations for communities.

Dependencies:
    - SQLAlchemy ORM for database operations
    - BaseService for common service patterns
    - CommunityRepository for community-specific database access

Typical usage example:
    service = CommunityService(db)
    new_community = await service.create_community(data)
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.services.base_service import BaseService
from app.services.service_exceptions import ResourceNotFoundError, ValidationError
from app.services.service_interfaces import ICommunityService
from app.db.models.community_model import Community
from app.db.repositories.community_repository import CommunityRepository
from app.api.v1.schemas.community_schema import CommunityCreate, CommunityUpdate


class CommunityService(
    BaseService[Community, CommunityCreate, CommunityUpdate, CommunityRepository],
    ICommunityService,
):
    """
    Service class for managing community-related CRUD operations.

    This class extends BaseService to provide core functionality for handling
    communities, including creation, retrieval, updates, and deletion. It serves
    as the entry point for community-related business logic.

    Attributes:
        - repository: Instance of CommunityRepository

    Methods:
        - create_community: Create a new community.
        - get_community: Retrieve a community by ID.
        - update_community: Update a community's details.
        - delete_community: Delete a community.
    """

    def __init__(self, db: Session, repository: Optional[CommunityRepository] = None):
        """
        Initialize the community service with a database session.

        Args:
            db (Session): SQLAlchemy session instance for database operations.
            repository (Optional[CommunityRepository]): An optional repository instance for testing.
        """
        super().__init__(
            model=Community,
            repository=repository or CommunityRepository(db),  # Use mock or real repo
            logger_name="CommunityService",
        )

    async def create_community(self, data: CommunityCreate) -> Community:
        """
        Create a new community with validation.

        Args:
            data (CommunityCreate): Validated community creation data.

        Returns:
            Community: The created community instance.

        Raises:
            ValidationError: If validation fails.
            BusinessRuleViolationError: If creation violates business rules.
        """
        if not data.name.strip():  # Ensure non-empty name
            raise ValidationError("Community name cannot be empty.")

        return await self.create(data)

    async def get_community(self, community_id: int) -> Community:
        """
        Retrieve a community by its unique identifier.

        Raises:
            ResourceNotFoundError: If the community does not exist.
        """
        community = await self.get(community_id)
        if not community:
            raise ResourceNotFoundError(f"Community with ID {community_id} not found.")

        return community

    async def update_community(
        self, community_id: int, data: CommunityUpdate
    ) -> Community:
        """
        Update an existing community.

        Raises:
            ResourceNotFoundError: If the community does not exist.
        """
        updated_community = await self.update(
            id=community_id, data=data
        )  # Corrected call

        if updated_community is None:
            raise ResourceNotFoundError(f"Community with ID {community_id} not found.")

        return updated_community

    async def delete_community(self, community_id: int) -> None:
        """
        Delete a community by its ID.

        Raises:
            ResourceNotFoundError: If the community does not exist.
        """
        await self.get_community(community_id)  # Ensure community exists before delete
        await self.delete(community_id)
