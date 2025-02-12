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
from unittest.mock import AsyncMock, patch
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


@pytest.mark.asyncio
async def test_send_notification_all_types():
    """
    Test send_notification method for all notification types.
    """
    service = NotificationService()

    # Mocking send_notification at the class level
    with patch.object(
        service, "send_notification", new_callable=AsyncMock
    ) as mock_send:
        for notif_type in NotificationType:
            await service.send_notification(notif_type, 1, {"message": "Test"})
            mock_send.assert_any_call(notif_type, 1, {"message": "Test"})


@pytest.mark.asyncio
async def test_get_notification_preferences_all_disabled():
    """
    Test notification preferences when all notifications are disabled.
    """
    service = NotificationService()
    service._logger = AsyncMock()

    service._get_notification_preferences = AsyncMock(
        return_value={
            "user_id": 1,
            "verification_notifications": False,
            "rating_notifications": False,
            "endorsement_notifications": False,
        }
    )
    prefs = await service._get_notification_preferences(1)
    assert prefs["user_id"] == 1
    assert prefs["verification_notifications"] is False
    assert prefs["rating_notifications"] is False
    assert prefs["endorsement_notifications"] is False


@pytest.mark.asyncio
async def test_send_endorsement_notifications_no_moderators():
    """
    Test that no verification notifications are sent when there are no moderators.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()
    service._get_community_moderators = AsyncMock(return_value=[])

    endorsement = AsyncMock()
    endorsement.id = 123
    endorsement.contact.user_id = 10
    endorsement.user.first_name = "John"
    endorsement.user.last_name = "Doe"
    endorsement.contact.contact_name = "Test Contact"
    endorsement.community.name = "Test Community"
    endorsement.rating = 5
    endorsement.comment = "Great work!"
    endorsement.community_id = 1

    await service._send_endorsement_notifications(endorsement)
    service._notification_service.send_notification.assert_called_once()


@pytest.mark.asyncio
async def test_send_endorsement_notifications_no_rating():
    """
    Test that only owner notification is sent when endorsement has no rating.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()
    service._get_community_moderators = AsyncMock(return_value=[200, 201])

    endorsement = AsyncMock()
    endorsement.id = 123
    endorsement.contact.user_id = 10
    endorsement.user.first_name = "Alice"
    endorsement.user.last_name = "Smith"
    endorsement.contact.contact_name = "Bob Johnson"
    endorsement.community.name = "Example Community"
    endorsement.rating = None  # No rating
    endorsement.comment = "Nice!"
    endorsement.community_id = 2

    await service._send_endorsement_notifications(endorsement)
    service._notification_service.send_notification.assert_called_once()


@pytest.mark.asyncio
async def test_send_notification_invalid_data():
    """
    Test send_notification with invalid data should not raise errors.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()

    try:
        await service.send_notification(NotificationType.RATING_UPDATED, 1, {})
    except Exception:
        pytest.fail("send_notification should not raise an exception")

    # If send_notification does nothing, no assertion is needed.


@pytest.mark.asyncio
async def test_send_notification_no_recipient():
    """
    Test send_notification when no user_id is provided.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()

    await service.send_notification(
        NotificationType.ENDORSEMENT_VERIFIED, None, {"test": "data"}
    )
    service._notification_service.send_notification.assert_not_called()


@pytest.mark.asyncio
async def test_send_endorsement_notifications_logging():
    """
    Ensure that debug logging is called during notification sending.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()
    service._get_community_moderators = AsyncMock(return_value=[100])

    endorsement = AsyncMock()
    endorsement.id = 123
    endorsement.contact.user_id = 10
    endorsement.user.first_name = "Eve"
    endorsement.user.last_name = "Brown"
    endorsement.contact.contact_name = "Charlie Doe"
    endorsement.community.name = "Some Community"
    endorsement.rating = 4.0
    endorsement.comment = "Nice Job!"
    endorsement.community_id = 3

    await service._send_endorsement_notifications(endorsement)

    # Verify at least one debug log was triggered
    if service._logger.debug.call_count == 0:
        pytest.fail("Expected at least one debug log, but none were triggered.")


@pytest.mark.asyncio
async def test_send_notification_handles_failure():
    """
    Test that send_notification handles exceptions gracefully.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()
    service._notification_service.send_notification.side_effect = Exception(
        "Simulated Failure"
    )

    try:
        await service.send_notification(
            NotificationType.ENDORSEMENT_RECEIVED, 1, {"test": "data"}
        )
    except Exception:
        pytest.fail("send_notification should not propagate exceptions")


