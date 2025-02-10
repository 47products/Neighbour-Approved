"""
Base User Service Module.

This module provides the BaseUserService class, which offers core user
retrieval and update operations. It serves as a foundational service
for user-related functionalities in the application.

Classes:
    BaseUserService: Handles core user retrieval and update operations.
"""

from typing import List, Optional, Dict, Any
import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.transaction_manager import TransactionManager
from app.services.base import BaseService
from app.services.service_interfaces import (
    IAuthenticationService,
    IEmailVerificationService,
    IRoleManagementService,
    IUserManagementService,
)
from app.db.models.user_model import User
from app.db.models.community_model import Community
from app.db.repositories.user_repository import UserRepository
from app.services.service_exceptions import (
    ResourceNotFoundError,
    ValidationError,
    BusinessRuleViolationError,
)
from app.api.v1.schemas.user_schema import UserCreate, UserUpdate


class BaseUserService(
    BaseService[User, UserCreate, UserUpdate, UserRepository],
    IAuthenticationService,
    IEmailVerificationService,
    IRoleManagementService,
    IUserManagementService,
):
    """Core service for user retrieval and updates.

    This service provides foundational user operations and serves as a base
    for more specialized user services. It implements basic CRUD operations
    with proper transaction management and error handling.

    Inherits from:
        BaseService[User, UserCreate, UserUpdate, UserRepository]: Provides
        basic CRUD operations with appropriate type parameters.

    Attributes:
        _repository (UserRepository): Repository instance for user data operations
        _logger: Structured logger instance for service operations
    """

    def __init__(self, db: Session):
        """Initialize the BaseUserService.

        Args:
            db: Database session for repository operations

        Example:
            service = BaseUserService(db_session)
        """
        super().__init__(
            model=User,
            repository=UserRepository(db),
            logger_name="BaseUserService",
        )
        self._logger = structlog.get_logger(__name__)

    async def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user by their unique identifier.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            User object if found

        Raises:
            ResourceNotFoundError: If no user with the specified ID exists

        Example:
            user = await service.get_user(user_id=1)
        """
        user = await self.get(user_id)
        if not user:
            self._logger.warning("user_not_found", user_id=user_id)
            raise ResourceNotFoundError(f"User {user_id} not found")
        return user

    async def update_user(self, user_id: int, data: UserUpdate) -> Optional[User]:
        """Update a user's information within a transaction.

        Args:
            user_id: The ID of the user to update
            data: Update schema containing the changes

        Returns:
            Updated User object

        Raises:
            ResourceNotFoundError: If the user does not exist
            ValidationError: If the update data is invalid
            BusinessRuleViolationError: If update violates business rules

        Example:
            user = await service.update_user(1, update_data)
        """
        transaction_manager = TransactionManager(self.db)
        try:
            async with transaction_manager.transaction():
                # Verify user exists
                user = await self.get_user(user_id)

                # Validate update data
                await self._validate_update(user, data)

                # Apply updates
                for key, value in data.model_dump(exclude_unset=True).items():
                    setattr(user, key, value)

                # No need to explicitly commit here (handled by transaction manager)
                await self.db.refresh(user)

                self._logger.info(
                    "user_updated",
                    user_id=user_id,
                    fields=list(data.model_dump(exclude_unset=True).keys()),
                )
                return user

        except (ValidationError, BusinessRuleViolationError):
            raise

        except SQLAlchemyError as e:
            self._logger.error(
                "update_failed",
                user_id=user_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            # Remove the extra rollback call here
            # await self.db.rollback()
            raise BusinessRuleViolationError(f"Failed to update user {user_id}") from e

    async def get_user_communities(self, user_id: int) -> List[Community]:
        """Get communities associated with user.

        Args:
            user_id: User's unique identifier

        Returns:
            List of communities user belongs to

        Raises:
            ResourceNotFoundError: If user not found

        Example:
            communities = await service.get_user_communities(user_id=1)
        """
        user = await self.get_user(user_id)
        return user.communities

    async def _validate_update(self, user: User, data: UserUpdate) -> None:
        """Validate user update data against business rules.

        Args:
            user: Existing user record
            data: Update data to validate

        Raises:
            ValidationError: If update data violates business rules
            BusinessRuleViolationError: If update violates system constraints
        """
        # Example validation - customize based on business rules
        if data.email and data.email != user.email:
            # Check email uniqueness
            existing = await self.repository.get_by_email(data.email)
            if existing and existing.id != user.id:
                raise ValidationError(
                    "Email already registered",
                    details={"field": "email"},
                )

    async def process_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate filter criteria for user queries.

        This method ensures that any filters applied to user queries are valid
        and follow business rules.

        Args:
            filters: Raw filter criteria

        Returns:
            Processed filter criteria

        Example:
            processed = await service.process_filters({"status": "active"})
        """
        processed_filters = filters.copy()

        # Process status filters
        if "status" in processed_filters:
            processed_filters["is_active"] = processed_filters.pop("status") == "active"

        # Add any additional filter processing logic here

        return processed_filters
