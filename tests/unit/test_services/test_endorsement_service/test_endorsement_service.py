"""
Unit tests to improve coverage for the EndorsementService module.

These tests exercise:
- _validate_endorsement_creation under various conditions (valid, missing/inactive contact or community,
  rating out-of-range, too-short comment, duplicate endorsement).
- _update_contact_metrics for successful metric computation, missing contact, and exception scenarios.
- create_endorsement in the success path and when validation fails.

Make sure your shared fixtures (e.g. dummy_db) are provided via conftest.py.
"""

import math
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.service_exceptions import (
    ValidationError,
    DuplicateResourceError,
    ResourceNotFoundError,
    StateError,
)
from app.api.v1.schemas.contact_endorsement_schema import ContactEndorsementCreate
from app.services.endorsement_service.endorsement_service import EndorsementService

# --- Dummy model classes for testing ---


class DummyContact:
    def __init__(self, id, is_active=True):
        self.id = id
        self.is_active = is_active
        self.endorsements_count = 0
        self.verified_endorsements_count = 0
        self.average_rating = None
        self.user_id = 2
        self.contact_name = "Dummy Contact"


class DummyCommunity:
    def __init__(self, id, is_active=True):
        self.id = id
        self.is_active = is_active
        self.verified_endorsements_count = 0
        self.total_endorsements = 0
        self.name = "Dummy Community"


class DummyContactEndorsement:
    def __init__(
        self,
        id,
        contact_id,
        community_id,
        user_id,
        rating,
        comment,
        created_at,
        is_verified=False,  # Allow passing in a value
    ):
        self.id = id
        self.contact_id = contact_id
        self.community_id = community_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment
        self.created_at = created_at
        self.is_verified = is_verified
        self.verification_notes = ""
        self.verification_date = None
        self.user = MagicMock(first_name="John", last_name="Doe")
        self.contact = DummyContact(contact_id)
        self.community = DummyCommunity(community_id)


# --- Tests for _validate_endorsement_creation ---


@pytest.mark.asyncio
async def test_validate_creation_valid(dummy_db):
    """Test that _validate_endorsement_creation passes with valid data."""
    service = EndorsementService(db=dummy_db)
    data = ContactEndorsementCreate(
        contact_id=1,
        community_id=1,
        user_id=10,
        rating=3,
        comment="This is a valid comment.",
    )
    # Return active contact and community.
    dummy_db.get = AsyncMock(
        side_effect=lambda model, id: (
            DummyContact(1) if model.__name__ == "Contact" else DummyCommunity(1)
        )
    )
    # Simulate no existing endorsement.
    service.repository.get_user_endorsement = AsyncMock(return_value=None)
    await service._validate_endorsement_creation(data)


@pytest.mark.asyncio
async def test_validate_creation_missing_contact(dummy_db):
    """Test that missing contact causes a ValidationError."""
    service = EndorsementService(db=dummy_db)
    data = ContactEndorsementCreate(
        contact_id=2, community_id=1, user_id=10, rating=3, comment="Valid comment."
    )
    dummy_db.get = AsyncMock(
        side_effect=lambda model, id: (
            None if model.__name__ == "Contact" else DummyCommunity(1)
        )
    )
    with pytest.raises(ValidationError, match="Contact 2 not found or inactive"):
        await service._validate_endorsement_creation(data)


@pytest.mark.asyncio
async def test_validate_creation_inactive_contact(dummy_db):
    """Test that an inactive contact causes a ValidationError."""
    service = EndorsementService(db=dummy_db)
    data = ContactEndorsementCreate(
        contact_id=2, community_id=1, user_id=10, rating=3, comment="Valid comment."
    )
    inactive_contact = DummyContact(2, is_active=False)
    dummy_db.get = AsyncMock(
        side_effect=lambda model, id: (
            inactive_contact if model.__name__ == "Contact" else DummyCommunity(1)
        )
    )
    with pytest.raises(ValidationError, match="Contact 2 not found or inactive"):
        await service._validate_endorsement_creation(data)


@pytest.mark.asyncio
async def test_validate_creation_missing_community(dummy_db):
    """Test that missing community causes a ValidationError."""
    service = EndorsementService(db=dummy_db)
    data = ContactEndorsementCreate(
        contact_id=1, community_id=2, user_id=10, rating=3, comment="Valid comment."
    )
    dummy_db.get = AsyncMock(
        side_effect=lambda model, id: (
            DummyContact(1) if model.__name__ == "Contact" else None
        )
    )
    with pytest.raises(ValidationError, match="Community 2 not found or inactive"):
        await service._validate_endorsement_creation(data)


@pytest.mark.asyncio
async def test_validate_creation_rating_out_of_range(dummy_db):
    """Test that an out-of-range rating causes a ValidationError."""
    service = EndorsementService(db=dummy_db)
    # Rating too low.
    data_low = ContactEndorsementCreate(
        contact_id=1, community_id=1, user_id=10, rating=0, comment="Valid comment."
    )
    dummy_db.get = AsyncMock(
        side_effect=lambda model, id: (
            DummyContact(1) if model.__name__ == "Contact" else DummyCommunity(1)
        )
    )
    service.repository.get_user_endorsement = AsyncMock(return_value=None)
    with pytest.raises(ValidationError, match="Rating must be between 1 and 5"):
        await service._validate_endorsement_creation(data_low)
    # Rating too high.
    data_high = ContactEndorsementCreate(
        contact_id=1, community_id=1, user_id=10, rating=6, comment="Valid comment."
    )
    with pytest.raises(ValidationError, match="Rating must be between 1 and 5"):
        await service._validate_endorsement_creation(data_high)


