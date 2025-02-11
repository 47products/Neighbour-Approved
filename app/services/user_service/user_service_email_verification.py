"""
Email Verification Service Module.

This module provides the EmailVerificationService class, responsible for
managing email verification workflows within the application.

Classes:
    EmailVerificationService: Handles the process of verifying user email addresses.
"""

from datetime import UTC, datetime
import structlog
from sqlalchemy.orm import Session

from app.db.models.role_model import Role
from app.db.models.user_model import User
from app.services.service_exceptions import (
    BusinessRuleViolationError,
    ValidationError,
)
from app.services.user_service.user_service_base_user import BaseUserService


class EmailVerificationService(BaseUserService):
    """Service for managing email verification processes.

    This service handles all aspects of email verification including
    eligibility checks, verification processing, and post-verification
    workflows.

    Inherits from:
        BaseUserService: Provides core user retrieval and update operations.
    """

    def __init__(self, db: Session):
        """Initialize email verification service.

        Args:
            db: Database session
        """
        super().__init__(db)
        self._logger = structlog.get_logger(__name__)

    async def verify_email(self, user_id: int) -> bool:
        """Mark a user's email as verified.

        This method implements the complete email verification workflow:
        1. Checks if user exists and is eligible for verification
        2. Updates verification status if not already verified
        3. Triggers post-verification processes

        Args:
            user_id: The unique identifier of the user to verify

        Returns:
            bool: True if verification was successful, False if already verified

        Raises:
            ResourceNotFoundError: If user does not exist
            ValidationError: If user is not eligible for verification
            BusinessRuleViolationError: If verification process fails
        """
        try:
            user = await self.get_user(user_id)

            # Check if already verified
            if user.email_verified:
                self._logger.info(
                    "email_already_verified", user_id=user_id, email=user.email
                )
                return False

            # Check verification eligibility
            if not await self._can_verify_email(user):
                raise ValidationError(
                    "User does not meet verification requirements",
                    details={"user_id": user_id},
                )

            # Update verification status
            user.email_verified = True
            user.verification_date = datetime.now(UTC)

            # Handle post-verification processes
            await self._handle_post_verification(user)

            await self.db.commit()

            self._logger.info(
                "email_verification_successful", user_id=user_id, email=user.email
            )
            return True

        except (ValidationError, BusinessRuleViolationError):
            await self.db.rollback()
            raise

        except Exception as e:
            self._logger.error(
                "email_verification_failed",
                user_id=user_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            await self.db.rollback()
            raise BusinessRuleViolationError("Email verification failed") from e

    async def _can_verify_email(self, user: User) -> bool:
        """Check if user meets verification requirements.

        This method implements business rules that determine whether a user
        is eligible for email verification. It checks various criteria including
        account status, user data completeness, and any time-based restrictions.

        Args:
            user: User to evaluate for verification eligibility

        Returns:
            bool: Whether user meets verification requirements

        Note:
            Current requirements include:
            - User must have an email address
            - User account must be active
            - Basic profile information must be complete
            - Required onboarding steps must be completed
        """
        try:
            if not user.email:
                self._logger.warning(
                    "verification_check_failed", user_id=user.id, reason="no_email"
                )
                return False

            if not user.is_active:
                self._logger.warning(
                    "verification_check_failed",
                    user_id=user.id,
                    reason="inactive_account",
                )
                return False

            # Check required profile data
            if not (user.first_name and user.last_name):
                self._logger.warning(
                    "verification_check_failed",
                    user_id=user.id,
                    reason="incomplete_profile",
                )
                return False

            # Check onboarding completion
            if not await self._has_completed_onboarding(user):
                self._logger.warning(
                    "verification_check_failed",
                    user_id=user.id,
                    reason="incomplete_onboarding",
                )
                return False

            return True

        except Exception as e:
            self._logger.error(
                "verification_check_error",
                user_id=user.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

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
                    .filter(Role.name == "verified_user", Role.is_active.is_(True))
                    .first()
                )
                if verified_role:
                    user.roles.append(verified_role)

            # Additional post-verification tasks can be added here
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
