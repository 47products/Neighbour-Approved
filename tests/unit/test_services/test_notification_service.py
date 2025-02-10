"""
Unit tests for the notification service module.

This module tests:
- The NotificationType enum, NotificationPreference, and NotificationEvent dataclasses.
- The NotificationService methods:
    - send_notification (a placeholder implementation).
    - _get_notification_preferences (which returns default values).
    - _send_endorsement_notifications (which sends owner notifications and, if applicable, moderator notifications).

The tests use shared fixtures (e.g. `dummy_community`) defined in conftest.py.
Additional dummy classes/fixtures are defined here to simulate logging, notification sending,
and endorsement-related objects.

Usage:
    $ pytest test_notification_service.py
"""

import datetime
import pytest
from app.services.notification_service import (
    NotificationType,
    NotificationPreference,
    NotificationEvent,
    NotificationService,
)


class DummyLogger:
    """
    A dummy logger that provides a debug method.

    This is used to avoid attribute errors when the service logs debug messages.
    """

    def debug(self, *args, **kwargs):
        # This method is intentionally left blank because logging is not required in tests.
        pass


class DummyNotificationSender:
    """
    Dummy notification sender to capture calls to send_notification.

    Attributes:
        calls (list): A list of tuples (notification_type, user_id, data) for each call.
    """

    def __init__(self):
        self.calls = []

    async def send_notification(self, notification_type, user_id, data):
        self.calls.append((notification_type, user_id, data))


@pytest.fixture
def dummy_notification_sender():
    """
    Fixture that returns an instance of DummyNotificationSender.

    This is used to capture calls made by the NotificationService.
    """
    return DummyNotificationSender()


# Dummy classes for endorsement notification testing.
# We create minimal dummy objects with the attributes required by NotificationService.
class DummyUser:
    """Simulates a user with first and last names."""

    def __init__(self, first_name: str, last_name: str):
        self.first_name = first_name
        self.last_name = last_name


class DummyContact:
    """Simulates a contact with a user_id and a contact name."""

    def __init__(self, user_id: int, contact_name: str):
        self.user_id = user_id
        self.contact_name = contact_name


# For the community, we reuse the dummy_community fixture defined in conftest.
# In our tests, we will instantiate it to simulate a community.


class DummyEndorsement:
    """
    Simulates an endorsement object with the attributes required for sending notifications.

    Attributes:
        id (int): Endorsement ID.
        contact (DummyContact): Contact receiving the endorsement.
        user (DummyUser): User who made the endorsement.
        community: Community object (must have a 'name' attribute).
        rating: Rating value.
        comment: Comment text.
        community_id (int): ID of the community.
    """

    def __init__(self, id, contact, user, community, rating, comment, community_id):
        self.id = id
        self.contact = contact
        self.user = user
        self.community = community
        self.rating = rating
        self.comment = comment
        self.community_id = community_id


# -----------------------------------------------------------------------------
# Tests for data structures and enums
# -----------------------------------------------------------------------------


def test_notification_type_enum():
    """
    Test that the NotificationType enum contains the expected values.
    """
    assert NotificationType.ENDORSEMENT_RECEIVED.value == "endorsement_received"
    assert NotificationType.ENDORSEMENT_VERIFIED.value == "endorsement_verified"
    assert NotificationType.VERIFICATION_REQUESTED.value == "verification_requested"
    assert NotificationType.RATING_UPDATED.value == "rating_updated"


def test_notification_preference_defaults():
    """
    Test that NotificationPreference initializes with default notification settings.
    """
    pref = NotificationPreference(user_id=42)
    assert pref.user_id == 42
    assert pref.verification_notifications is True
    assert pref.rating_notifications is True
    assert pref.endorsement_notifications is True


def test_notification_event_fields():
    """
    Test that NotificationEvent correctly stores event data.
    """
    now = datetime.datetime.now()
    event = NotificationEvent(
        event_type=NotificationType.RATING_UPDATED,
        timestamp=now,
        recipient_id=10,
        sender_id=5,
        data={"new_rating": 4.5},
        metadata={"source": "test"},
    )
    assert event.event_type == NotificationType.RATING_UPDATED
    assert event.timestamp == now
    assert event.recipient_id == 10
    assert event.sender_id == 5
    assert event.data == {"new_rating": 4.5}
    assert event.metadata == {"source": "test"}


