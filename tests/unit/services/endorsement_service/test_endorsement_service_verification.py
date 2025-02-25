"""
Unit tests for the VerificationMixin in the Endorsement Service Verification Module.

This module tests the functionality of the VerificationMixin, including:
    - verify_endorsement: Marking an endorsement as verified.
    - process_verification: Running the full verification workflow.
    - _validate_verification_eligibility: Checking eligibility of an endorsement for verification.
    - _create_verification_audit_log: Creating (or failing to create) an audit log.
    - _can_verify_endorsement: Determining if an endorsement is eligible.
    - _format_verification_notes: Formatting the verification notes with context.

Usage:
    Run these tests using pytest.
Dependencies:
    - pytest
    - pytest-asyncio
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.endorsement_service.endorsement_service_verification import (
    VerificationMixin,
)
from app.services.service_exceptions import (
    ValidationError,
    ResourceNotFoundError,
    StateError,
)


# ------------------------------------------------------------------------------
# Dummy Classes and Mixin for Testing
# ------------------------------------------------------------------------------


class DummyEndorsement:
    """
    Dummy endorsement class for testing VerificationMixin.

    Attributes:
        id (int): Endorsement identifier.
        comment (Optional[str]): The comment on the endorsement.
        rating (Optional[float]): The rating value.
        is_verified (bool): Whether the endorsement is verified.
        contact_id (int): The identifier for the contact.
        community_id (int): The community identifier.
        verification_date (Optional[datetime]): The date of verification.
        verification_notes (str): The verification notes.
    """

    def __init__(
        self,
        id: int = 1,
        comment: Optional[str] = "Good service",
        rating: Optional[float] = 4.0,
        is_verified: bool = False,
        contact_id: int = 10,
        community_id: int = 100,
    ):
        self.id = id
        self.comment = comment
        self.rating = rating
        self.is_verified = is_verified
        self.contact_id = contact_id
        self.community_id = community_id
        self.verification_date = None
        self.verification_notes = ""


class DummyVerificationMixin(VerificationMixin):
    """
    Dummy subclass of VerificationMixin for testing purposes.

    This class provides dummy implementations for:
        - get_endorsement
        - _update_contact_metrics
        - _update_verification_metrics
        - _create_verification_audit_log
        - _send_verification_notifications

    It also sets up dummy database, repository, and logging attributes.
    """

    def __init__(self):
        self.db = MagicMock()
        self.db.commit = AsyncMock()
        self.repository = MagicMock()
        self._logger = MagicMock()
        self.MAX_PENDING_VERIFICATIONS = 5
        # Storage for a dummy endorsement; tests override this as needed.
        self._dummy_endorsement: Optional[DummyEndorsement] = None

    async def get_endorsement(self, endorsement_id: int) -> Optional[DummyEndorsement]:
        """Return the preset dummy endorsement."""
        return self._dummy_endorsement

    async def _update_contact_metrics(self, contact_id: int) -> None:
        """Dummy implementation that does nothing."""

    async def _update_verification_metrics(self, endorsement: DummyEndorsement) -> None:
        """Dummy implementation that does nothing."""

    async def _create_verification_audit_log(
        self, endorsement: DummyEndorsement, verifier_id: int
    ) -> None:
        """
        Create an audit log entry for an endorsement verification.

        In the try block, logs audit data using _logger.info.
        If an exception occurs, logs an error using _logger.error.
        """
        try:
            audit_data = {
                "endorsement_id": endorsement.id,
                "verifier_id": verifier_id,
                "verification_date": endorsement.verification_date,
                "contact_id": endorsement.contact_id,
                "community_id": endorsement.community_id,
            }
            self._logger.info("verification_audit_log_created", **audit_data)
        except Exception as e:
            self._logger.error(
                "audit_log_creation_failed",
                error=str(e),
                endorsement_id=endorsement.id,
            )

    async def _send_verification_notifications(
        self, endorsement: DummyEndorsement
    ) -> None:
        """Dummy implementation that does nothing."""

    async def _validate_verification_eligibility(
        self, endorsement: DummyEndorsement
    ) -> None:
        """
        Validate that an endorsement is eligible for verification.

        Raises ValidationError if already verified or if neither comment nor rating is present.
        """
        if endorsement.is_verified:
            raise ValidationError("Endorsement already verified")
        if not (endorsement.comment or endorsement.rating):
            raise ValidationError("Insufficient content for verification")

    async def _can_verify_endorsement(self, endorsement: DummyEndorsement) -> bool:
        """
        Dummy implementation that returns False if already verified or missing content,
        or compares pending verification count.
        """
        if endorsement.is_verified or not (endorsement.comment or endorsement.rating):
            return False
        pending_count = await self.repository.get_pending_verifications_count(
            endorsement.contact_id
        )
        return pending_count < self.MAX_PENDING_VERIFICATIONS

    def _format_verification_notes(
        self, notes: Optional[str], context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Format the verification notes with additional context.
        """
        formatted = notes or ""
        if context:
            formatted += " | Context: " + ", ".join(
                f"{k}={v}" for k, v in context.items()
            )
        return formatted


