"""
Notifications Module for Endorsement Service

This module provides the NotificationMixin class which contains methods for sending notifications
related to endorsement verification events. It integrates with the NotificationService to dispatch
notifications to relevant parties including endorsement creators, contact owners, and moderators.

Key functions:
    - _send_verification_notifications: Dispatch notifications after an endorsement is verified.
    - _build_notification_context: Construct a context dictionary for notifications.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from app.services.notification_service import NotificationType
from app.db.models.contact_endorsement_model import ContactEndorsement


class NotificationMixin:
    """
    Mixin providing notification functionalities for endorsement verification events.

    This mixin includes helper methods to build notification contexts and dispatch notifications
    to various stakeholders.
    """

    async def _send_verification_notifications(
        self, endorsement: ContactEndorsement
    ) -> None:
        """
        Send notifications after an endorsement is verified.

        This method dispatches notifications to the endorsement creator and the contact owner.
        It utilizes the NotificationService to send notifications with contextual information.

        Args:
            endorsement (ContactEndorsement): The verified endorsement.
        """
        try:
            # Build the notification context.
            context = await self._build_notification_context(endorsement)

            # Notify the endorsement creator.
            await self._notification_service.send_notification(
                NotificationType.ENDORSEMENT_VERIFIED,
                endorsement.user_id,
                context,
                endorsement.id,
            )

            # Notify the contact owner if available.
            if endorsement.contact and getattr(endorsement.contact, "user_id", None):
                await self._notification_service.send_notification(
                    NotificationType.CONTACT_ENDORSEMENT_VERIFIED,
                    endorsement.contact.user_id,
                    context,
                    endorsement.id,
                )

        except Exception as e:
            # Log the error and swallow the exception.
            self._logger.error(
                "notification_dispatch_failed",
                error=str(e),
                endorsement_id=endorsement.id,
            )

    async def _build_notification_context(
        self, endorsement: ContactEndorsement
    ) -> Dict[str, Any]:
        """
        Build a comprehensive notification context for an endorsement.

        This context includes details such as the verification date, notes, rating impact,
        and other relevant metadata to be included in notifications.

        Args:
            endorsement (ContactEndorsement): The endorsement used as the notification source.

        Returns:
            Dict[str, Any]: A dictionary containing notification context data.
        """
        return {
            "verification_date": endorsement.verification_date,
            "verification_notes": endorsement.verification_notes,
            "rating_impact": await self._calculate_rating_impact(
                endorsement
            ),  # Implement as needed.
            "timestamp": datetime.now(timezone.utc),
            "type": "endorsement_verification",
        }