# -----------------------------------------------------------------------------
# Tests for NotificationService methods
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_notification_placeholder():
    """
    Test that the placeholder send_notification method completes without error.

    The current implementation does nothing and returns None.
    """
    service = NotificationService()
    result = await service.send_notification(
        NotificationType.RATING_UPDATED, 1, {"new_rating": 4.5}
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_notification_preferences():
    """
    Test that _get_notification_preferences returns default preferences.

    The method should return a dictionary with the user_id and default boolean values.
    """
    service = NotificationService()
    # Set a dummy logger to avoid attribute errors.
    service._logger = DummyLogger()
    prefs = await service._get_notification_preferences(100)
    assert prefs["user_id"] == 100
    assert prefs["verification_notifications"] is True
    assert prefs["rating_notifications"] is True
    assert prefs["endorsement_notifications"] is True


@pytest.mark.asyncio
async def test_send_endorsement_notifications_with_comment(
    dummy_community, dummy_notification_sender
):
    """
    Test that _send_endorsement_notifications sends both the owner notification and moderator notifications
    when the endorsement has both a rating and a nonempty comment.

    The owner notification should be sent with type ENDORSEMENT_RECEIVED, and moderator notifications
    with type VERIFICATION_REQUESTED.
    """
    service = NotificationService()
    service._logger = DummyLogger()
    # Inject the dummy notification sender.
    service._notification_service = dummy_notification_sender

    # Override _get_community_moderators to simulate returning moderator IDs.
    async def fake_get_community_moderators(community_id):
        return [200, 201]

    service._get_community_moderators = fake_get_community_moderators

    # Create dummy endorsement objects.
    endorser = DummyUser("John", "Doe")
    contact = DummyContact(user_id=10, contact_name="Jane Smith")
    # Use the dummy_community fixture to create a community instance.
    community_cls = dummy_community  # dummy_community is a fixture returning a class.
    community_instance = community_cls(active=True)
    community_instance.name = "Test Community"

    endorsement = DummyEndorsement(
        id=123,
        contact=contact,
        user=endorser,
        community=community_instance,
        rating=4.2,
        comment="Excellent work!",
        community_id=999,
    )

    await service._send_endorsement_notifications(endorsement)
    # Expect one notification for the owner and one for each moderator (total 1 + 2 = 3).
    assert len(dummy_notification_sender.calls) == 3

    # Verify owner notification details.
    owner_notification = dummy_notification_sender.calls[0]
    assert owner_notification[0] == NotificationType.ENDORSEMENT_RECEIVED
    assert owner_notification[1] == contact.user_id
    data = owner_notification[2]
    assert data["endorsement_id"] == endorsement.id
    expected_endorser_name = f"{endorser.first_name} {endorser.last_name}"
    assert data["endorser_name"] == expected_endorser_name
    assert data["contact_name"] == contact.contact_name
    assert data["community_name"] == community_instance.name
    assert data["rating"] == endorsement.rating
    assert data["has_comment"] is True

    # Verify moderator notifications.
    for notif in dummy_notification_sender.calls[1:]:
        assert notif[0] == NotificationType.VERIFICATION_REQUESTED
        assert notif[1] in [200, 201]
        mod_data = notif[2]
        assert mod_data["endorsement_id"] == endorsement.id
        assert mod_data["contact_name"] == contact.contact_name
        assert mod_data["community_name"] == community_instance.name


@pytest.mark.asyncio
async def test_send_endorsement_notifications_without_comment(
    dummy_community, dummy_notification_sender
):
    """
    Test that _send_endorsement_notifications sends only the owner notification
    when the endorsement's comment is empty.

    In this scenario, no moderator notifications should be sent.
    """
    service = NotificationService()
    service._logger = DummyLogger()
    service._notification_service = dummy_notification_sender

    async def fake_get_community_moderators(community_id):
        return [200, 201]

    service._get_community_moderators = fake_get_community_moderators

    endorser = DummyUser("Alice", "Smith")
    contact = DummyContact(user_id=20, contact_name="Bob Johnson")
    community_cls = dummy_community
    community_instance = community_cls(active=True)
    community_instance.name = "Example Community"

    endorsement = DummyEndorsement(
        id=456,
        contact=contact,
        user=endorser,
        community=community_instance,
        rating=3.8,
        comment="",  # Empty comment
        community_id=888,
    )

    await service._send_endorsement_notifications(endorsement)
    # Only the owner notification should be sent.
    assert len(dummy_notification_sender.calls) == 1

    owner_notification = dummy_notification_sender.calls[0]
    assert owner_notification[0] == NotificationType.ENDORSEMENT_RECEIVED
    assert owner_notification[1] == contact.user_id
    data = owner_notification[2]
    assert data["endorsement_id"] == endorsement.id
    expected_endorser_name = f"{endorser.first_name} {endorser.last_name}"
    assert data["endorser_name"] == expected_endorser_name
    assert data["contact_name"] == contact.contact_name
    assert data["community_name"] == community_instance.name
    assert data["rating"] == endorsement.rating
    assert data["has_comment"] is False
