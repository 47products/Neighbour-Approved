"""
Unit tests for ContactServiceVerification.

This test suite validates the contact verification process, ensuring:
- Contacts are verified successfully when criteria are met.
- Verification fails if criteria are not met.
- Errors are handled properly when verification encounters failures.

Test Coverage:
- `verify_contact()`

Typical usage example:
    pytest tests/unit/test_services/test_contact_service/test_contact_service_verification.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.service_exceptions import (
    ResourceNotFoundError,
    ValidationError,
    StateError,
)


@pytest.mark.asyncio
async def test_verify_contact_success(
    contact_service_verification, dummy_db, mock_verifiable_contact
):
    """
    Test successful contact verification.
    """
    dummy_db.query.return_value.filter_by.return_value.first.return_value = (
        mock_verifiable_contact
    )

    result = await contact_service_verification.verify_contact(
        contact_id=1, verified_by=2
    )

    assert result is True
    assert mock_verifiable_contact.is_verified is True
    assert mock_verifiable_contact.verification_date is not None
    assert "Verified by user 2" in mock_verifiable_contact.verification_notes

    dummy_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_contact_not_found(contact_service_verification, dummy_db):
    """
    Test that verification fails when the contact does not exist.
    """
    dummy_db.query.return_value.filter_by.return_value.first.return_value = None

    with pytest.raises(ResourceNotFoundError, match="Contact 99 not found"):
        await contact_service_verification.verify_contact(contact_id=99, verified_by=2)


@pytest.mark.asyncio
async def test_verify_contact_fails_verification_criteria(
    contact_service_verification, dummy_db, mock_unverifiable_contact
):
    """
    Test that verification fails if a contact does not meet the required criteria.
    """
    dummy_db.query.return_value.filter_by.return_value.first.return_value = (
        mock_unverifiable_contact
    )

    with pytest.raises(
        ValidationError, match="Contact does not meet verification requirements"
    ):
        await contact_service_verification.verify_contact(contact_id=2, verified_by=2)


@pytest.mark.asyncio
async def test_verify_contact_state_error(
    contact_service_verification, dummy_db, mock_verifiable_contact
):
    """
    Test that verification rollback is triggered when an error occurs during commit.
    """
    dummy_db.query.return_value.filter_by.return_value.first.return_value = (
        mock_verifiable_contact
    )
    dummy_db.commit = AsyncMock(
        side_effect=Exception("Database error")
    )  # ✅ Ensure commit() is async
    dummy_db.rollback = AsyncMock()

    with pytest.raises(StateError, match="Failed to verify contact: Database error"):
        await contact_service_verification.verify_contact(contact_id=1, verified_by=2)

    dummy_db.rollback.assert_awaited_once()  # ✅ Ensure rollback() is awaited
