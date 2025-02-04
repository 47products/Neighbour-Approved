"""
Authentication Service Module.

This module provides the AuthenticationService class, responsible for
handling user authentication processes, including verifying credentials,
tracking login attempts, and managing authentication-related workflows.

Classes:
    AuthenticationService: Manages user authentication operations.
"""

from typing import Optional, Tuple, cast
from datetime import UTC, datetime, timedelta
from pydantic import EmailStr
import structlog

from app.core.error_handling import AuthenticationError
from app.db.models.user_model import User
from app.db.repositories.user_repository import UserRepository
from app.services.service_exceptions import ValidationError
from app.services.user_service.base_user import BaseUserService
from app.services.user_service.security import SecurityService


class AuthenticationService(BaseUserService):
    """Service for managing user authentication.

    This service handles all authentication-related operations including
    user verification, login tracking, and security enforcement.

    Inherits from:
        BaseUserService: Provides core user retrieval and update operations.

    Attributes:
        security_service: Service for handling password operations
        _logger: Structured logger instance
    """

    def __init__(self, db, security_service: SecurityService):
        """Initialize authentication service.

        Args:
            db: Database session
            security_service: Service for password operations
        """
        super().__init__(db)
        self.security_service = security_service
        self._logger = structlog.get_logger(__name__)

    async def authenticate(self, email: EmailStr, password: str) -> Optional[User]:
        """Authenticate a user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            Authenticated user or None if authentication fails

        Raises:
            ValidationError: If login attempts exceed limit
            AuthenticationError: If authentication fails
        """
        try:
            repository = cast(UserRepository, self.repository)
            user = await repository.get_by_email(email)

            if not user or not user.is_active:
                self._logger.info(
                    "authentication_failed",
                    email=email,
                    reason="user_not_found_or_inactive",
                )
                return None

            # Check if user is locked out
            if user.failed_login_lockout and user.failed_login_lockout > datetime.now(
                UTC
            ):
                raise ValidationError(
                    "Account temporarily locked. Please try again later.",
                    details={"lockout_until": user.failed_login_lockout},
                )

            if not await self.security_service.verify_password(user.password, password):
                await self._handle_failed_login(user)
                self._logger.info(
                    "authentication_failed",
                    email=email,
                    reason="invalid_password",
                )
                return None

            # Authentication successful - update last login
            user.last_login = datetime.now(UTC)
            user.failed_login_attempts = 0
            user.failed_login_lockout = None
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
                error_type=type(e).__name__,
            )
            raise

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
            Tuple containing authenticated user and whether this is first login

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

            # Check lockout status
            if user.failed_login_lockout and user.failed_login_lockout > datetime.now(
                UTC
            ):
                raise ValidationError(
                    "Account temporarily locked. Please try again later.",
                    details={"lockout_until": user.failed_login_lockout},
                )

            if not await self.security_service.verify_password(user.password, password):
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

        self._logger.info(
            "login_successful",
            user_id=user.id,
            email=user.email,
        )

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
