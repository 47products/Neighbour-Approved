"""
Contact Endorsement Repository Statistics Module.

This module provides the ContactEndorsementStatsMixin class which encapsulates
methods to fetch aggregated statistics for contact endorsements.

Usage Example:
    from app.db.repositories.contact_endorsement_repository.stats import ContactEndorsementStatsMixin

    class MyRepository(ContactEndorsementStatsMixin, BaseRepository):
        pass

Dependencies:
    - SQLAlchemy (for query execution)
    - app.db.models.contact_endorsement_model.ContactEndorsement (Contact endorsement model)
    - app.db.errors.QueryError (Custom error for query failures)
"""

from typing import Dict, Any
from sqlalchemy import select, func, case
from sqlalchemy.exc import SQLAlchemyError

from app.db.errors import QueryError


class ContactEndorsementStatsMixin:
    """
    Mixin class for retrieving aggregated statistics for contact endorsements.

    Provides a method to compute total endorsements, verified endorsements,
    and average rating for a given contact.
    """

    async def get_stats(self, contact_id: int) -> Dict[str, Any]:
        """
        Get aggregated statistics for a contact's endorsements.

        Args:
            contact_id (int): ID of the contact.

        Returns:
            Dict[str, Any]: Aggregated statistics including total endorsements,
            verified endorsements, and average rating.

        Raises:
            QueryError: If the query fails.
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
