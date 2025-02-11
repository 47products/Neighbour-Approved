"""
Main Endorsement Service Module.

This module implements the core EndorsementService class that handles endorsement-related operations
for contacts. It provides functionality for creating endorsements, updating contact metrics, and integrates
mixins for rating calculations, verification workflows, and notifications.

Key classes:
    - EndorsementService: Orchestrates endorsement business logic including creation, metrics update,
      and integration of rating, verification, and notification functionalities.

Usage example:
    from endorsement_service import EndorsementService
    service = EndorsementService(db_session)
    endorsement = await service.create_endorsement(data)
"""

from typing import cast
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.services.notification_service import NotificationService
from app.services.service_interfaces import IEndorsementService
from app.services.service_exceptions import (
    ValidationError,
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

# Import mixins from the helper modules
from .endorsement_service_rating import RatingMixin
from .endorsement_service_verification import VerificationMixin
from .endorsement_service_notifications import NotificationMixin


class EndorsementService(
    BaseService[
        ContactEndorsement,  # Model type
        ContactEndorsementCreate,  # Create schema type
        ContactEndorsementUpdate,  # Update schema type
        ContactEndorsement,  # Read schema type (using ContactEndorsement as a placeholder)
    ],
    IEndorsementService,
    RatingMixin,
    VerificationMixin,
    NotificationMixin,
):
    """
    Service for managing endorsement-related operations and business logic.

    This class implements core operations such as creating endorsements, validating data,
    and updating contact metrics. It also incorporates additional functionalities via mixins
    for rating calculations, verification workflows, and notification dispatch.

    Attributes:
        MIN_RATING (int): Minimum allowed rating value.
        MAX_RATING (int): Maximum allowed rating value.
        MIN_COMMENT_LENGTH (int): Minimum required length for endorsement comments.
        MAX_PENDING_VERIFICATIONS (int): Maximum pending verifications allowed per contact.
        db (Session): Database session for repository operations.
        _notification_service (NotificationService): Service for sending notifications.
    """

    MIN_RATING = 1
    MAX_RATING = 5
    MIN_COMMENT_LENGTH = 10
    MAX_PENDING_VERIFICATIONS = 5

    def __init__(self, db: Session):
        """
        Initialize the EndorsementService.

        Args:
            db (Session): Database session for repository operations.
        """
        super().__init__(
            model=ContactEndorsement,
            repository=ContactEndorsementRepository(db),
            logger_name="EndorsementService",
        )
        self._notification_service = NotificationService()
        # Instead of assigning to the read-only property "db", set the underlying attribute.
        object.__setattr__(self, "_db", db)

    async def create_endorsement(
        self, data: ContactEndorsementCreate
    ) -> ContactEndorsement:
        """
        Create a new endorsement with full validation and metrics update.

        This method validates the provided data, creates the endorsement, and updates the
        corresponding contact's metrics. It also logs the creation event.

        Args:
            data (ContactEndorsementCreate): Validated endorsement creation data.
                - contact_id: Unique identifier of the contact being endorsed.
                - community_id: Unique identifier of the community.
                - user_id: Unique identifier of the endorsing user.
                - rating: Optional numeric rating.
                - comment: Optional textual comment.

        Returns:
            ContactEndorsement: The newly created endorsement instance.

        Raises:
            ValidationError: If the input data fails validation.
            DuplicateResourceError: If an endorsement already exists.
            StateError: If updating contact metrics fails.

        Example:
            endorsement = await service.create_endorsement(endorsement_data)
        """
        try:
            # Validate creation data
            await self._validate_endorsement_creation(data)

            # Create the endorsement using the inherited create method.
            endorsement = await self.create(data)

            # Update contact metrics based on the new endorsement.
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
        """
        Validate endorsement creation data against business rules.

        The validation includes checks for the existence and status of the contact and community,
        rating range, comment length, and duplicate endorsements.

        Args:
            data (ContactEndorsementCreate): Endorsement creation data.

        Raises:
            ValidationError: If the contact or community is not found or inactive, if the rating
                is outside the allowed range, or if the comment is too short.
            DuplicateResourceError: If the user has already endorsed this contact in the community.
        """
        # Validate that the contact exists and is active.
        contact = await self.db.get(Contact, data.contact_id)
        community = await self.db.get(Community, data.community_id)

        if not contact or not contact.is_active:
            raise ValidationError(f"Contact {data.contact_id} not found or inactive")

        if not community or not community.is_active:
            raise ValidationError(
                f"Community {data.community_id} not found or inactive"
            )

        # Validate the rating range if provided.
        if (
            data.rating is not None
            and not self.MIN_RATING <= data.rating <= self.MAX_RATING
        ):
            raise ValidationError(
                f"Rating must be between {self.MIN_RATING} and {self.MAX_RATING}"
            )

        # Validate the comment length if provided.
        if data.comment and len(data.comment) < self.MIN_COMMENT_LENGTH:
            raise ValidationError(
                f"Comment must be at least {self.MIN_COMMENT_LENGTH} characters"
            )

        # Check for an existing endorsement to avoid duplicates.
        from typing import cast

        repository = cast(ContactEndorsementRepository, self.repository)
        existing = await repository.get_user_endorsement(
            data.user_id, data.contact_id, data.community_id
        )
        if existing:
            raise DuplicateResourceError(
                "User has already endorsed this contact in this community"
            )

    async def _update_contact_metrics(self, contact_id: int) -> None:
        """
        Update endorsement-related metrics for a contact.

        This method recalculates metrics such as the total number of endorsements, verified
        endorsements, and average rating, then updates the contact record accordingly.

        Args:
            contact_id (int): Unique identifier of the contact to update.

        Raises:
            ResourceNotFoundError: If the contact is not found.
            StateError: If the update process fails.
        """
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            from app.services.service_exceptions import ResourceNotFoundError

            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        try:
            # Retrieve all endorsements for the contact.
            from typing import cast

            repository = cast(ContactEndorsementRepository, self.repository)
            endorsements = await repository.get_contact_endorsements(contact_id)

            total_count = len(endorsements)
            verified_count = sum(1 for e in endorsements if e.is_verified)

            # Calculate the average rating based on verified endorsements.
            rated_endorsements = [
                e.rating for e in endorsements if e.is_verified and e.rating is not None
            ]
            average_rating = (
                (sum(rated_endorsements) / len(rated_endorsements))
                if rated_endorsements
                else None
            )

            # Update the contact record with new metrics.
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
                "contact_metrics_update_failed", contact_id=contact_id, error=str(e)
            )
            from app.services.service_exceptions import StateError

            raise StateError(f"Failed to update contact metrics: {str(e)}")
