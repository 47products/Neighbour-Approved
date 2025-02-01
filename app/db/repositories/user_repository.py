"""
User Repository Module.

This module implements the User repository pattern, providing a centralized location
for all user-related database operations. It focuses purely on data access operations,
leaving business logic to the service layer.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.role_model import Role
from app.db.repositories.repository_implementation import BaseRepository
from app.db.models.user_model import User
from app.api.v1.schemas.user_schema import UserCreate, UserUpdate
from app.db.errors import (
    QueryError,
    IntegrityError,
)


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for user data access operations.

    This repository handles all database operations related to user entities,
    implementing a clean separation between data access and business logic.

    Attributes:
        _model: The User model class
        _db: The database session
        _logger: Structured logger instance
    """

    def __init__(self, db: Session):
        """
        Initialize user repository.

        Args:
            db: Database session for operations
        """
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.

        Args:
            email: User's email address

        Returns:
            Optional[User]: User if found, None otherwise

        Raises:
            QueryError: If database query fails
        """
        try:
            query = select(self._model).where(self._model.email == email)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            self._logger.error(
                "get_by_email_failed",
                email=email,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve user by email",
                details={"email": email, "error": str(e)},
            ) from e

    async def get_by_ids(self, user_ids: List[int]) -> List[User]:
        """
        Retrieve multiple users by their IDs.

        Args:
            user_ids: List of user IDs

        Returns:
            List[User]: List of found users

        Raises:
            QueryError: If database query fails
        """
        try:
            query = select(self._model).where(self._model.id.in_(user_ids))
            result = await self.db.execute(query)
            return list(result.scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(
                "get_by_ids_failed",
                user_ids=user_ids,
                error=str(e),
            )
            raise QueryError(
                message="Failed to retrieve users by IDs",
                details={"user_ids": user_ids, "error": str(e)},
            ) from e

    async def get_by_filters(
        self,
        *,
        is_active: Optional[bool] = None,
        email_verified: Optional[bool] = None,
        role_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        Retrieve users based on filters.

        Args:
            is_active: Filter by active status
            email_verified: Filter by email verification status
            role_name: Filter by role name
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List[User]: List of matching users

        Raises:
            QueryError: If database query fails
        """
        try:
            query = select(self._model)
            conditions = []

            if is_active is not None:
                conditions.append(self._model.is_active.is_(is_active))
            if email_verified is not None:
                conditions.append(self._model.email_verified.is_(email_verified))
            if role_name is not None:
                conditions.append(self._model.roles.any(name=role_name))

            if conditions:
                query = query.where(and_(*conditions))

            query = query.offset(skip).limit(limit)
            result = await self.db.execute(query)
            return list(result.scalars().all())

        except SQLAlchemyError as e:
            self._logger.error("get_by_filters_failed", error=str(e))
            raise QueryError(
                message="Failed to retrieve filtered users",
                details={"error": str(e)},
            ) from e

    async def search(
        self,
        search_term: str,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[User]:
        """
        Search users by name or email.

        Args:
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum records to return
            active_only: Whether to include only active users

        Returns:
            List[User]: List of matching users

        Raises:
            QueryError: If database query fails
        """
        try:
            conditions = [
                or_(
                    self._model.email.ilike(f"%{search_term}%"),
                    self._model.first_name.ilike(f"%{search_term}%"),
                    self._model.last_name.ilike(f"%{search_term}%"),
                )
            ]

            if active_only:
                conditions.append(self._model.is_active.is_(True))

            query = (
                select(self._model).where(and_(*conditions)).offset(skip).limit(limit)
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(
                "search_failed",
                search_term=search_term,
                error=str(e),
            )
            raise QueryError(
                message="Failed to search users",
                details={"search_term": search_term, "error": str(e)},
            ) from e

    async def update_last_login(self, user_id: int, timestamp: datetime) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID
            timestamp: Login timestamp

        Raises:
            IntegrityError: If update fails
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
                "update_last_login_failed",
                user_id=user_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to update last login",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def update_status(self, user_id: int, is_active: bool) -> None:
        """
        Update user's active status.

        Args:
            user_id: User ID
            is_active: New active status

        Raises:
            IntegrityError: If update fails
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
            self._logger.error(
                "update_status_failed",
                user_id=user_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to update user status",
                details={"user_id": user_id, "error": str(e)},
            ) from e

    async def bulk_update_status(self, user_ids: List[int], is_active: bool) -> int:
        """
        Update status for multiple users.

        Args:
            user_ids: List of user IDs
            is_active: New active status

        Returns:
            int: Number of users updated

        Raises:
            IntegrityError: If update fails
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
                "bulk_status_update_failed",
                user_ids=user_ids,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to update user statuses",
                details={"user_ids": user_ids, "error": str(e)},
            ) from e

    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id (int): The ID of the user.
            role_id (int): The ID of the role.

        Returns:
            bool: True if the role was assigned, False otherwise.
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
        except Exception as e:
            self._logger.error(
                "assign_role_failed", user_id=user_id, role_id=role_id, error=str(e)
            )
            return False
