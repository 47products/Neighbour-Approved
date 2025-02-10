"""
Rating Module for Endorsement Service

This module provides the RatingMixin class which contains methods for calculating and recalculating
weighted ratings for endorsements. It applies various factors such as time decay, community trust,
and verification impact to produce a normalized rating on a 1.0 to 5.0 scale.

Key functions:
    - calculate_weighted_rating: Compute a weighted rating for an endorsement.
    - recalculate_contact_ratings: Recompute the average rating for a contact based on its endorsements.

Usage example:
    weighted_rating = await rating_mixin.calculate_weighted_rating(endorsement)
"""

from datetime import datetime, UTC
from typing import List
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.db.models.contact_model import Contact
from app.db.models.community_model import Community
from app.services.notification_service import NotificationType
from app.services.service_exceptions import StateError
from typing import cast
from app.db.repositories.contact_endorsement_repository import (
    ContactEndorsementRepository,
)


class RatingMixin:
    """
    Mixin providing rating calculation functionalities for endorsements.

    Methods in this mixin calculate weighted ratings considering factors such as time decay,
    endorser reputation, community trust, and verification impact.
    """

    async def calculate_weighted_rating(self, endorsement: ContactEndorsement) -> float:
        """
        Calculate the weighted rating for an endorsement.

        The calculation incorporates the base rating, time decay with seasonal adjustments,
        endorser reputation, community trust, expertise weight, and verification impact.

        Args:
            endorsement (ContactEndorsement): The endorsement for which to calculate the weighted rating.

        Returns:
            float: The calculated weighted rating, normalized between 1.0 and 5.0.

        Example:
            rating = await rating_mixin.calculate_weighted_rating(endorsement)
        """
        # Base rating (1-5 scale)
        base_rating = endorsement.rating if endorsement.rating else 0.0

        # Calculate time decay factor with seasonal adjustment.
        age_days = (datetime.now(UTC) - endorsement.created_at).days
        seasonal_factor = await self._calculate_seasonal_factor(endorsement.created_at)
        time_factor = max(0.5, (1 - (age_days / 365)) * seasonal_factor)

        # Calculate additional factors.
        endorser_stats = await self._get_endorser_statistics(
            endorsement.user_id
        )  # Implement as needed.
        reputation_score = min(
            1.5, self._calculate_reputation_score(endorser_stats)
        )  # Implement as needed.
        community_factor = await self._get_community_trust_factor(
            endorsement.community_id
        )
        expertise_weight = await self._calculate_expertise_weight(
            endorsement.user_id, endorsement.contact.categories
        )  # Implement as needed.
        verification_factor = self._calculate_verification_impact(endorsement)

        weighted_rating = (
            base_rating
            * time_factor
            * reputation_score
            * community_factor
            * expertise_weight
            * verification_factor
        )

        return round(max(1.0, min(5.0, weighted_rating)), 2)

    async def recalculate_contact_ratings(self, contact_id: int) -> None:
        """
        Recalculate all weighted ratings for a contact.

        This method retrieves all endorsements for the contact, calculates the weighted rating for
        each, and then updates the contact's average rating accordingly. It also triggers a notification
        once the rating has been updated.

        Args:
            contact_id (int): Unique identifier of the contact.

        Raises:
            StateError: If the contact is not found or if the recalculation fails.

        Example:
            await rating_mixin.recalculate_contact_ratings(contact_id)
        """
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise StateError(f"Contact {contact_id} not found")

        repository = cast(ContactEndorsementRepository, self.repository)
        endorsements = await repository.get_contact_endorsements(contact_id)
        weighted_ratings: List[float] = []

        for endorsement in endorsements:
            if endorsement.rating:
                weighted_rating = await self.calculate_weighted_rating(endorsement)
                weighted_ratings.append(weighted_rating)

        if weighted_ratings:
            contact.average_rating = round(
                sum(weighted_ratings) / len(weighted_ratings), 2
            )
            await self.db.commit()

            # Trigger a notification that the rating was updated.
            await self._notification_service.send_notification(
                NotificationType.RATING_UPDATED,
                contact.user_id,
                {
                    "contact_id": contact.id,
                    "new_rating": contact.average_rating,
                    "total_ratings": len(weighted_ratings),
                },
            )

    async def _calculate_seasonal_factor(self, timestamp: datetime) -> float:
        """
        Calculate a seasonal adjustment factor based on the provided timestamp.

        Args:
            timestamp (datetime): The timestamp to evaluate.

        Returns:
            float: The seasonal adjustment factor (default is 1.0 if no specific adjustment applies).
        """
        month = timestamp.month
        seasonal_weights = {
            1: 1.2,
            6: 1.1,
            9: 1.1,
            12: 0.9,
        }
        return seasonal_weights.get(month, 1.0)

    def _calculate_verification_impact(self, endorsement: ContactEndorsement) -> float:
        """
        Calculate the impact of verification status on the weighted rating.

        Args:
            endorsement (ContactEndorsement): The endorsement to evaluate.

        Returns:
            float: The factor by which the verification status modifies the rating.
        """
        base_factor = 1.2 if endorsement.is_verified else 1.0

        if endorsement.verification_notes:
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
        """
        Calculate the trust factor based on community characteristics.

        Args:
            community_id (int): Unique identifier of the community.

        Returns:
            float: The calculated trust factor.
        """
        community = await self.db.get(Community, community_id)
        if not community:
            return 1.0

        verified_ratio = community.verified_endorsements_count / max(
            community.total_endorsements, 1
        )
        return min(1.3, 0.8 + verified_ratio)

    async def _get_endorser_activity_factor(self, user_id: int) -> float:
        """
        Calculate a factor based on the endorser's activity and reliability.

        Args:
            user_id (int): Unique identifier of the endorser.

        Returns:
            float: A factor representing the endorser's activity level.
        """
        repository = cast(ContactEndorsementRepository, self.repository)
        activity_stats = await repository.get_user_activity_stats(user_id)

        activity_score = min(1.0, activity_stats["monthly_endorsements"] / 10)
        reliability_score = activity_stats["verification_success_rate"]

        return min(1.2, 0.8 + (activity_score * reliability_score))
