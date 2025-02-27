"""
User Retrieval Mixin Module.

This module provides the mixin class that implements user retrieval operations,
such as fetching users by email, IDs, filters, and search functionality.
"""

from typing import Optional, List
from sqlalchemy import select, or_, and_
from sqlalchemy.exc import SQLAlchemyError

from app.db.models.user_model import User
from app.db.errors import QueryError


class UserRetrievalMixin:
    """
    Mixin class providing user retrieval operations.

    Expects the inheriting class to have:
        - _model: The User model.
        - db: The active SQLAlchemy database session.
        - _logger: Logger for error logging.
    """

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.

        Args:
            email (str): The user's email address.

        Returns:
            Optional[User]: The user if found; otherwise, None.

        Raises:
            QueryError: If the database query fails.
        """
        try:
            query = select(self._model).where(self._model.email == email)
            result = await self.db.execute(query)
            # Process the result immediately; don't return the result object
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.error("get_by_email_failed", email=email, error=str(e))
            raise QueryError(
                message="Failed to retrieve user by email",
                details={"email": email, "error": str(e)},
            ) from e

    async def get_by_ids(self, user_ids: List[int]) -> List[User]:
        """
        Retrieve multiple users by their IDs.

        Args:
            user_ids (List[int]): A list of user IDs.

        Returns:
            List[User]: A list of matching users.

        Raises:
            QueryError: If the database query fails.
        """
        try:
            query = select(self._model).where(self._model.id.in_(user_ids))
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error("get_by_ids_failed", user_ids=user_ids, error=str(e))
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
        Retrieve users based on provided filters.

        Args:
            is_active (Optional[bool]): Filter by active status.
            email_verified (Optional[bool]): Filter by email verification status.
            role_name (Optional[str]): Filter by role name.
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 100.

        Returns:
            List[User]: A list of users matching the filters.

        Raises:
            QueryError: If the database query fails.
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
            search_term (str): The search term.
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to return. Defaults to 100.
            active_only (bool, optional): Whether to include only active users. Defaults to True.

        Returns:
            List[User]: A list of users matching the search criteria.

        Raises:
            QueryError: If the database query fails.
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
            self._logger.error("search_failed", search_term=search_term, error=str(e))
            raise QueryError(
                message="Failed to search users",
                details={"search_term": search_term, "error": str(e)},
            ) from e
