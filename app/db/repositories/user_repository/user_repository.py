"""
User Repository Module

This module composes the UserRepository class by integrating multiple mixins
that separate the concerns of retrieval, update, and role assignment operations.
It provides a clean and maintainable interface for all user-related data access.
"""

from sqlalchemy.orm import Session

from app.db.repositories.repository_implementation import BaseRepository
from app.db.models.user_model import User
from app.api.v1.schemas.user_schema import UserCreate, UserUpdate

from .retrieval import UserRetrievalMixin
from .updates import UserUpdatesMixin
from .assignment import UserAssignmentMixin


class UserRepository(
    BaseRepository[User, UserCreate, UserUpdate],
    UserRetrievalMixin,
    UserUpdatesMixin,
    UserAssignmentMixin,
):
    """
    Repository for managing user data in the database.

    This class integrates multiple mixins:
      - UserRetrievalMixin: Provides methods to retrieve users.
      - UserUpdatesMixin: Provides methods to update user records.
      - UserAssignmentMixin: Provides methods for assigning roles to users.

    It extends BaseRepository, ensuring a clean separation between data access
    and business logic.
    """

    def __init__(self, db: Session) -> None:
        """
        Initialize the UserRepository with a database session.

        Args:
            db (Session): The active SQLAlchemy database session.
        """
        super().__init__(User, db)
