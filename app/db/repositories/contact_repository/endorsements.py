"""
Contact Endorsements Module.

This module provides the `ContactEndorsementsMixin` class which encapsulates methods
to handle contact endorsement statistics and update endorsement metrics. It includes
functionality to fetch endorsement stats and update a contact's related fields.

Usage Example:
    from app.db.repositories.contact_repository.endorsements import ContactEndorsementsMixin

    class MyRepository(ContactEndorsementsMixin, BaseRepository):
        pass

Dependencies:
    - SQLAlchemy (for query execution and transactions)
    - app.db.models.contact_endorsement_model.ContactEndorsement (Contact endorsement model)
    - app.db.errors.QueryError, IntegrityError (Custom error classes)
"""

from typing import Dict, Any
from sqlalchemy import select, func, case, and_
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.contact_endorsement_model import ContactEndorsement
from app.db.errors import QueryError, IntegrityError


class ContactEndorsementsMixin:
    """
    Mixin class for managing contact endorsement statistics and metrics.

    Provides methods to retrieve endorsement statistics and update related metrics
    for a contact.
    """

    async def get_endorsement_stats(self, contact_id: int) -> Dict[str, Any]:
        """
        Retrieve endorsement statistics for a given contact.

        This method calculates the total endorsements, verified endorsements,
        average rating, and the distribution of ratings for the contact.

        Args:
            contact_id (int): The unique identifier of the contact.

        Returns:
            Dict[str, Any]: A dictionary containing endorsement statistics:
                - total_endorsements (int): Total number of endorsements.
                - verified_endorsements (int): Count of verified endorsements.
                - average_rating (Optional[float]): Average rating (rounded to 2 decimals).
                - rating_distribution (dict): Distribution of ratings.

        Raises:
            QueryError: If the query fails due to a database error.
        """
        try:
            # Query for basic endorsement statistics.
            stats_query = select(
                func.count(ContactEndorsement.id).label("total"),
                func.sum(
                    case((ContactEndorsement.is_verified.is_(True), 1), else_=0)
                ).label("verified"),
                func.avg(ContactEndorsement.rating).label("average_rating"),
            ).where(ContactEndorsement.contact_id == contact_id)

            result = await self.db.execute(stats_query)
            basic_stats = result.one()

            # Query for rating distribution.
            rating_query = (
                select(
                    ContactEndorsement.rating,
                    func.count(ContactEndorsement.id).label("count"),
                )
                .where(
                    and_(
                        ContactEndorsement.contact_id == contact_id,
                        ContactEndorsement.rating.is_not(None),
                    )
                )
                .group_by(ContactEndorsement.rating)
            )
            rating_result = await self.db.execute(rating_query)
            rating_distribution = {row.rating: row.count for row in rating_result}

            return {
                "total_endorsements": basic_stats.total or 0,
                "verified_endorsements": basic_stats.verified or 0,
                "average_rating": (
                    round(basic_stats.average_rating, 2)
                    if basic_stats.average_rating
                    else None
                ),
                "rating_distribution": rating_distribution,
            }
        except SQLAlchemyError as e:
            self._logger.error(
                "get_endorsement_stats_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve endorsement statistics",
                details={"contact_id": contact_id, "error": str(e)},
            ) from e

    async def update_endorsement_metrics(self, contact_id: int) -> None:
        """
        Update a contact's endorsement-related metrics.

        This method retrieves the latest endorsement statistics for a contact and
        updates the corresponding fields in the contact's record.

        Args:
            contact_id (int): The unique identifier of the contact.

        Raises:
            IntegrityError: If the update fails due to a database error.
        """
        try:
            stats = await self.get_endorsement_stats(contact_id)
            stmt = (
                self._model.__table__.update()
                .where(self._model.id == contact_id)
                .values(
                    endorsements_count=stats["total_endorsements"],
                    verified_endorsements_count=stats["verified_endorsements"],
                    average_rating=stats["average_rating"],
                )
            )
            await self.db.execute(stmt)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "update_endorsement_metrics_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to update endorsement metrics",
                details={"contact_id": contact_id, "error": str(e)},
            ) from e
