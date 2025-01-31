from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from app.db.models.contact_endorsement_model import ContactEndorsement


class NotificationType(Enum):
    """Enumeration of notification types."""

    ENDORSEMENT_RECEIVED = "endorsement_received"
    ENDORSEMENT_VERIFIED = "endorsement_verified"
    VERIFICATION_REQUESTED = "verification_requested"
    RATING_UPDATED = "rating_updated"


@dataclass
class NotificationPreference:
    """User notification preferences."""

    user_id: int
    verification_notifications: bool = True
    rating_notifications: bool = True
    endorsement_notifications: bool = True


@dataclass
class NotificationEvent:
    """Structured notification event data."""

    event_type: NotificationType
    timestamp: datetime
    recipient_id: int
    sender_id: Optional[int]
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class NotificationService:
    """Service for handling system notifications."""

    async def send_notification(
        self, notification_type: NotificationType, user_id: int, data: Dict[str, Any]
    ) -> None:
        """Send notification to user."""
        # Implement actual notification sending

    async def _get_notification_preferences(self, user_id: int) -> Dict[str, bool]:
        """Get user's notification preferences.

        Args:
            user_id: User to get preferences for

        Returns:
            Dictionary of notification preferences

        Note:
            Currently returns default preferences. In a real implementation,
            this would fetch user-specific preferences from a database.
        """
        self._logger.debug(
            "fetching_notification_preferences",
            user_id=user_id,
            source="default_configuration",  # Indicates using default values
        )

        # Temporary implementation - would normally fetch from database
        return {
            "user_id": user_id,  # Include user_id to maintain traceability
            "verification_notifications": True,
            "rating_notifications": True,
            "endorsement_notifications": True,
        }

    async def _send_endorsement_notifications(
        self, endorsement: ContactEndorsement
    ) -> None:
        """Send notifications for new endorsement creation.

        Args:
            endorsement: Newly created endorsement
        """
        # Notify contact owner
        await self._notification_service.send_notification(
            NotificationType.ENDORSEMENT_RECEIVED,
            endorsement.contact.user_id,
            {
                "endorsement_id": endorsement.id,
                "endorser_name": f"{endorsement.user.first_name} {endorsement.user.last_name}",
                "contact_name": endorsement.contact.contact_name,
                "community_name": endorsement.community.name,
                "rating": endorsement.rating,
                "has_comment": bool(endorsement.comment),
            },
        )

        # Request verification if needed
        if endorsement.rating and endorsement.comment:
            for moderator_id in await self._get_community_moderators(
                endorsement.community_id
            ):
                await self._notification_service.send_notification(
                    NotificationType.VERIFICATION_REQUESTED,
                    moderator_id,
                    {
                        "endorsement_id": endorsement.id,
                        "contact_name": endorsement.contact.contact_name,
                        "community_name": endorsement.community.name,
                    },
                )
