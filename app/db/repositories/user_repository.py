"""
User Repository Module.

This module implements the User repository pattern, providing a centralized location
for all user-related database operations. It extends the base repository implementation
with user-specific functionality while maintaining consistent error handling, logging,
and transaction management.

The repository handles all CRUD operations for User entities, along with specialized
operations such as authentication, email verification, and role-based queries. It
ensures proper separation of concerns by encapsulating all database access logic
within repository methods.

Typical usage example:

    db = SessionLocal()
    user_repository = UserRepository(db)
    
    # Create a new user
    new_user = await user_repository.create_user(user_data)
    
    # Authenticate a user
    user = await user_repository.authenticate("user@example.com", "password")
    
    # Search for users
    users = await user_repository.search_users("john", limit=10)

The repository implements comprehensive error handling and logging, ensuring that
database operations are properly tracked and debugged when issues arise.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.db.repositories.repository_implementation import BaseRepository
from app.db.models.user_model import User
from app.api.v1.schemas.user_schema import UserCreate, UserUpdate
from app.core.error_handling import (
    DatabaseError,
    RecordNotFoundError,
    DuplicateRecordError,
)


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    User repository implementing user-specific database operations.

    This repository extends the base repository implementation with methods
    specific to user management, including authentication, role management,
    and user relationship handling. It provides a comprehensive interface
    for all user-related database operations while ensuring proper error
    handling and transaction management.

    The repository implements the following key functionalities:
    - User CRUD operations with enhanced validation
    - Authentication and session management
    - Email verification
    - Role-based user queries
    - User search and filtering
    - Account activation/deactivation

    Attributes:
        _model: The User model class
        _db: The database session
        _logger: Structured logger instance

    Typical usage example:
        repository = UserRepository(db_session)
        user = await repository.create_user(user_data)
        users = await repository.search_users("john")
    """

    def __init__(self, db: Session):
        """
        Initialize user repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(User, db)

    async def create_user(self, data: UserCreate) -> User:
        """
        Create a new user with enhanced validation.

        This method extends the base create operation with user-specific validation
        and error handling. It ensures email uniqueness and proper initialization
        of user attributes.

        Args:
            data: UserCreate schema containing validated user creation data

        Returns:
            User: Newly created user instance

        Raises:
            DuplicateRecordError: If a user with the same email already exists
            DatabaseError: If the database operation fails
            ValueError: If the provided data is invalid

        Example:
            user_data = UserCreate(email="user@example.com", password="secret")
            user = await repository.create_user(user_data)
        """
        try:
            self._logger.info("creating_user", email=data.email)

            # Check for existing user with same email
            if await self.get_by_email(data.email):
                raise DuplicateRecordError("User with this email already exists")

            user = await self.create(data)
            self._logger.info("user_created", user_id=user.id, email=user.email)
            return user

        except IntegrityError as e:
            self._logger.error("user_creation_failed", error=str(e), email=data.email)
            raise DatabaseError("Failed to create user") from e

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.

        This method provides a way to look up users by their email address,
        which is a common operation for authentication and user management.

        Args:
            email: User's email address

        Returns:
            Optional[User]: User instance if found, None otherwise

        Example:
            user = await repository.get_by_email("user@example.com")
        """
        query = select(self._model).where(self._model.email == email)
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_user(self, user_id: int) -> Optional[User]:
        """
        Retrieve an active user by their ID.

        This method retrieves a user only if they exist and their account
        is currently active. This is useful for operations that should only
        work with active user accounts.

        Args:
            user_id: User's unique identifier

        Returns:
            Optional[User]: User instance if found and active, None otherwise

        Example:
            active_user = await repository.get_active_user(123)
        """
        query = select(self._model).where(
            and_(self._model.id == user_id, self._model.is_active == True)
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def update_user(self, *, user_id: int, data: UserUpdate) -> User:
        """
        Update user information with conflict checking.

        This method implements user updates with additional validation and
        conflict checking. It ensures that email updates don't conflict with
        existing users and that the user exists before attempting updates.

        Args:
            user_id: User's unique identifier
            data: UserUpdate schema containing the fields to update

        Returns:
            User: Updated user instance

        Raises:
            RecordNotFoundError: If the user doesn't exist
            DuplicateRecordError: If the email update conflicts with existing user
            DatabaseError: If the database operation fails

        Example:
            updated_user = await repository.update_user(
                user_id=123,
                data=UserUpdate(email="new@example.com")
            )
        """
        try:
            # Verify user exists
            user = await self.get(user_id)
            if not user:
                raise RecordNotFoundError(f"User {user_id} not found")

            # Check email uniqueness if being updated
            if data.email and data.email != user.email:
                existing_user = await self.get_by_email(data.email)
                if existing_user:
                    raise DuplicateRecordError("Email already registered")

            updated_user = await self.update(id=user_id, schema=data)
            self._logger.info("user_updated", user_id=user_id)
            return updated_user

        except IntegrityError as e:
            self._logger.error("user_update_failed", error=str(e), user_id=user_id)
            raise DatabaseError("Failed to update user") from e

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Retrieve a user for authentication purposes.

        This method handles only the data retrieval aspect of authentication,
        leaving business logic to the service layer.

        Args:
            email: User's email address
            password: User's password (plain text)

        Returns:
            Optional[User]: User instance if found, None otherwise
        """
        return await self.get_by_email(email)

    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp.

        Records the current timestamp as the user's last login time.
        Handles only the data persistence aspect of the login tracking.

        Args:
            user_id: User's unique identifier

        Raises:
            DatabaseError: If the database operation fails
        """
        try:
            user = await self.get(user_id)
            if user:
                user.last_login = datetime.now()
                await self._db.commit()
                self._logger.info("last_login_updated", user_id=user_id)
        except Exception as e:
            self._logger.error(
                "last_login_update_failed",
                error=str(e),
                user_id=user_id,
                error_type=type(e).__name__,
            )
            await self._db.rollback()
            raise DatabaseError("Failed to update last login timestamp") from e

    async def search_users(
        self, search_term: str, skip: int = 0, limit: int = 10, active_only: bool = True
    ) -> List[User]:
        """
        Search users by name or email.

        This method provides a flexible search interface for finding users
        based on their name or email address. It supports pagination and
        can filter for active users only.

        Args:
            search_term: Term to search for in user names and email
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            active_only: Whether to include only active users

        Returns:
            List[User]: List of matching user instances

        Example:
            # Search for active users with "john" in their name or email
            users = await repository.search_users("john", limit=10)
        """
        query = (
            select(self._model)
            .where(
                and_(
                    self._model.is_active == True if active_only else True,
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

    async def get_users_by_role(self, role_name: str) -> List[User]:
        """
        Retrieve users with a specific role.

        This method finds all active users who have been assigned a particular role.
        It's useful for role-based access control and administrative functions.

        Args:
            role_name: Name of the role to search for

        Returns:
            List[User]: List of users with the specified role

        Example:
            admin_users = await repository.get_users_by_role("admin")
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

    async def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Deactivate a user account.

        This method marks a user account as inactive, effectively disabling
        their access to the system while preserving their data.

        Args:
            user_id: User's unique identifier

        Returns:
            Optional[User]: Updated user instance if successful, None if user not found

        Example:
            deactivated_user = await repository.deactivate_user(123)
        """
        user = await self.get(user_id)
        if user:
            user.is_active = False
            await self._db.commit()
            self._logger.info("user_deactivated", user_id=user_id)
            return user
        return None

    async def reactivate_user(self, user_id: int) -> Optional[User]:
        """
        Reactivate a deactivated user account.

        This method reactivates a previously deactivated user account,
        restoring their access to the system.

        Args:
            user_id: User's unique identifier

        Returns:
            Optional[User]: Updated user instance if successful, None if user not found

        Example:
            reactivated_user = await repository.reactivate_user(123)
        """
        user = await self.get(user_id)
        if user:
            user.is_active = True
            await self._db.commit()
            self._logger.info("user_reactivated", user_id=user_id)
            return user
        return None
