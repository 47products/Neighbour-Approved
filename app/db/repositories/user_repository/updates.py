"""
User Updates Mixin Module.

This module provides the mixin class that implements update operations for user
data, including updating last login timestamps, user active status, and bulk status updates.
"""

from datetime import datetime
from typing import List
from sqlalchemy.exc import SQLAlchemyError

from app.db.errors import IntegrityError


class UserUpdatesMixin:
    """
    Mixin class providing user update operations.

    Expects the inheriting class to have:
        - _model: The User model.
        - db: The active SQLAlchemy database session.
        - _logger: Logger for error logging.
    """

    async def update_last_login(self, user_id: int, timestamp: datetime) -> None:
        """
        Update the last login timestamp for a user.

        Args:
            user_id (int): The unique identifier of the user.
            timestamp (datetime): The new last login timestamp.

        Raises:
            IntegrityError: If the update operation fails.
        """
        try:
            stmt = (
                self._model.__table__.update()
                .where(self._model.id == user_id)
                .values(last_login=timestamp)
            )
            await self.db.execute(stmt)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "update_last_login_failed", user_id=user_id, error=str(e)
            )
            raise IntegrityError(
                message="Failed to update last login",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def update_status(self, user_id: int, is_active: bool) -> None:
        """
        Update the active status of a user.

        Args:
            user_id (int): The unique identifier of the user.
            is_active (bool): The new active status.

        Raises:
            IntegrityError: If the update operation fails.
        """
        try:
            stmt = (
                self._model.__table__.update()
                .where(self._model.id == user_id)
                .values(is_active=is_active)
            )
            await self.db.execute(stmt)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error("update_status_failed", user_id=user_id, error=str(e))
            raise IntegrityError(
                message="Failed to update user status",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def bulk_update_status(self, user_ids: List[int], is_active: bool) -> int:
        """
        Bulk update the active status for multiple users.

        Args:
            user_ids (List[int]): A list of user IDs to update.
            is_active (bool): The new active status to set.

        Returns:
            int: The number of users that were updated.

        Raises:
            IntegrityError: If the bulk update operation fails.
        """
        try:
            stmt = (
                self._model.__table__.update()
                .where(self._model.id.in_(user_ids))
                .values(is_active=is_active)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "bulk_status_update_failed", user_ids=user_ids, error=str(e)
            )
            raise IntegrityError(
                message="Failed to update user statuses",
                details={"user_ids": user_ids, "error": str(e)},
            ) from e
