"""
User Assignment Mixin Module.

This module provides a mixin class that implements user role assignment operations,
allowing roles to be assigned to users.
"""

from sqlalchemy.exc import SQLAlchemyError
from app.db.models.role_model import Role


class UserAssignmentMixin:
    """
    Mixin class providing user role assignment operations.

    Expects the inheriting class to have:
        - _model: The User model.
        - db: The active SQLAlchemy database session.
        - _logger: Logger for error logging.
        - get: Method to retrieve a user by ID.
    """

    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id (int): The unique identifier of the user.
            role_id (int): The unique identifier of the role.

        Returns:
            bool: True if the role was successfully assigned, False otherwise.
        """
        try:
            user = await self.get(user_id)
            if not user:
                return False

            role = await self.db.get(Role, role_id)
            if not role:
                return False

            if role not in user.roles:
                user.roles.append(role)
                await self.db.commit()
                return True

            return False
        except SQLAlchemyError as e:
            self._logger.error(
                "assign_role_failed", user_id=user_id, role_id=role_id, error=str(e)
            )
            return False
