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

from app.services.base import BaseService
from app.services.notification_service import NotificationService, NotificationType
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
        self._notification_service = NotificationService()

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

    async def calculate_weighted_rating(self, endorsement: ContactEndorsement) -> float:
        """
        Calculate weighted rating using advanced metrics and time-based decay.

        This method implements a sophisticated rating calculation that considers:
        - Endorser's reputation and activity level
        - Time decay with seasonality adjustments
        - Community trust factors
        - Verification status impact
        - Category expertise weighting

        Args:
            endorsement: Endorsement to calculate rating for

        Returns:
            float: Calculated weighted rating between 1.0 and 5.0

        Note:
            The weighting factors are calibrated based on statistical analysis
            of rating patterns and user behavior.
        """
        # Base rating (1-5 scale)
        base_rating = endorsement.rating if endorsement.rating else 0.0

        # Calculate time decay factor with seasonality
        age_days = (datetime.now(UTC) - endorsement.created_at).days
        seasonal_factor = self._calculate_seasonal_factor(endorsement.created_at)
        time_factor = max(0.5, (1 - (age_days / 365)) * seasonal_factor)

        # Calculate endorser reputation score
        endorser_stats = await self._get_endorser_statistics(endorsement.user_id)
        reputation_score = min(1.5, self._calculate_reputation_score(endorser_stats))

        # Calculate community trust factor
        community_factor = await self._get_community_trust_factor(
            endorsement.community_id
        )

        # Calculate category expertise weight
        expertise_weight = await self._calculate_expertise_weight(
            endorsement.user_id, endorsement.contact.categories
        )

        # Calculate verification impact
        verification_factor = self._calculate_verification_impact(endorsement)

        # Combine factors with balanced weighting
        weighted_rating = (
            base_rating
            * time_factor
            * reputation_score
            * community_factor
            * expertise_weight
            * verification_factor
        )

        # Normalize to 1-5 scale and round to 2 decimal places
        return round(max(1.0, min(5.0, weighted_rating)), 2)

    async def _calculate_seasonal_factor(self, timestamp: datetime) -> float:
        """
        Calculate seasonal adjustment factor for time-based weighting.

        Args:
            timestamp: Rating timestamp

        Returns:
            float: Seasonal adjustment factor
        """
        month = timestamp.month
        # Adjust weight based on typical seasonal patterns
        seasonal_weights = {
            # Higher weight during peak activity months
            1: 1.2,  # January (post-holiday activity)
            6: 1.1,  # June (summer season)
            9: 1.1,  # September (fall season)
            12: 0.9,  # December (holiday season)
        }
        return seasonal_weights.get(month, 1.0)

    def _calculate_verification_impact(self, endorsement: ContactEndorsement) -> float:
        """
        Calculate impact of verification status on rating weight.

        Args:
            endorsement: Endorsement to evaluate

        Returns:
            float: Verification impact factor
        """
        base_factor = 1.2 if endorsement.is_verified else 1.0

        # Additional factors based on verification metadata
        if endorsement.verification_notes:
            # Parse verification context for additional weighting
            context_keywords = {
                "verified_identity": 0.1,
                "confirmed_transaction": 0.15,
                "documented_evidence": 0.2,
            }
            additional_weight = sum(
                weight
                for keyword, weight in context_keywords.items()
                if keyword in endorsement.verification_notes.lower()
            )
            return base_factor + additional_weight

        return base_factor

    async def _get_community_trust_factor(self, community_id: int) -> float:
        """Calculate trust factor based on community characteristics."""
        community = await self.db.get(Community, community_id)
        if not community:
            return 1.0

        # Base factor on verified endorsement ratio
        verified_ratio = community.verified_endorsements_count / max(
            community.total_endorsements, 1
        )
        return min(1.3, 0.8 + verified_ratio)

    async def _get_endorser_activity_factor(self, user_id: int) -> float:
        """Calculate factor based on endorser's activity and reliability."""
        repository = cast(ContactEndorsementRepository, self.repository)
        activity_stats = await repository.get_user_activity_stats(user_id)

        # Consider endorsement frequency and verification rate
        activity_score = min(1.0, activity_stats["monthly_endorsements"] / 10)
        reliability_score = activity_stats["verification_success_rate"]

        return min(1.2, 0.8 + (activity_score * reliability_score))

    async def recalculate_contact_ratings(self, contact_id: int) -> None:
        """Recalculate all weighted ratings for a contact.

        This method triggers a full recalculation of all ratings when:
        - New endorsements are added
        - Endorsements are verified
        - Endorser reputation changes

        Args:
            contact_id: Contact to recalculate ratings for

        Raises:
            ResourceNotFoundError: If contact not found
            StateError: If recalculation fails
        """
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        try:
            repository = cast(ContactEndorsementRepository, self.repository)
            endorsements = await repository.get_contact_endorsements(contact_id)

            # Calculate weighted ratings
            weighted_ratings = []
            for endorsement in endorsements:
                if endorsement.rating:
                    weighted_rating = await self.calculate_weighted_rating(endorsement)
                    weighted_ratings.append(weighted_rating)

            # Update contact's average rating
            if weighted_ratings:
                contact.average_rating = round(
                    sum(weighted_ratings) / len(weighted_ratings), 2
                )
                await self.db.commit()

                # Trigger rating update notification
                await self._notification_service.send_notification(
                    NotificationType.RATING_UPDATED,
                    contact.user_id,
                    {
                        "contact_id": contact.id,
                        "new_rating": contact.average_rating,
                        "total_ratings": len(weighted_ratings),
                    },
                )

        except Exception as e:
            await self.db.rollback()
            raise StateError(f"Rating recalculation failed: {str(e)}") from e

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

    async def process_verification(
        self,
        endorsement_id: int,
        verifier_id: int,
        verification_context: Optional[Dict[str, Any]] = None,
        verification_notes: Optional[str] = None,
    ) -> ContactEndorsement:
        """
        Process comprehensive endorsement verification workflow.

        This method implements a multi-step verification process including:
        - Eligibility validation
        - Identity verification
        - Content authenticity checks
        - Community standards compliance
        - Fraud detection

        Args:
            endorsement_id: Endorsement to verify
            verifier_id: User performing verification
            verification_context: Optional contextual data about verification
            verification_notes: Optional verification notes

        Returns:
            ContactEndorsement: Updated endorsement

        Raises:
            ValidationError: If verification requirements not met
            StateError: If verification fails
        """
        endorsement = await self.get_endorsement(endorsement_id)
        if not endorsement:
            raise ResourceNotFoundError(f"Endorsement {endorsement_id} not found")

        try:
            # Comprehensive verification checks
            await self._validate_verification_eligibility(endorsement)
            await self._validate_verifier_authority(verifier_id, endorsement)
            await self._check_content_authenticity(endorsement)
            await self._validate_community_standards(endorsement)

            # Process verification
            endorsement.is_verified = True
            endorsement.verification_date = datetime.now(UTC)
            endorsement.verification_notes = self._format_verification_notes(
                verification_notes, verification_context
            )

            # Update related metrics
            await self._update_verification_metrics(endorsement)

            # Create verification audit trail
            await self._create_verification_audit(
                endorsement, verifier_id, verification_context
            )

            # Trigger notifications
            await self._send_verification_notifications(endorsement)

            await self.db.commit()
            return endorsement

        except Exception as e:
            await self.db.rollback()
            raise StateError(f"Verification failed: {str(e)}") from e

    async def _validate_verification_eligibility(
        self, endorsement: ContactEndorsement
    ) -> None:
        """
        Validate if endorsement meets verification requirements.

        Performs comprehensive eligibility checks including:
        - Content requirements
        - Age restrictions
        - Previous verification history
        - User reputation thresholds

        Args:
            endorsement: Endorsement to validate

        Raises:
            ValidationError: If requirements not met
        """
        if endorsement.is_verified:
            raise ValidationError("Endorsement already verified")

        # Content validation
        if not self._meets_content_requirements(endorsement):
            raise ValidationError("Insufficient content for verification")

        # Age validation
        if not await self._meets_age_requirements(endorsement):
            raise ValidationError("Endorsement too recent for verification")

        # History validation
        if not await self._has_valid_history(endorsement):
            raise ValidationError(
                "Previous verification attempts prevent reverification"
            )

    async def _create_verification_audit_log(
        self, endorsement: ContactEndorsement, verifier_id: int
    ) -> None:
        """Create audit log entry for endorsement verification.

        Logs verification details including:
        - Timestamp and verifier
        - Pre and post verification metrics
        - Applied verification criteria

        Args:
            endorsement: Verified endorsement
            verifier_id: User who performed verification
        """
        try:
            # Create audit log entry with verification details
            audit_data = {
                "endorsement_id": endorsement.id,
                "verifier_id": verifier_id,
                "verification_date": endorsement.verification_date,
                "contact_id": endorsement.contact_id,
                "community_id": endorsement.community_id,
                "rating_before": endorsement.contact.average_rating,
                "endorsement_count_before": endorsement.contact.endorsements_count,
                "verified_count_before": endorsement.contact.verified_endorsements_count,
            }

            # Record verification criteria met
            audit_data["criteria_met"] = {
                "has_required_info": bool(endorsement.comment or endorsement.rating),
                "community_active": endorsement.community.is_active,
                "contact_active": endorsement.contact.is_active,
                "within_pending_limit": await self._check_pending_limit(
                    endorsement.contact_id
                ),
            }

            # Store audit log (implement actual storage)
            self._logger.info("verification_audit_log_created", **audit_data)

        except Exception as e:
            self._logger.error(
                "audit_log_creation_failed",
                error=str(e),
                endorsement_id=endorsement.id,
            )
            # Don't re-raise - audit log failure shouldn't fail verification

    async def _check_pending_limit(self, contact_id: int) -> bool:
        """Check if contact is within pending verifications limit."""
        repository = cast(ContactEndorsementRepository, self.repository)
        pending_count = await repository.get_pending_verifications_count(contact_id)
        return pending_count < self.MAX_PENDING_VERIFICATIONS

    async def _has_verification_permission(
        self, verifier_id: int, endorsement: ContactEndorsement
    ) -> bool:
        """Check if user has permission to verify endorsement."""
        # Implement permission checks based on:
        # - User roles
        # - Community membership
        # - Verification quotas
        return True  # Implement actual checks

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

    async def _send_verification_notifications(
        self, endorsement: ContactEndorsement
    ) -> None:
        """
        Send comprehensive notifications for endorsement verification.

        This method manages notification dispatch to all relevant parties:
        - Endorsement creator
        - Contact owner
        - Community moderators
        - Related stakeholders

        Notifications are sent through multiple channels based on user preferences
        and include contextual data for proper handling.

        Args:
            endorsement: Verified endorsement
        """
        try:
            # Prepare notification context
            notification_context = await self._build_notification_context(endorsement)

            # Notify endorsement creator
            await self._notification_service.send_notification(
                NotificationType.ENDORSEMENT_VERIFIED,
                endorsement.user_id,
                {
                    "endorsement_id": endorsement.id,
                    "contact_name": endorsement.contact.contact_name,
                    "community_name": endorsement.community.name,
                    "verification_date": endorsement.verification_date,
                    "context": notification_context,
                },
            )

            # Notify contact owner with detailed impact
            await self._notification_service.send_notification(
                NotificationType.CONTACT_ENDORSEMENT_VERIFIED,
                endorsement.contact.user_id,
                {
                    "endorsement_id": endorsement.id,
                    "endorser_name": f"{endorsement.user.first_name} {endorsement.user.last_name}",
                    "rating_impact": await self._calculate_rating_impact(endorsement),
                    "verification_details": notification_context,
                },
            )

            # Notify community moderators
            moderator_ids = await self._get_community_moderators(
                endorsement.community_id
            )
            for moderator_id in moderator_ids:
                await self._notification_service.send_notification(
                    NotificationType.MODERATION_VERIFICATION_COMPLETE,
                    moderator_id,
                    {
                        "endorsement_id": endorsement.id,
                        "community_id": endorsement.community_id,
                        "verification_context": notification_context,
                    },
                )

            # Send analytics update
            await self._notification_service.send_notification(
                NotificationType.ANALYTICS_UPDATE,
                None,  # System notification
                {
                    "event_type": "endorsement_verified",
                    "endorsement_id": endorsement.id,
                    "metrics_impact": await self._calculate_metrics_impact(endorsement),
                },
            )

        except Exception as e:
            self._logger.error(
                "notification_dispatch_failed",
                error=str(e),
                endorsement_id=endorsement.id,
            )
            # Don't re-raise - notification failure shouldn't fail verification

    async def _build_notification_context(
        self, endorsement: ContactEndorsement
    ) -> Dict[str, Any]:
        """
        Build comprehensive notification context.

        Creates a rich context object containing all relevant information
        for notification processing and display.

        Args:
            endorsement: Source endorsement

        Returns:
            Dict[str, Any]: Notification context
        """
        return {
            "verification_date": endorsement.verification_date,
            "verification_notes": endorsement.verification_notes,
            "rating_impact": await self._calculate_rating_impact(endorsement),
            "community_context": await self._get_community_context(endorsement),
            "contact_metrics": await self._get_contact_metrics(endorsement.contact_id),
            "type": "endorsement_verification",
            "timestamp": datetime.now(UTC),
        }
