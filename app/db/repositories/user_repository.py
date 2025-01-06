"""
User repository implementation module.

This module provides the concrete implementation of user-related database operations,
extending the base repository with user-specific functionality. It handles all data
access operations for user management, including authentication-related queries
and relationship management.
"""

from typing import Optional, List, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.repositories.repository import BaseRepository
from app.db.models.user import User
from app.api.v1.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    User repository implementing user-specific database operations.

    This repository extends the base repository implementation with methods
    specific to user management, including authentication, role management,
    and user relationship handling.
    """

    def __init__(self, db: Session):
        """Initialize the user repository with a database session."""
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.

        Args:
            email: User's email address

        Returns:
            User instance if found, None otherwise
        """
        query = select(self._model).where(self._model.email == email)
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_user(self, user_id: int) -> Optional[User]:
        """
        Retrieve an active user by their ID.

        Args:
            user_id: User's unique identifier

        Returns:
            User instance if found and active, None otherwise
        """
        query = select(self._model).where(
            and_(self._model.id == user_id, self._model.is_active == True)
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, schema: UserCreate) -> User:
        """
        Create a new user with enhanced validation.

        Args:
            schema: User creation data

        Returns:
            Created user instance

        Raises:
            HTTPException: If email already exists
        """
        existing_user = await self.get_by_email(schema.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )

        return await self.create(schema)

    async def update_user(self, *, user_id: int, schema: UserUpdate) -> Optional[User]:
        """
        Update user information with conflict checking.

        Args:
            user_id: User's unique identifier
            schema: User update data

        Returns:
            Updated user instance

        Raises:
            HTTPException: If email update conflicts with existing user
        """
        if schema.email:
            existing_user = await self.get_by_email(schema.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )

        return await self.update(id=user_id, schema=schema)

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            User instance if authentication successful, None otherwise
        """
        user = await self.get_by_email(email)
        if not user or not user.is_active:
            return None

        # Note: Implement password verification based on your hashing strategy
        if not user.verify_password(password):
            return None

        await self.update_last_login(user.id)
        return user

    async def update_last_login(self, user_id: int) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User's unique identifier
        """
        user = await self.get(user_id)
        if user:
            user.record_login()
            await self._db.commit()

    async def verify_email(self, user_id: int) -> Optional[User]:
        """
        Mark user's email as verified.

        Args:
            user_id: User's unique identifier

        Returns:
            Updated user instance
        """
        user = await self.get(user_id)
        if user:
            user.verify_email()
            await self._db.commit()
            return user
        return None

    async def get_users_by_role(self, role_name: str) -> List[User]:
        """
        Retrieve users with a specific role.

        Args:
            role_name: Name of the role

        Returns:
            List of users with the specified role
        """
        query = (
            select(self._model)
            .join(self._model.roles)
            .where(
                and_(
                    self._model.roles.any(name=role_name), self._model.is_active == True
                )
            )
        )
        result = await self._db.execute(query)
        return result.scalars().all()

    async def search_users(
        self, *, search_term: str, skip: int = 0, limit: int = 10
    ) -> List[User]:
        """
        Search users by name or email.

        Args:
            search_term: Search term to match against user fields
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching users
        """
        query = (
            select(self._model)
            .where(
                and_(
                    self._model.is_active == True,
                    or_(
                        self._model.email.ilike(f"%{search_term}%"),
                        self._model.first_name.ilike(f"%{search_term}%"),
                        self._model.last_name.ilike(f"%{search_term}%"),
                    ),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self._db.execute(query)
        return result.scalars().all()

    async def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Deactivate a user account.

        Args:
            user_id: User's unique identifier

        Returns:
            Updated user instance
        """
        user = await self.get(user_id)
        if user:
            user.is_active = False
            await self._db.commit()
            return user
        return None

    async def reactivate_user(self, user_id: int) -> Optional[User]:
        """
        Reactivate a deactivated user account.

        Args:
            user_id: User's unique identifier

        Returns:
            Updated user instance
        """
        user = await self.get(user_id)
        if user:
            user.is_active = True
            await self._db.commit()
            return user
        return None
