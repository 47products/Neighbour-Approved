import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from app.services.endorsement_service.endorsement_service_notifications import (
    NotificationMixin,
)
from app.services.notification_service import NotificationType

# Ensure that NotificationType includes the CONTACT_ENDORSEMENT_VERIFIED attribute.
if not hasattr(NotificationType, "CONTACT_ENDORSEMENT_VERIFIED"):
    NotificationType.CONTACT_ENDORSEMENT_VERIFIED = "contact_endorsement_verified"


# --- Dummy classes for testing ---


class DummyContact:
    def __init__(self, user_id: int):
        self.user_id = user_id


class DummyEndorsement:
    """
    A dummy endorsement object with the minimal attributes required by NotificationMixin.
    Accepts a 'with_contact' parameter to determine if a contact should be set.
    """

    def __init__(self, with_contact: bool = True):
        self.id = 123
        self.user_id = 10
        self.verification_date = datetime.now() - timedelta(days=1)
        self.verification_notes = "Verified successfully"
        if with_contact:
            self.contact = DummyContact(user_id=20)
        else:
            self.contact = None


class DummyNotificationMixin(NotificationMixin):
    """
    A dummy subclass of NotificationMixin that sets up the required
    _notification_service, _logger, and _calculate_rating_impact.
    """

    def __init__(self):
        # Create a dummy notification service with an async send_notification.
        self._notification_service = type("DummyService", (), {})()
        self._notification_service.send_notification = AsyncMock()
        # Create a dummy logger.
        self._logger = MagicMock()

    async def _calculate_rating_impact(self, endorsement):
        # For testing, simply return a fixed value.
        return 0.5


# --- Tests for _build_notification_context ---


@pytest.mark.asyncio
async def test_build_notification_context():
    """
    Test that _build_notification_context returns a dictionary with the expected keys and values.
    """
    mixin = DummyNotificationMixin()
    dummy_endorsement = DummyEndorsement(with_contact=True)

    context = await mixin._build_notification_context(dummy_endorsement)

    # Check that the context includes the correct endorsement details.
    assert context["verification_date"] == dummy_endorsement.verification_date
    assert context["verification_notes"] == dummy_endorsement.verification_notes
    assert context["rating_impact"] == pytest.approx(0.5)
    assert "timestamp" in context
    assert isinstance(context["timestamp"], datetime)
    assert context["type"] == "endorsement_verification"


# --- Tests for _send_verification_notifications ---


@pytest.mark.asyncio
async def test_send_verification_notifications_with_contact():
    """
    Test that _send_verification_notifications dispatches two notifications
    when the endorsement has a valid contact.
    """
    mixin = DummyNotificationMixin()
    dummy_endorsement = DummyEndorsement(with_contact=True)

    # Override _build_notification_context to return a fixed context.
    fixed_context = {
        "verification_date": dummy_endorsement.verification_date,
        "verification_notes": dummy_endorsement.verification_notes,
        "rating_impact": 0.5,
        "timestamp": "dummy_timestamp",
        "type": "endorsement_verification",
    }
    mixin._build_notification_context = AsyncMock(return_value=fixed_context)

    await mixin._send_verification_notifications(dummy_endorsement)

    # Two notifications should be sent.
    assert mixin._notification_service.send_notification.call_count == 2

    # First call: notification for the endorsement creator.
    first_call_args = mixin._notification_service.send_notification.call_args_list[0][0]
    assert first_call_args[0] == NotificationType.ENDORSEMENT_VERIFIED
    assert first_call_args[1] == dummy_endorsement.user_id
    assert first_call_args[2] == fixed_context
    assert first_call_args[3] == dummy_endorsement.id

    # Second call: notification for the contact owner.
    second_call_args = mixin._notification_service.send_notification.call_args_list[1][
        0
    ]
    assert second_call_args[0] == NotificationType.CONTACT_ENDORSEMENT_VERIFIED
    assert second_call_args[1] == dummy_endorsement.contact.user_id
    assert second_call_args[2] == fixed_context
    assert second_call_args[3] == dummy_endorsement.id


@pytest.mark.asyncio
async def test_send_verification_notifications_without_contact():
    """
    Test that _send_verification_notifications dispatches only one notification
    when the endorsement does not have a contact.
    """
    mixin = DummyNotificationMixin()
    dummy_endorsement = DummyEndorsement(with_contact=False)

    fixed_context = {
        "verification_date": dummy_endorsement.verification_date,
        "verification_notes": dummy_endorsement.verification_notes,
        "rating_impact": 0.5,
        "timestamp": "dummy_timestamp",
        "type": "endorsement_verification",
    }
    mixin._build_notification_context = AsyncMock(return_value=fixed_context)

    await mixin._send_verification_notifications(dummy_endorsement)

    # Only one notification should be sent (for the endorsement creator).
    assert mixin._notification_service.send_notification.call_count == 1

    call_args = mixin._notification_service.send_notification.call_args[0]
    assert call_args[0] == NotificationType.ENDORSEMENT_VERIFIED
    assert call_args[1] == dummy_endorsement.user_id
    assert call_args[2] == fixed_context
    assert call_args[3] == dummy_endorsement.id


@pytest.mark.asyncio
async def test_send_verification_notifications_exception_in_context():
    """
    Test that if _build_notification_context raises an exception,
    the error is logged and the exception is swallowed.
    """
    mixin = DummyNotificationMixin()
    dummy_endorsement = DummyEndorsement(with_contact=True)

    # Make _build_notification_context raise an exception.
    mixin._build_notification_context = AsyncMock(
        side_effect=RuntimeError("Context error")
    )

    await mixin._send_verification_notifications(dummy_endorsement)

    # Verify that the logger.error was called with the exception details.
    mixin._logger.error.assert_called_once()
    _, kwargs = mixin._logger.error.call_args
    assert "Context error" in kwargs.get("error", "")
    # No notification should have been sent.
    assert mixin._notification_service.send_notification.call_count == 0


@pytest.mark.asyncio
async def test_send_verification_notifications_exception_in_notification():
    """
    Test that if sending a notification raises an exception,
    the error is logged and the exception is swallowed.
    """
    mixin = DummyNotificationMixin()
    dummy_endorsement = DummyEndorsement(with_contact=True)

    fixed_context = {
        "verification_date": dummy_endorsement.verification_date,
        "verification_notes": dummy_endorsement.verification_notes,
        "rating_impact": 0.5,
        "timestamp": "dummy_timestamp",
        "type": "endorsement_verification",
    }
    mixin._build_notification_context = AsyncMock(return_value=fixed_context)
    # Simulate an exception when sending the first notification.
    mixin._notification_service.send_notification = AsyncMock(
        side_effect=RuntimeError("Notification error")
    )

    await mixin._send_verification_notifications(dummy_endorsement)

    # Logger should capture the error.
    mixin._logger.error.assert_called_once()
    _, kwargs = mixin._logger.error.call_args
    assert "Notification error" in kwargs.get("error", "")