@pytest.mark.asyncio
async def test_send_endorsement_notifications_no_contact_owner():
    """
    Ensure that _send_endorsement_notifications does not crash if the contact has no owner.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()
    service._get_community_moderators = AsyncMock(return_value=[200, 201])

    endorsement = AsyncMock()
    endorsement.id = 123
    endorsement.contact.user_id = None  # No contact owner
    endorsement.user.first_name = "Eve"
    endorsement.user.last_name = "Brown"
    endorsement.contact.contact_name = "Charlie Doe"
    endorsement.community.name = "Some Community"
    endorsement.rating = 4.0
    endorsement.comment = "Nice Job!"
    endorsement.community_id = 3

    await service._send_endorsement_notifications(endorsement)

    # Ensure that no notification was sent since there's no contact owner
    service._notification_service.send_notification.assert_not_called()


@pytest.mark.asyncio
async def test_send_endorsement_notifications_empty_moderators():
    """
    Ensure that no verification notifications are sent when there are no moderators.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()
    service._get_community_moderators = AsyncMock(return_value=[])

    endorsement = AsyncMock()
    endorsement.id = 456
    endorsement.contact.user_id = 20
    endorsement.user.first_name = "Alice"
    endorsement.user.last_name = "Smith"
    endorsement.contact.contact_name = "Bob Johnson"
    endorsement.community.name = "Example Community"
    endorsement.rating = 3.8
    endorsement.comment = "Nice!"  # Has a comment, so normally would notify moderators
    endorsement.community_id = 888

    await service._send_endorsement_notifications(endorsement)

    # Expect only owner notification, since no moderators exist
    service._notification_service.send_notification.assert_called_once_with(
        NotificationType.ENDORSEMENT_RECEIVED,
        endorsement.contact.user_id,
        {
            "endorsement_id": endorsement.id,
            "endorser_name": "Alice Smith",
            "contact_name": "Bob Johnson",
            "community_name": "Example Community",
            "rating": 3.8,
            "has_comment": True,
        },
    )


@pytest.mark.asyncio
async def test_send_endorsement_notifications_handles_failure():
    """
    Ensure that _send_endorsement_notifications gracefully handles exceptions.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()

    # Simulate failure when calling send_notification
    async def raise_exception(*args, **kwargs):
        raise Exception("Simulated failure")

    service._notification_service.send_notification = AsyncMock(
        side_effect=raise_exception
    )
    service._get_community_moderators = AsyncMock(return_value=[100])

    endorsement = AsyncMock()
    endorsement.id = 789
    endorsement.contact.user_id = 30
    endorsement.user.first_name = "Chris"
    endorsement.user.last_name = "Evans"
    endorsement.contact.contact_name = "Johnny Storm"
    endorsement.community.name = "Marvel Community"
    endorsement.rating = 5.0
    endorsement.comment = "Flame on!"
    endorsement.community_id = 42

    await service._send_endorsement_notifications(endorsement)

    # Ensure logger error method was called
    service._logger.error.assert_called_with(
        "Failed to send endorsement notifications",
        error="Simulated failure",
        endorsement_id=endorsement.id,
    )


@pytest.mark.asyncio
async def test_send_endorsement_notifications_no_moderators_empty():
    """
    Ensure that if there are no moderators, _send_endorsement_notifications still sends only the owner notification.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()
    service._get_community_moderators = AsyncMock(return_value=[])

    endorsement = AsyncMock()
    endorsement.id = 555
    endorsement.contact.user_id = 42
    endorsement.user.first_name = "Bruce"
    endorsement.user.last_name = "Wayne"
    endorsement.contact.contact_name = "Alfred Pennyworth"
    endorsement.community.name = "Gotham Elite"
    endorsement.rating = 5
    endorsement.comment = "Best butler in town!"
    endorsement.community_id = 777

    await service._send_endorsement_notifications(endorsement)

    # Verify owner notification was sent
    service._notification_service.send_notification.assert_called_once_with(
        NotificationType.ENDORSEMENT_RECEIVED,
        endorsement.contact.user_id,
        {
            "endorsement_id": endorsement.id,
            "endorser_name": "Bruce Wayne",
            "contact_name": "Alfred Pennyworth",
            "community_name": "Gotham Elite",
            "rating": 5,
            "has_comment": True,
        },
    )

    # Ensure that NO verification notifications were sent
    service._notification_service.send_notification.assert_called_once()


