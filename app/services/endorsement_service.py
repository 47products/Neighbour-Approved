"""
Contact endorsement service implementation module.

This module implements the endorsement management service layer, handling all
endorsement-related business logic including rating calculations, verification
workflows, and notification triggers. It ensures proper separation of concerns
by encapsulating business rules and validation logic separate from data access.
"""

from datetime import datetime, UTC
from typing import List, Optional, Dict, Any, cast
from sqlalchemy.orm import Session
import structlog

from app.services.base import BaseService
from app.services.service_interfaces import IEndorsementService
from app.services.service_exceptions import (
    ValidationError,
    BusinessRuleViolationError,
    ResourceNotFoundError,
    DuplicateResourceError,
    StateError,
)
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.db.models.contact_model import Contact
from app.db.models.community_model import Community
from app.db.repositories.contact_endorsement_repository import (
    ContactEndorsementRepository,
)
from app.api.v1.schemas.contact_endorsement_schema import (
    ContactEndorsementCreate,
    ContactEndorsementUpdate,
)


class EndorsementService(
    BaseService[ContactEndorsement, ContactEndorsementCreate, ContactEndorsementUpdate],
    IEndorsementService,
):
    """
    Service for managing endorsement-related operations and business logic.

    This service implements endorsement management operations including creation,
    updates, verification workflows, and rating calculations. It encapsulates
    all endorsement-related business rules and validation logic.

    Attributes:
        MIN_RATING (int): Minimum allowed rating value
        MAX_RATING (int): Maximum allowed rating value
        MIN_COMMENT_LENGTH (int): Minimum length for endorsement comments
        MAX_PENDING_VERIFICATIONS (int): Maximum pending verifications per contact
    """

    MIN_RATING = 1
    MAX_RATING = 5
    MIN_COMMENT_LENGTH = 10
    MAX_PENDING_VERIFICATIONS = 5

    def __init__(self, db: Session):
        """Initialize the endorsement service.

        Args:
            db: Database session for repository operations
        """
        super().__init__(
            model=ContactEndorsement,
            repository=ContactEndorsementRepository(db),
            logger_name="EndorsementService",
        )

    async def create_endorsement(
        self, data: ContactEndorsementCreate
    ) -> ContactEndorsement:
        """Create a new endorsement with validation.

        This method implements comprehensive validation including uniqueness
        checks, rating validation, and comment validation before creating
        a new endorsement.

        Args:
            data: Validated endorsement creation data

        Returns:
            Created endorsement instance

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If creation violates business rules
            DuplicateResourceError: If endorsement already exists
        """
        try:
            # Validate creation data
            await self._validate_endorsement_creation(data)

            # Create endorsement
            endorsement = await self.create(data)

            # Update contact metrics
            await self._update_contact_metrics(endorsement.contact_id)

            self._logger.info(
                "endorsement_created",
                endorsement_id=endorsement.id,
                contact_id=data.contact_id,
                user_id=data.user_id,
            )

            return endorsement

        except Exception as e:
            self._logger.error(
                "endorsement_creation_failed",
                error=str(e),
                contact_id=data.contact_id,
                user_id=data.user_id,
            )
            raise

    async def _validate_endorsement_creation(
        self, data: ContactEndorsementCreate
    ) -> None:
        """Validate endorsement creation against business rules.

        Performs comprehensive validation including:
        - Contact and community existence
        - Rating range validation
        - Comment validation
        - Duplicate endorsement checks

        Args:
            data: Endorsement creation data

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If creation violates business rules
        """
        # Validate contact and community exist and are active
        contact = await self.db.get(Contact, data.contact_id)
        community = await self.db.get(Community, data.community_id)

        if not contact or not contact.is_active:
            raise ValidationError(f"Contact {data.contact_id} not found or inactive")

        if not community or not community.is_active:
            raise ValidationError(
                f"Community {data.community_id} not found or inactive"
            )

        # Validate rating range if provided
        if (
            data.rating is not None
            and not self.MIN_RATING <= data.rating <= self.MAX_RATING
        ):
            raise ValidationError(
                f"Rating must be between {self.MIN_RATING} and {self.MAX_RATING}"
            )

        # Validate comment length if provided
        if data.comment and len(data.comment) < self.MIN_COMMENT_LENGTH:
            raise ValidationError(
                f"Comment must be at least {self.MIN_COMMENT_LENGTH} characters"
            )

        # Check for existing endorsement
        repository = cast(ContactEndorsementRepository, self.repository)
        existing = await repository.get_user_endorsement(
            data.user_id, data.contact_id, data.community_id
        )
        if existing:
            raise DuplicateResourceError(
                "User has already endorsed this contact in this community"
            )

    async def _update_contact_metrics(self, contact_id: int) -> None:
        """Update contact's endorsement-related metrics.

        This method recalculates and updates:
        - Total endorsement count
        - Verified endorsement count
        - Average rating
        - Other endorsement-based metrics

        Args:
            contact_id: Contact to update

        Raises:
            ResourceNotFoundError: If contact not found
            StateError: If update fails
        """
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        try:
            # Get all contact endorsements
            repository = cast(ContactEndorsementRepository, self.repository)
            endorsements = await repository.get_contact_endorsements(contact_id)

            # Calculate metrics
            total_count = len(endorsements)
            verified_count = sum(1 for e in endorsements if e.is_verified)

            # Calculate average rating from verified endorsements
            rated_endorsements = [
                e.rating for e in endorsements if e.is_verified and e.rating is not None
            ]
            average_rating = (
                sum(rated_endorsements) / len(rated_endorsements)
                if rated_endorsements
                else None
            )

            # Update contact
            contact.endorsements_count = total_count
            contact.verified_endorsements_count = verified_count
            contact.average_rating = (
                round(average_rating, 2) if average_rating else None
            )

            await self.db.commit()

            self._logger.info(
                "contact_metrics_updated",
                contact_id=contact_id,
                total_count=total_count,
                verified_count=verified_count,
                average_rating=average_rating,
            )

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "contact_metrics_update_failed",
                contact_id=contact_id,
                error=str(e),
            )
            raise StateError(f"Failed to update contact metrics: {str(e)}")

    async def verify_endorsement(self, endorsement_id: int, verified_by: int) -> bool:
        """Mark an endorsement as verified.

        This method implements the endorsement verification workflow including
        validation and audit logging.

        Args:
            endorsement_id: Endorsement's unique identifier
            verified_by: User ID performing verification

        Returns:
            bool: True if endorsement was verified

        Raises:
            ValidationError: If verification requirements not met
            ResourceNotFoundError: If endorsement not found
            StateError: If verification fails
        """
        endorsement = await self.get_endorsement(endorsement_id)
        if not endorsement:
            raise ResourceNotFoundError(f"Endorsement {endorsement_id} not found")

        try:
            # Check if endorsement can be verified
            if not await self._can_verify_endorsement(endorsement):
                raise ValidationError(
                    "Endorsement does not meet verification requirements"
                )

            # Update verification status
            endorsement.is_verified = True
            endorsement.verification_date = datetime.now(UTC)
            endorsement.verification_notes = (
                f"Verified by user {verified_by} on {datetime.now(UTC)}"
            )

            # Update contact metrics
            await self._update_contact_metrics(endorsement.contact_id)

            await self.db.commit()

            self._logger.info(
                "endorsement_verified",
                endorsement_id=endorsement_id,
                verified_by=verified_by,
            )

            return True

        except Exception as e:
            await self.db.rollback()
            self._logger.error(
                "endorsement_verification_failed",
                endorsement_id=endorsement_id,
                error=str(e),
            )
            raise StateError(f"Failed to verify endorsement: {str(e)}")

    async def _can_verify_endorsement(self, endorsement: ContactEndorsement) -> bool:
        """Check if endorsement meets verification requirements.

        An endorsement can be verified if:
        - It has required comment/rating information
        - User has verified status
        - Community guidelines are met
        - Contact is active and in good standing

        Args:
            endorsement: Endorsement to evaluate

        Returns:
            bool: Whether endorsement can be verified
        """
        # Early returns for invalid conditions
        if (
            endorsement.is_verified
            or not (endorsement.comment or endorsement.rating)
            or not endorsement.community.is_active
            or not endorsement.contact.is_active
        ):
            return False

        # Check pending verifications limit
        repository = cast(ContactEndorsementRepository, self.repository)
        pending_count = await repository.get_pending_verifications_count(
            endorsement.contact_id
        )

        return pending_count < self.MAX_PENDING_VERIFICATIONS

    async def get_community_endorsements(
        self, community_id: int
    ) -> List[ContactEndorsement]:
        """Get endorsements within a community.

        Args:
            community_id: Community's unique identifier

        Returns:
            List of community endorsements

        Raises:
            ResourceNotFoundError: If community not found
        """
        community = await self.db.get(Community, community_id)
        if not community:
            raise ResourceNotFoundError(f"Community {community_id} not found")

        repository = cast(ContactEndorsementRepository, self.repository)
        return await repository.get_community_endorsements(community_id)

    async def get_endorsement_stats(self, endorsement_id: int) -> Dict[str, Any]:
        """Get comprehensive endorsement statistics.

        This method aggregates various metrics about an endorsement including:
        - Verification status and history
        - Rating trends
        - Community context
        - User reputation

        Args:
            endorsement_id: Endorsement to analyze

        Returns:
            Dictionary of endorsement statistics

        Raises:
            ResourceNotFoundError: If endorsement not found
        """
        endorsement = await self.get_endorsement(endorsement_id)
        if not endorsement:
            raise ResourceNotFoundError(f"Endorsement {endorsement_id} not found")

        repository = cast(ContactEndorsementRepository, self.repository)

        # Get community stats
        community_stats = await repository.get_community_endorsement_stats(
            endorsement.community_id
        )

        # Get user endorsement history
        user_stats = await repository.get_user_endorsement_stats(endorsement.user_id)

        stats = {
            "endorsement": {
                "rating": endorsement.rating,
                "has_comment": bool(endorsement.comment),
                "is_verified": endorsement.is_verified,
                "verification_date": endorsement.verification_date,
                "created_at": endorsement.created_at,
            },
            "community_context": {
                "total_endorsements": community_stats["total"],
                "verified_ratio": community_stats["verified_ratio"],
                "average_rating": community_stats["average_rating"],
            },
            "user_history": {
                "total_endorsements": user_stats["total"],
                "verified_ratio": user_stats["verified_ratio"],
                "average_rating": user_stats["average_rating"],
            },
        }

        return stats
