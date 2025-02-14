"""
Contact Endorsement Repository Deletion Module.

This module provides the ContactEndorsementDeletionMixin class which encapsulates
methods to delete endorsements from the database.

Usage Example:
    from app.db.repositories.contact_endorsement_repository.deletion import ContactEndorsementDeletionMixin

    class MyRepository(ContactEndorsementDeletionMixin, BaseRepository):
        pass

Dependencies:
    - SQLAlchemy (for executing deletion statements)
    - app.db.models.contact_endorsement_model.ContactEndorsement (Contact endorsement model)
    - app.db.errors.IntegrityError (Custom error for integrity issues)
"""

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from app.db.errors import IntegrityError


class ContactEndorsementDeletionMixin:
    """
    Mixin class for deleting contact endorsements.

    Provides a method to delete an endorsement for a contact by a specific user.
    """

    async def delete_by_contact_and_user(self, contact_id: int, user_id: int) -> bool:
        """
        Delete an endorsement for a contact by a specific user.

        Args:
            contact_id (int): Contact ID.
            user_id (int): User ID.

        Returns:
            bool: True if the endorsement was deleted, False otherwise.

        Raises:
            IntegrityError: If deletion fails due to a database error.
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
