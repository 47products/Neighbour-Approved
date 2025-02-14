"""
Community Repository Module.

This module composes the various mixins to implement the full repository for
community data access operations. Business logic resides in the service layer.

Usage Example:
    from app.db.repositories.community_repository import CommunityRepository

    repo = CommunityRepository(db_session)

Dependencies:
    - BaseRepository (base repository implementation)
    - Community model, CommunityCreate, CommunityUpdate (schema and model definitions)
    - Mixins: CommunityQueriesMixin, CommunityActionsMixin
"""

from sqlalchemy.orm import Session
from app.db.repositories.repository_implementation import BaseRepository
from app.db.models.community_model import Community
from app.api.v1.schemas.community_schema import CommunityCreate, CommunityUpdate
from .queries import CommunityQueriesMixin
from .actions import CommunityActionsMixin


class CommunityRepository(
    CommunityQueriesMixin,
    CommunityActionsMixin,
    BaseRepository[Community, CommunityCreate, CommunityUpdate],
):
    """
    Repository for community data access operations.
    Combines query and action functionalities.
    """

    def __init__(self, db: Session):
        """
        Initialize community repository.

        Args:
            db (Session): Database session for operations.
        """
        super().__init__(Community, db)