# ------------------------------------------------------------------------------
# Tests for verify_endorsement
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_endorsement_not_found():
    """
    Test that verify_endorsement raises ResourceNotFoundError if the endorsement is not found.
    """
    mixin = DummyVerificationMixin()
    mixin._dummy_endorsement = None
    with pytest.raises(ResourceNotFoundError):
        await mixin.verify_endorsement(endorsement_id=1, verified_by=99)


@pytest.mark.asyncio
async def test_verify_endorsement_ineligible():
    """
    Test that verify_endorsement raises ValidationError if the endorsement fails eligibility.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement()
    mixin._dummy_endorsement = endorsement
    mixin._can_verify_endorsement = AsyncMock(return_value=False)
    with pytest.raises(ValidationError):
        await mixin.verify_endorsement(endorsement_id=1, verified_by=99)


@pytest.mark.asyncio
async def test_verify_endorsement_success():
    """
    Test that verify_endorsement successfully marks an endorsement as verified.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement()
    mixin._dummy_endorsement = endorsement
    mixin._can_verify_endorsement = AsyncMock(return_value=True)
    result = await mixin.verify_endorsement(endorsement_id=1, verified_by=99)
    assert result is True
    assert endorsement.is_verified is True
    assert endorsement.verification_date is not None
    assert "Verified by user 99" in endorsement.verification_notes
    mixin.db.commit.assert_called_once()
    mixin._logger.info.assert_called_with(
        "endorsement_verified", endorsement_id=1, verified_by=99
    )


# ------------------------------------------------------------------------------
# Tests for process_verification
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_verification_not_found():
    """
    Test that process_verification raises ResourceNotFoundError when the endorsement is not found.
    """
    mixin = DummyVerificationMixin()
    mixin._dummy_endorsement = None
    with pytest.raises(ResourceNotFoundError):
        await mixin.process_verification(endorsement_id=1, verifier_id=99)


@pytest.mark.asyncio
async def test_process_verification_eligibility_failure():
    """
    Test that process_verification propagates a ValidationError if eligibility validation fails.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(is_verified=True)
    mixin._dummy_endorsement = endorsement
    with pytest.raises(ValidationError):
        await mixin.process_verification(endorsement_id=1, verifier_id=99)


@pytest.mark.asyncio
async def test_process_verification_success():
    """
    Test that process_verification successfully processes an endorsement verification.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(is_verified=False, comment="Good", rating=4.0)
    mixin._dummy_endorsement = endorsement
    mixin._validate_verification_eligibility = AsyncMock(return_value=None)
    mixin._update_verification_metrics = AsyncMock()
    mixin._create_verification_audit_log = AsyncMock()
    mixin._send_verification_notifications = AsyncMock()
    mixin._format_verification_notes = lambda notes, ctx: "Formatted notes"

    updated = await mixin.process_verification(
        endorsement_id=1,
        verifier_id=99,
        verification_context={"extra": "info"},
        verification_notes="Base note",
    )
    assert updated.is_verified is True
    assert updated.verification_date is not None
    assert updated.verification_notes == "Formatted notes"
    mixin._update_verification_metrics.assert_called_once_with(endorsement)
    mixin._create_verification_audit_log.assert_called_once_with(endorsement, 99)
    mixin._send_verification_notifications.assert_called_once_with(endorsement)
    mixin.db.commit.assert_called_once()