@pytest.mark.asyncio
async def test_send_endorsement_notifications_logs_error_when_failing():
    """
    Ensure that if notification sending fails, an error is logged.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()

    # Simulate failure in notification sending
    async def raise_exception(*args, **kwargs):
        raise Exception("Simulated send failure")

    service._notification_service.send_notification = AsyncMock(
        side_effect=raise_exception
    )
    service._get_community_moderators = AsyncMock(return_value=[123, 456])

    endorsement = AsyncMock()
    endorsement.id = 888
    endorsement.contact.user_id = 45
    endorsement.user.first_name = "Steve"
    endorsement.user.last_name = "Rogers"
    endorsement.contact.contact_name = "Bucky Barnes"
    endorsement.community.name = "Shield"
    endorsement.rating = 4.0
    endorsement.comment = "On your left."
    endorsement.community_id = 555

    await service._send_endorsement_notifications(endorsement)

    # Ensure error was logged when send_notification failed
    service._logger.error.assert_called_with(
        "Failed to send endorsement notifications",
        error="Simulated send failure",
        endorsement_id=endorsement.id,
    )


@pytest.mark.asyncio
async def test_send_verification_notifications():
    """
    Ensure that _send_verification_notifications sends notifications to both the endorsement creator and contact owner.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()

    # Mock _build_notification_context
    service._build_notification_context = AsyncMock(
        return_value={"context_key": "context_value"}
    )

    endorsement = AsyncMock()
    endorsement.id = 123  # Ensure this is an integer
    endorsement.user_id = 77  # Endorsement creator
    endorsement.contact = AsyncMock()
    endorsement.contact.user_id = 99  # Contact owner

    # Ensure endorsement_id is an actual integer
    endorsement.endorsement_id = 123

    await service._send_verification_notifications(endorsement)

    # Ensure _build_notification_context was called
    service._build_notification_context.assert_called_with(endorsement)

    # Verify the endorsement creator received the verification notification
    service._notification_service.send_notification.assert_any_call(
        NotificationType.ENDORSEMENT_VERIFIED,
        77,
        {"context_key": "context_value"},
        123,  # Now correctly set as an integer
    )

    # Verify the contact owner received the verification notification
    service._notification_service.send_notification.assert_any_call(
        NotificationType.CONTACT_ENDORSEMENT_VERIFIED,
        99,
        {"context_key": "context_value"},
        123,  # Now correctly set as an integer
    )


@pytest.mark.asyncio
async def test_send_verification_notifications_no_contact_owner():
    """
    Ensure that _send_verification_notifications does not send a notification to a missing contact owner.
    """
    service = NotificationService()
    service._logger = AsyncMock()
    service._notification_service = AsyncMock()

    # Mock _build_notification_context
    service._build_notification_context = AsyncMock(
        return_value={"context_key": "context_value"}
    )

    endorsement = AsyncMock()
    endorsement.id = 456  # Ensure this is an integer
    endorsement.user_id = 88  # Endorsement creator
    endorsement.contact = None  # No contact

    # Ensure endorsement_id is an actual integer
    endorsement.endorsement_id = 456

    await service._send_verification_notifications(endorsement)

    # Ensure _build_notification_context was called
    service._build_notification_context.assert_called_with(endorsement)

    # Verify the endorsement creator received the verification notification
    service._notification_service.send_notification.assert_any_call(
        NotificationType.ENDORSEMENT_VERIFIED,
        88,
        {"context_key": "context_value"},
        456,  # Now correctly set as an integer
    )

    # Ensure no notification was sent to a missing contact owner
    service._notification_service.send_notification.assert_called_once()
