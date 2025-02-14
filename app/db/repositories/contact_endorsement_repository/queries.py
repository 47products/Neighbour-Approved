"""
Contact Endorsement Repository Queries Module.

This module provides the ContactEndorsementQueriesMixin class which encapsulates
query-related operations for contact endorsements. It includes methods to:
    - Retrieve an endorsement for a contact by a specific user.
    - Retrieve endorsements within a specific community.

Usage Example:
    from app.db.repositories.contact_endorsement_repository.queries import ContactEndorsementQueriesMixin

    class MyRepository(ContactEndorsementQueriesMixin, BaseRepository):
        pass

Dependencies:
    - SQLAlchemy (for query execution)
    - app.db.models.contact_endorsement_model.ContactEndorsement (Contact endorsement model)
    - app.db.errors.QueryError (Custom error for query failures)
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.contact_endorsement_model import ContactEndorsement
from app.db.errors import QueryError


class ContactEndorsementQueriesMixin:
    """
    Mixin class for contact endorsement query operations.

    Provides methods to fetch endorsement records using various criteria,
    including filtering by contact and user, and by community.
    """

    async def get_by_contact_and_user(
        self, contact_id: int, user_id: int
    ) -> Optional[ContactEndorsement]:
        """
        Retrieve an endorsement for a contact by a specific user.

        Args:
            contact_id (int): ID of the contact.
            user_id (int): ID of the user.

        Returns:
            Optional[ContactEndorsement]: The endorsement if found, otherwise None.

        Raises:
            QueryError: If the database query fails.
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
            community_id (int): Community ID.
            skip (int): Number of records to skip.
            limit (int): Maximum records to retrieve.

        Returns:
            List[ContactEndorsement]: List of endorsements in the community.

        Raises:
            QueryError: If the database query fails.
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