# New Test: Process verification with no notes or context
@pytest.mark.asyncio
async def test_process_verification_no_notes():
    """
    Test that process_verification handles the case when no verification notes or context are provided.

    This test ensures that _format_verification_notes returns an empty string.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(is_verified=False, comment="Good", rating=4.0)
    mixin._dummy_endorsement = endorsement
    mixin._validate_verification_eligibility = AsyncMock(return_value=None)
    mixin._update_verification_metrics = AsyncMock()
    mixin._create_verification_audit_log = AsyncMock()
    mixin._send_verification_notifications = AsyncMock()
    # _format_verification_notes returns empty string if notes is None.
    mixin._format_verification_notes = lambda notes, ctx: notes or ""
    updated = await mixin.process_verification(endorsement_id=1, verifier_id=99)
    assert updated.verification_notes == ""


# ------------------------------------------------------------------------------
# Tests for _validate_verification_eligibility
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_verification_eligibility_already_verified():
    """
    Test that _validate_verification_eligibility raises ValidationError if the endorsement is already verified.
    (Covers missing line 152.)
    """
    mixin = VerificationMixin()
    endorsement = DummyEndorsement()
    endorsement.is_verified = True
    endorsement.comment = "Some comment"
    endorsement.rating = 4.0
    with pytest.raises(ValidationError, match="Endorsement already verified"):
        await mixin._validate_verification_eligibility(endorsement)


@pytest.mark.asyncio
async def test_validate_verification_eligibility_insufficient_content():
    """
    Test that _validate_verification_eligibility raises ValidationError when neither comment nor rating is provided.
    (Covers the branch at line 153->exit.)
    """
    mixin = VerificationMixin()
    endorsement = DummyEndorsement()
    endorsement.is_verified = False
    endorsement.comment = None
    endorsement.rating = None
    with pytest.raises(ValidationError, match="Insufficient content for verification"):
        await mixin._validate_verification_eligibility(endorsement)


@pytest.mark.asyncio
async def test_validate_verification_eligibility_success():
    """
    Test that _validate_verification_eligibility passes for a valid endorsement.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(is_verified=False, comment="Good", rating=4.0)
    await mixin._validate_verification_eligibility(endorsement)


@pytest.mark.asyncio
async def test_validate_verification_eligibility_missing_content():
    """
    Test that _validate_verification_eligibility raises a ValidationError
    when the endorsement lacks both comment and rating.

    (Covers missing lines 151-154.)
    """
    mixin = VerificationMixin()

    # Create a dummy endorsement-like object with no comment and no rating.
    class DummyCE:
        is_verified = False
        comment = None
        rating = None

    endorsement = DummyCE()

    with pytest.raises(ValidationError, match="Insufficient content for verification"):
        await mixin._validate_verification_eligibility(endorsement)


# ------------------------------------------------------------------------------
# Tests for _create_verification_audit_log
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_verification_audit_log_success():
    """
    Test that _create_verification_audit_log logs an audit log entry successfully.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(contact_id=10, community_id=100)
    endorsement.id = 42
    endorsement.verification_date = datetime.now(timezone.utc)
    await mixin._create_verification_audit_log(endorsement, verifier_id=99)
    mixin._logger.info.assert_called_with(
        "verification_audit_log_created",
        endorsement_id=42,
        verifier_id=99,
        verification_date=endorsement.verification_date,
        contact_id=10,
        community_id=100,
    )


@pytest.mark.asyncio
async def test_create_verification_audit_log_failure_corrected():
    """
    Test that _create_verification_audit_log handles exceptions by logging an error,
    but does not interrupt the verification process.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(contact_id=10, community_id=100)
    endorsement.id = 42
    endorsement.verification_date = datetime.now(timezone.utc)
    # Force logger.info to raise an exception.
    mixin._logger.info = MagicMock(side_effect=Exception("Logging failed"))
    mixin._logger.error = MagicMock()
    await mixin._create_verification_audit_log(endorsement, verifier_id=99)
    mixin._logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_create_verification_audit_log_error():
    """
    Test that _create_verification_audit_log handles exceptions by logging an error.

    This test forces an exception in the call to _logger.info so that the except branch is executed.
    (Covers missing lines 201-208 and 223-228.)
    """
    mixin = VerificationMixin()

    # Create a dummy endorsement-like object.
    class DummyCE:
        id = 42
        contact_id = 10
        community_id = 100
        verification_date = datetime(
            2025, 2, 10, 13, 12, 50, 388179, tzinfo=timezone.utc
        )

    endorsement = DummyCE()
    verifier_id = 99

    # Configure the logger so that info() raises an exception.
    mixin._logger = MagicMock()
    mixin._logger.info.side_effect = Exception("Test failure")
    mixin._logger.error = MagicMock()

    await mixin._create_verification_audit_log(endorsement, verifier_id)
    mixin._logger.error.assert_called_once()


