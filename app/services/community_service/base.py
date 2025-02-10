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

from sqlalchemy.orm import Session
from app.services.base import BaseService
from app.services.service_interfaces import ICommunityService
from app.db.models.community_model import Community
from app.db.repositories.community_repository import CommunityRepository
from app.api.v1.schemas.community_schema import CommunityCreate, CommunityUpdate


class CommunityService(
    BaseService[Community, CommunityCreate, CommunityUpdate], ICommunityService
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

    def __init__(self, db: Session):
        """
        Initialize the community service with a database session.

        Args:
            db (Session): SQLAlchemy session instance for database operations.
        """
        super().__init__(
            model=Community,
            repository=CommunityRepository(db),
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
        return await self.create(data)

    async def get_community(self, community_id: int) -> Community:
        """
        Retrieve a community by its unique identifier.

        Args:
            community_id (int): The ID of the community to retrieve.

        Returns:
            Community: The retrieved community instance.

        Raises:
            ResourceNotFoundError: If the community does not exist.
        """
        return await self.get(community_id)

    async def update_community(
        self, community_id: int, data: CommunityUpdate
    ) -> Community:
        """
        Update an existing community.

        Args:
            community_id (int): The ID of the community to update.
            data (CommunityUpdate): Validated update data.

        Returns:
            Community: The updated community instance.

        Raises:
            ResourceNotFoundError: If the community does not exist.
            ValidationError: If update data is invalid.
        """
        return await self.update(community_id, data)

    async def delete_community(self, community_id: int) -> None:
        """
        Delete a community by its ID.

        Args:
            community_id (int): The ID of the community to delete.

        Raises:
            ResourceNotFoundError: If the community does not exist.
        """
        await self.delete(community_id)
