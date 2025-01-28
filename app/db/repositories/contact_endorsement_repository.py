"""
Contact Endorsement Repository Module.

This module implements the repository pattern for contact endorsement data access,
focusing purely on database operations. Business logic resides in the service layer.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.repositories.repository_implementation import BaseRepository
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.api.v1.schemas.contact_endorsement_schema import (
    ContactEndorsementCreate,
    ContactEndorsementUpdate,
)
from app.db.errors import QueryError, IntegrityError, ValidationError


class ContactEndorsementRepository(
    BaseRepository[
        ContactEndorsement, ContactEndorsementCreate, ContactEndorsementUpdate
    ]
):
    """
    Repository for contact endorsement data access operations.

    Attributes:
        _model: The ContactEndorsement model class
        _db: The database session
        _logger: Structured logger instance
    """

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Args:
            db: Database session for operations
        """
        super().__init__(ContactEndorsement, db)

    async def get_by_contact_and_user(
        self, contact_id: int, user_id: int
    ) -> Optional[ContactEndorsement]:
        """
        Retrieve an endorsement for a contact by a specific user.

        Args:
            contact_id: ID of the contact
            user_id: ID of the user

        Returns:
            Optional[ContactEndorsement]: The endorsement if found

        Raises:
            QueryError: If the database query fails
        """
        try:
            query = select(self._model).where(
                and_(
                    self._model.contact_id == contact_id,
                    self._model.user_id == user_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            self._logger.error(
                "get_by_contact_and_user_failed",
                contact_id=contact_id,
                user_id=user_id,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve endorsement by contact and user",
                details={
                    "contact_id": contact_id,
                    "user_id": user_id,
                    "error": str(e),
                },
            ) from e

    async def get_by_community(
        self, community_id: int, skip: int = 0, limit: int = 100
    ) -> List[ContactEndorsement]:
        """
        Retrieve all endorsements within a specific community.

        Args:
            community_id: Community ID
            skip: Number of records to skip
            limit: Maximum records to retrieve

        Returns:
            List[ContactEndorsement]: Endorsements in the community

        Raises:
            QueryError: If the database query fails
        """
        try:
            query = (
                select(self._model)
                .where(self._model.community_id == community_id)
                .offset(skip)
                .limit(limit)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(
                "get_by_community_failed",
                community_id=community_id,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve endorsements by community",
                details={"community_id": community_id, "error": str(e)},
            ) from e

    async def get_stats(self, contact_id: int) -> Dict[str, Any]:
        """
        Get aggregated statistics for a contact's endorsements.

        Args:
            contact_id: ID of the contact

        Returns:
            Dict[str, Any]: Aggregated statistics

        Raises:
            QueryError: If the query fails
        """
        try:
            query = select(
                func.count(self._model.id).label("total"),
                func.sum(case((self._model.is_verified.is_(True), 1), else_=0)).label(
                    "verified"
                ),
                func.avg(self._model.rating).label("average_rating"),
            ).where(self._model.contact_id == contact_id)

            result = await self.db.execute(query)
            stats = result.one()
            return {
                "total": stats.total or 0,
                "verified": stats.verified or 0,
                "average_rating": (
                    round(stats.average_rating, 2) if stats.average_rating else None
                ),
            }

        except SQLAlchemyError as e:
            self._logger.error(
                "get_stats_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve contact endorsement stats",
                details={"contact_id": contact_id, "error": str(e)},
            ) from e

    async def delete_by_contact_and_user(self, contact_id: int, user_id: int) -> bool:
        """
        Delete an endorsement for a contact by a specific user.

        Args:
            contact_id: Contact ID
            user_id: User ID

        Returns:
            bool: Whether the endorsement was deleted

        Raises:
            IntegrityError: If deletion fails
        """
        try:
            stmt = self._model.__table__.delete().where(
                and_(
                    self._model.contact_id == contact_id,
                    self._model.user_id == user_id,
                )
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount > 0

        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "delete_by_contact_and_user_failed",
                contact_id=contact_id,
                user_id=user_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to delete endorsement",
                details={"contact_id": contact_id, "user_id": user_id, "error": str(e)},
            ) from e