@pytest.mark.asyncio
async def test_validate_creation_comment_too_short(dummy_db):
    """Test that a too-short comment causes a ValidationError."""
    service = EndorsementService(db=dummy_db)
    data = ContactEndorsementCreate(
        contact_id=1, community_id=1, user_id=10, rating=3, comment="Too short"
    )
    dummy_db.get = AsyncMock(
        side_effect=lambda model, id: (
            DummyContact(1) if model.__name__ == "Contact" else DummyCommunity(1)
        )
    )
    service.repository.get_user_endorsement = AsyncMock(return_value=None)
    with pytest.raises(ValidationError, match="Comment must be at least 10 characters"):
        await service._validate_endorsement_creation(data)


@pytest.mark.asyncio
async def test_validate_creation_duplicate(dummy_db):
    """Test that a duplicate endorsement causes a DuplicateResourceError."""
    service = EndorsementService(db=dummy_db)
    data = ContactEndorsementCreate(
        contact_id=1,
        community_id=1,
        user_id=10,
        rating=3,
        comment="Valid comment with sufficient length.",
    )
    dummy_db.get = AsyncMock(
        side_effect=lambda model, id: (
            DummyContact(1) if model.__name__ == "Contact" else DummyCommunity(1)
        )
    )
    service.repository.get_user_endorsement = AsyncMock(return_value=MagicMock())
    with pytest.raises(
        DuplicateResourceError, match="User has already endorsed this contact"
    ):
        await service._validate_endorsement_creation(data)


# --- Tests for _update_contact_metrics ---


@pytest.mark.asyncio
async def test_update_contact_metrics_contact_not_found(dummy_db):
    """Test that _update_contact_metrics raises ResourceNotFoundError when contact is missing."""
    service = EndorsementService(db=dummy_db)
    dummy_db.get = AsyncMock(return_value=None)
    with pytest.raises(ResourceNotFoundError, match="Contact 1 not found"):
        await service._update_contact_metrics(1)


@pytest.mark.asyncio
async def test_update_contact_metrics_success(dummy_db):
    """Test that _update_contact_metrics computes and updates metrics correctly."""
    service = EndorsementService(db=dummy_db)
    contact = DummyContact(1)
    dummy_db.get = AsyncMock(return_value=contact)
    # Create endorsements: two verified with ratings and one unverified.
    endorsements = [
        DummyContactEndorsement(
            1,
            1,
            1,
            10,
            4,
            "Good",
            datetime.now() - timedelta(days=10),
            is_verified=True,
        ),
        DummyContactEndorsement(
            2,
            1,
            1,
            11,
            5,
            "Excellent",
            datetime.now() - timedelta(days=20),
            is_verified=True,
        ),
        DummyContactEndorsement(
            3,
            1,
            1,
            12,
            None,
            "No rating",
            datetime.now() - timedelta(days=30),
            is_verified=False,
        ),
    ]
    service.repository.get_contact_endorsements = AsyncMock(return_value=endorsements)
    dummy_db.commit = AsyncMock()
    await service._update_contact_metrics(1)
    # Verify metrics: total endorsements = 3, verified = 2, average rating = (4+5)/2 = 4.5.
    assert contact.endorsements_count == 3
    assert contact.verified_endorsements_count == 2
    assert math.isclose(contact.average_rating, 4.5, rel_tol=1e-9)
    dummy_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact_metrics_exception(dummy_db):
    """Test that an exception during metrics update leads to rollback and StateError."""
    service = EndorsementService(db=dummy_db)
    contact = DummyContact(1)
    dummy_db.get = AsyncMock(return_value=contact)
    service.repository.get_contact_endorsements = AsyncMock(
        side_effect=Exception("Test exception")
    )
    dummy_db.rollback = AsyncMock()
    with pytest.raises(
        StateError, match="Failed to update contact metrics: Test exception"
    ):
        await service._update_contact_metrics(1)
    dummy_db.rollback.assert_awaited_once()


# --- Tests for create_endorsement ---


@pytest.mark.asyncio
async def test_create_endorsement_success(dummy_db):
    """Test that create_endorsement works correctly in the success path."""
    service = EndorsementService(db=dummy_db)
    data = ContactEndorsementCreate(
        contact_id=1,
        community_id=1,
        user_id=10,
        rating=4,
        comment="A valid comment for creation.",
    )
    dummy_db.get = AsyncMock(
        side_effect=lambda model, id: (
            DummyContact(1) if model.__name__ == "Contact" else DummyCommunity(1)
        )
    )
    service.repository.get_user_endorsement = AsyncMock(return_value=None)
    endorsement = DummyContactEndorsement(
        100, 1, 1, 10, 4, data.comment, datetime.now() - timedelta(days=10)
    )
    service.create = AsyncMock(return_value=endorsement)
    service._update_contact_metrics = AsyncMock()
    result = await service.create_endorsement(data)
    assert result.id == 100
    service._update_contact_metrics.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_create_endorsement_failure(dummy_db):
    """Test that create_endorsement re-raises exceptions from validation."""
    service = EndorsementService(db=dummy_db)
    data = ContactEndorsementCreate(
        contact_id=1, community_id=1, user_id=10, rating=4, comment="A valid comment."
    )
    service._validate_endorsement_creation = AsyncMock(
        side_effect=ValidationError("Test validation error")
    )
    with pytest.raises(ValidationError, match="Test validation error"):
        await service.create_endorsement(data)
