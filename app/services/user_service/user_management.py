"""
User Management Service Module.

This module provides the UserManagementService class, responsible for
managing user creation and deletion operations within the application.

Classes:
    UserManagementService: Handles the creation and deletion of user accounts.
"""

from typing import cast
import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.schemas.user_schema import UserCreate
from app.db.models.user_model import User
from app.db.repositories.user_repository import UserRepository
from app.services.service_exceptions import (
    DuplicateResourceError,
    AccessDeniedError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.user_service.base_user import BaseUserService
from app.services.user_service.security import SecurityService


class UserManagementService(BaseUserService):
    """Service for managing user account creation and deletion.

    This service handles all aspects of user lifecycle management, including
    account creation, validation, and secure deletion with proper checks.

    Inherits from:
        BaseUserService: Provides core user retrieval and update operations.

    Attributes:
        security_service: Service for password operations
        _logger: Structured logger instance
    """

    def __init__(self, db: Session, security_service: SecurityService):
        """Initialize the user management service.

        Args:
            db: Database session for repository operations
            security_service: Service for handling password operations
        """
        super().__init__(db)
        self.security_service = security_service
        self._logger = structlog.get_logger(__name__)

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user account.

        This method validates the input data, checks for existing users,
        and creates a new user record with proper password hashing.

        Args:
            data: Schema containing validated user data
                - email: User's email address
                - password: Plain text password
                - first_name: User's first name
                - last_name: User's last name

        Returns:
            Newly created user instance

        Raises:
            DuplicateResourceError: If email already registered
            ValidationError: If data is invalid
            SQLAlchemyError: If database operation fails

        Example:
            user = await service.create_user(
                UserCreate(
                    email="user@example.com",
                    password="SecureP@ss123",
                    first_name="John",
                    last_name="Doe"
                )
            )
        """
        try:
            # Check for existing user
            repository = cast(UserRepository, self.repository)
            existing_user = await repository.get_by_email(data.email)
            if existing_user:
                self._logger.warning(
                    "user_creation_duplicate_email",
                    email=data.email,
                )
                raise DuplicateResourceError(
                    "Email already registered",
                    details={"email": data.email},
                )

            # Hash password
            hashed_password = await self.security_service.hash_password(data.password)
            user_data = data.model_copy()
            user_data.password = hashed_password

            user = await self.create(user_data)

            self._logger.info(
                "user_created",
                user_id=user.id,
                email=user.email,
            )
            return user

        except (ValidationError, DuplicateResourceError):
            raise

        except SQLAlchemyError as e:
            self._logger.error(
                "user_creation_failed",
                email=data.email,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def delete_user(self, user_id: int) -> bool:
        """Delete an existing user account.

        This method checks if the user can be safely deleted and handles
        the deletion process with proper cleanup.

        Args:
            user_id: The unique identifier of the user to delete

        Returns:
            True if user was successfully deleted

        Raises:
            ResourceNotFoundError: If user not found
            AccessDeniedError: If user cannot be deleted
            SQLAlchemyError: If deletion fails

        Example:
            success = await service.delete_user(user_id=123)
        """
        try:
            user = await self.get_user(user_id)

            # Check if user can be deleted
            if not await self._can_delete_user(user):
                raise AccessDeniedError(
                    "Cannot delete user with active communities",
                    details={"user_id": user_id},
                )

            # Perform deletion
            success = await self.delete(user_id)

            if success:
                self._logger.info(
                    "user_deleted",
                    user_id=user_id,
                    email=user.email,
                )

            return success

        except (ResourceNotFoundError, AccessDeniedError):
            raise

        except SQLAlchemyError as e:
            self._logger.error(
                "user_deletion_failed",
                user_id=user_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def _can_delete_user(self, user: User) -> bool:
        """Check if user can be deleted based on business rules.

        A user cannot be deleted if they:
        - Own any active communities
        - Have active contacts
        - Have pending endorsements
        - Have special system roles

        Args:
            user: User to check for deletion eligibility

        Returns:
            Whether user can be deleted

        Example:
            can_delete = await service._can_delete_user(user)
        """
        # Check if user owns any active communities
        if any(community.is_active for community in user.owned_communities):
            self._logger.warning(
                "user_deletion_blocked_communities",
                user_id=user.id,
                email=user.email,
            )
            return False

        # Check if user has any active contacts
        if any(contact.is_active for contact in user.contacts):
            self._logger.warning(
                "user_deletion_blocked_contacts",
                user_id=user.id,
                email=user.email,
            )
            return False

        # Check for pending endorsements
        if any(
            not endorsement.is_verified for endorsement in user.contact_endorsements
        ):
            self._logger.warning(
                "user_deletion_blocked_endorsements",
                user_id=user.id,
                email=user.email,
            )
            return False

        # Check for system roles
        if any(role.is_system_role for role in user.roles if role.is_active):
            self._logger.warning(
                "user_deletion_blocked_system_role",
                user_id=user.id,
                email=user.email,
            )
            return False

        return True