# ------------------------------------------------------------------------------
# Tests for _can_verify_endorsement
# ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_can_verify_endorsement_already_verified():
    """
    Test that _can_verify_endorsement returns False if the endorsement is already verified.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(is_verified=True, comment="Good", rating=4.0)
    result = await mixin._can_verify_endorsement(endorsement)
    assert result is False


@pytest.mark.asyncio
async def test_can_verify_endorsement_insufficient_content():
    """
    Test that _can_verify_endorsement returns False if the endorsement has insufficient content.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(comment=None, rating=None)
    result = await mixin._can_verify_endorsement(endorsement)
    assert result is False


@pytest.mark.asyncio
async def test_can_verify_endorsement_pending_too_high():
    """
    Test that _can_verify_endorsement returns False when the pending verifications count
    is not less than MAX_PENDING_VERIFICATIONS.

    (Covers missing lines 223-228.)
    """
    mixin = VerificationMixin()
    mixin.MAX_PENDING_VERIFICATIONS = 5

    # Create a dummy endorsement-like object that is eligible based on content.
    class DummyCE:
        is_verified = False
        comment = "Good"
        rating = 4.0
        contact_id = 10

    endorsement = DummyCE()

    # Simulate the repository returning a pending count equal to MAX_PENDING_VERIFICATIONS.
    mixin.repository = MagicMock()
    mixin.repository.get_pending_verifications_count = AsyncMock(return_value=5)

    result = await mixin._can_verify_endorsement(endorsement)
    assert result is False


@pytest.mark.asyncio
async def test_can_verify_endorsement_success():
    """
    Test that _can_verify_endorsement returns True when the endorsement is eligible.
    """
    mixin = DummyVerificationMixin()
    endorsement = DummyEndorsement(
        is_verified=False, comment="Good", rating=4.0, contact_id=10
    )
    mixin.repository.get_pending_verifications_count = AsyncMock(return_value=0)
    result = await mixin._can_verify_endorsement(endorsement)
    assert result is True


@pytest.mark.asyncio
async def test_can_verify_endorsement_immediate_false():
    """
    Test that _can_verify_endorsement returns False immediately when the endorsement is already verified.
    (Covers the if branch at line 202.)
    """
    mixin = VerificationMixin()
    endorsement = DummyEndorsement()
    endorsement.is_verified = True
    endorsement.comment = "Valid comment"
    endorsement.rating = 3.0
    # We don’t need to set repository in this case since the early return is taken.
    result = await mixin._can_verify_endorsement(endorsement)
    assert result is False


# ------------------------------------------------------------------------------
# Tests for _format_verification_notes
# ------------------------------------------------------------------------------


def test_format_verification_notes_with_context():
    """
    Test that _format_verification_notes correctly appends context information when provided.
    (Covers lines 224–228.)
    """
    mixin = VerificationMixin()
    base_notes = "Base note"
    context = {"k": "v", "a": "b"}
    formatted = mixin._format_verification_notes(base_notes, context)
    # Expected output should include the base note, the separator, and the context key=value pairs.
    assert formatted.startswith("Base note | Context:")
    assert "k=v" in formatted
    assert "a=b" in formatted


def test_format_verification_notes_without_context():
    """
    Test that _format_verification_notes returns just the notes if no context is provided.
    """
    mixin = DummyVerificationMixin()
    notes = "Only note"
    formatted = mixin._format_verification_notes(notes, None)
    assert formatted == "Only note"


def test_format_verification_notes_context_only():
    """
    Test that _format_verification_notes returns an empty string with appended context when no notes are provided.
    """
    mixin = DummyVerificationMixin()
    formatted = mixin._format_verification_notes(None, {"k": "v"})
    assert formatted.startswith(" | Context:")
    assert "k=v" in formatted


def test_format_verification_notes_appends_context():
    """
    Test that _format_verification_notes appends context data when provided.

    This test ensures that given a base note and a context dictionary,
    the method returns a string that appends the context in the format:
        "<base_notes> | Context: key1=value1, key2=value2"
    """
    mixin = DummyVerificationMixin()
    base_notes = "Test note"
    context = {"key1": "value1", "key2": "value2"}
    result = mixin._format_verification_notes(base_notes, context)
    # Assuming dictionary insertion order is preserved (Python 3.7+),
    # the expected output is:
    expected = "Test note | Context: key1=value1, key2=value2"
    assert result == expected


def test_format_verification_notes_no_context():
    """
    Test that _format_verification_notes returns just the base note when no context is provided.
    """
    mixin = DummyVerificationMixin()
    base_notes = "Test note"
    result = mixin._format_verification_notes(base_notes, None)
    assert result == "Test note"
