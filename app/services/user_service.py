"""
User service implementation module for Neighbour Approved application.

This module implements the user management service layer, handling all
user-related business logic including authentication, role management,
and user lifecycle operations. It ensures proper separation of concerns
by encapsulating business rules and workflows separate from data access.
"""

from datetime import datetime, UTC, timedelta
from typing import List, Optional, Tuple, cast
import bcrypt
from pydantic import EmailStr
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.error_handling import AuthenticationError
from app.services.base import BaseService
from app.services.interfaces import IUserService
from app.services.exceptions import (
    BusinessRuleViolationError,
    ValidationError,
    AccessDeniedError,
    DuplicateResourceError,
    ResourceNotFoundError,
)
from app.db.models.user_model import User
from app.db.models.community_model import Community
from app.db.models.role_model import Role
from app.db.repositories.user_repository import UserRepository
from app.api.v1.schemas.user_schema import UserCreate, UserUpdate


class UserService(BaseService[User, UserCreate, UserUpdate], IUserService):
    """
    Service for managing user-related operations and business logic.

    This service implements user management operations including authentication,
    profile management, role assignments, and user verification workflows. It
    encapsulates all user-related business rules and validation logic.
    """

    def __init__(self, db: Session):
        """Initialize the user service.

        Args:
            db: Database session for repository operations
        """
        super().__init__(
            model=User,
            repository=UserRepository(db),
            logger_name="UserService",
        )

    async def authenticate(self, email: EmailStr, password: str) -> Optional[User]:
        """Authenticate a user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            Authenticated user or None if authentication fails

        Raises:
            ValidationError: If login attempts exceed limit
        """
        try:
            # Repository cast needed for type checking
            repository = cast(UserRepository, self.repository)
            user = await repository.get_by_email(email)

            if not user or not user.is_active:
                self._logger.info(
                    "authentication_failed",
                    email=email,
                    reason="user_not_found_or_inactive",
                )
                return None

            if not user.verify_password(password):
                self._logger.info(
                    "authentication_failed",
                    email=email,
                    reason="invalid_password",
                )
                return None

            # Update last login timestamp
            user.last_login = datetime.now(UTC)
            await self.db.commit()

            self._logger.info(
                "authentication_successful",
                user_id=user.id,
                email=email,
            )
            return user

        except Exception as e:
            self._logger.error(
                "authentication_error",
                email=email,
                error=str(e),
            )
            raise

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user with validation.

        Args:
            data: User creation data

        Returns:
            Created user instance

        Raises:
            DuplicateResourceError: If email already exists
            ValidationError: If validation fails
        """
        # Check for existing user
        repository = cast(UserRepository, self.repository)
        existing_user = await repository.get_by_email(data.email)
        if existing_user:
            raise DuplicateResourceError(
                "Email already registered",
                details={"email": data.email},
            )

        return await self.create(data)

    async def validate_create(self, data: UserCreate) -> None:
        """Validate user creation data.

        Args:
            data: User creation data

        Raises:
            ValidationError: If validation fails
        """
        if len(data.password) < 8:
            raise ValidationError(
                "Password must be at least 8 characters",
                details={"field": "password"},
            )

        # Add additional validation rules here
        await super().validate_create(data)

    async def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID.

        Args:
            user_id: User's unique identifier

        Returns:
            User instance if found and active

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        return user

    async def update_user(self, user_id: int, data: UserUpdate) -> Optional[User]:
        """Update user information.

        Args:
            user_id: User's unique identifier
            data: Update data

        Returns:
            Updated user instance

        Raises:
            ResourceNotFoundError: If user not found
            ValidationError: If validation fails
            DuplicateResourceError: If email update conflicts
        """
        # Check email uniqueness if being updated
        if data.email:
            repository = cast(UserRepository, self.repository)
            existing_user = await repository.get_by_email(data.email)
            if existing_user and existing_user.id != user_id:
                raise DuplicateResourceError(
                    "Email already registered",
                    details={"email": data.email},
                )

        return await self.update(id=user_id, data=data)

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user account.

        Args:
            user_id: User's unique identifier

        Returns:
            True if user was deleted

        Raises:
            AccessDeniedError: If user cannot be deleted
            ResourceNotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        # Check if user can be deleted
        if not await self._can_delete_user(user):
            raise AccessDeniedError("Cannot delete user with active communities")

        return await self.delete(user_id)

    async def _can_delete_user(self, user: User) -> bool:
        """Check if user can be deleted based on business rules.

        A user cannot be deleted if they:
        - Own any active communities
        - Have active contacts
        - Have pending endorsements
        - Have special system roles

        Args:
            user: User to check

        Returns:
            Whether user can be deleted
        """
        # Check if user owns any active communities
        if any(community.is_active for community in user.owned_communities):
            return False

        # Check if user has any active contacts
        if any(contact.is_active for contact in user.contacts):
            return False

        # Check for pending endorsements
        if any(
            not endorsement.is_verified for endorsement in user.contact_endorsements
        ):
            return False

        # Check for system roles
        if any(role.is_system_role for role in user.roles if role.is_active):
            return False

        return True

    async def verify_email(self, user_id: int) -> bool:
        """Mark user's email as verified.

        Args:
            user_id: User's unique identifier

        Returns:
            True if email was verified

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        if user.email_verified:
            return True

        user.email_verified = True
        await self.db.commit()

        self._logger.info(
            "email_verified",
            user_id=user_id,
            email=user.email,
        )
        return True

    async def assign_role(self, user_id: int, role_id: int) -> Optional[User]:
        """Assign a role to a user.

        Args:
            user_id: User's unique identifier
            role_id: Role to assign

        Returns:
            Updated user instance

        Raises:
            ResourceNotFoundError: If user or role not found
            ValidationError: If role assignment is invalid
        """
        user = await self.get_user(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        role = await self.db.get(Role, role_id)
        if not role or not role.is_active:
            raise ResourceNotFoundError(f"Role {role_id} not found")

        if role in user.roles:
            return user

        user.roles.append(role)
        await self.db.commit()

        self._logger.info(
            "role_assigned",
            user_id=user_id,
            role_id=role_id,
            role_name=role.name,
        )
        return user

    async def remove_role(self, user_id: int, role_id: int) -> Optional[User]:
        """Remove a role from a user.

        Args:
            user_id: User's unique identifier
            role_id: Role to remove

        Returns:
            Updated user instance

        Raises:
            ResourceNotFoundError: If user or role not found
            ValidationError: If role removal is invalid
        """
        user = await self.get_user(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        role = await self.db.get(Role, role_id)
        if not role:
            raise ResourceNotFoundError(f"Role {role_id} not found")

        if role not in user.roles:
            return user

        user.roles.remove(role)
        await self.db.commit()

        self._logger.info(
            "role_removed",
            user_id=user_id,
            role_id=role_id,
            role_name=role.name,
        )
        return user

    async def get_user_communities(self, user_id: int) -> List[Community]:
        """Get communities associated with user.

        Args:
            user_id: User's unique identifier

        Returns:
            List of communities user belongs to

        Raises:
            ResourceNotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        return user.communities

    async def _can_verify_email(self, user: User) -> bool:
        """Check if user meets verification requirements.

        This method implements business rules that determine whether a user
        is eligible for email verification. It checks various criteria including
        account status, user data completeness, and any time-based restrictions.

        Args:
            user: User to evaluate for verification eligibility

        Returns:
            bool: Whether user meets verification requirements
        """
        if not user.email:
            return False

        if not user.is_active:
            return False

        # Check required profile data
        if not (user.first_name and user.last_name):
            return False

        # Example: Check if user has completed any required initial steps
        if not await self._has_completed_onboarding(user):
            return False

        return True

    async def _has_completed_onboarding(self, user: User) -> bool:
        """Check if user has completed required onboarding steps.

        This helper method evaluates whether a user has completed all required
        onboarding steps necessary for verification. This may include profile
        completion, accepting terms, or other business requirements.

        Args:
            user: User to check onboarding status

        Returns:
            bool: Whether onboarding is complete
        """
        # Add onboarding checks based on business requirements
        required_fields = [
            user.email,
            user.first_name,
            user.last_name,
            user.country,  # Optional based on requirements
        ]
        return all(required_fields)

    async def _handle_post_verification(self, user: User) -> None:
        """Handle post-verification workflows and updates.

        This method manages all actions that should occur after successful
        email verification, such as role assignments, community access,
        or notification triggers.

        Args:
            user: Newly verified user

        Raises:
            BusinessRuleViolationError: If post-verification actions fail
        """
        try:
            # Assign basic verified user role if not present
            if not any(role.name == "verified_user" for role in user.roles):
                verified_role = (
                    await self.db.query(Role)
                    .filter(Role.name == "verified_user", Role.is_active == True)
                    .first()
                )
                if verified_role:
                    user.roles.append(verified_role)

            # Update verification timestamp
            user.verification_date = datetime.now(UTC)
            await self.db.commit()

            self._logger.info(
                "post_verification_complete",
                user_id=user.id,
                email=user.email,
            )

        except Exception as e:
            self._logger.error(
                "post_verification_failed",
                user_id=user.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise BusinessRuleViolationError(
                "Failed to complete post-verification workflow"
            ) from e

    async def hash_password(self, password: str) -> str:
        """Generate secure password hash using bcrypt.

        Args:
            password: Plain text password to hash

        Returns:
            str: Securely hashed password

        Raises:
            ValidationError: If password does not meet requirements
        """
        if not self._validate_password_strength(password):
            raise ValidationError("Password does not meet security requirements")

        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements.

        Password must:
        - Be at least 8 characters long
        - Contain at least one uppercase letter
        - Contain at least one lowercase letter
        - Contain at least one number
        - Contain at least one special character

        Args:
            password: Password to validate

        Returns:
            bool: Whether password meets requirements
        """
        if len(password) < 8:
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        return all([has_upper, has_lower, has_digit, has_special])

    async def verify_password(self, stored_hash: str, password: str) -> bool:
        """Securely verify a password against stored hash.

        Args:
            stored_hash: Hashed password from database
            password: Plain text password to verify

        Returns:
            bool: Whether password matches hash
        """
        return bcrypt.checkpw(password.encode(), stored_hash.encode())

    async def authenticate_user(
        self, email: EmailStr, password: str, track_login: bool = True
    ) -> Tuple[User, bool]:
        """Authenticate user with email and password.

        This method implements the complete authentication workflow including
        password verification, account status validation, and login tracking.

        Args:
            email: User's email address
            password: Plain text password
            track_login: Whether to record successful login

        Returns:
            Tuple[User, bool]: Authenticated user and whether this is first login

        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If input validation fails
        """
        try:
            user = await self.repository.get_by_email(email)
            if not user:
                raise AuthenticationError("Invalid email or password")

            if not user.is_active:
                raise AuthenticationError("Account is deactivated")

            if not await self.verify_password(user.password, password):
                await self._handle_failed_login(user)
                raise AuthenticationError("Invalid email or password")

            is_first_login = user.last_login is None
            if track_login:
                await self._track_successful_login(user)

            return user, is_first_login

        except Exception as e:
            self._logger.error(
                "authentication_failed",
                email=email,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def _track_successful_login(self, user: User) -> None:
        """Record successful login attempt.

        Updates user's last login timestamp and resets any failed login tracking.

        Args:
            user: User who successfully logged in
        """
        user.last_login = datetime.now(UTC)
        user.failed_login_attempts = 0
        user.failed_login_lockout = None
        await self.db.commit()

        self._logger.info("login_successful", user_id=user.id, email=user.email)

    async def _handle_failed_login(self, user: User) -> None:
        """Handle failed login attempt.

        Implements progressive lockout policy for failed attempts:
        - First 3 failures: No lockout
        - 4-6 failures: 15 minute lockout
        - 7+ failures: 1 hour lockout

        Args:
            user: User who failed to log in
        """
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

        if user.failed_login_attempts >= 7:
            lockout_duration = timedelta(hours=1)
        elif user.failed_login_attempts >= 4:
            lockout_duration = timedelta(minutes=15)
        else:
            lockout_duration = None

        if lockout_duration:
            user.failed_login_lockout = datetime.now(UTC) + lockout_duration

        await self.db.commit()

        self._logger.warning(
            "login_failed",
            user_id=user.id,
            email=user.email,
            attempts=user.failed_login_attempts,
            lockout_duration=lockout_duration,
        )
