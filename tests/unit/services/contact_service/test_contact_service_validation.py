"""
Unit tests for ContactServiceValidation.

This test suite validates contact creation logic, ensuring:
- Required fields are present.
- Restricted words are not used.
- Duplicate contacts are not created.

Test Coverage:
- `validate_contact_creation()`

Typical usage example:
    pytest tests/unit/test_services/test_contact_service/test_contact_service_validation.py
"""

import pytest
from unittest.mock import MagicMock
from app.db.models.contact_model import Contact
from app.services.service_exceptions import ValidationError, DuplicateResourceError


@pytest.mark.asyncio
async def test_validate_contact_creation_success(
    contact_service_validation, dummy_db, mock_contact_data
):
    """
    Test successful contact validation.
    """
    dummy_db.query.return_value.filter_by.return_value.first.return_value = (
        None  # No duplicate contact found
    )

    # No exception should be raised
    await contact_service_validation.validate_contact_creation(mock_contact_data)


@pytest.mark.asyncio
async def test_validate_contact_creation_missing_fields(
    contact_service_validation, mock_contact_data
):
    """
    Test that validation fails when required fields are missing.
    """
    # Remove a required field
    del mock_contact_data.__dict__["email"]

    with pytest.raises(ValidationError, match="Missing required fields: email"):
        await contact_service_validation.validate_contact_creation(mock_contact_data)


@pytest.mark.asyncio
async def test_validate_contact_creation_restricted_words(
    contact_service_validation, mock_contact_data
):
    """
    Test that validation fails when a contact name contains restricted words.
    """
    mock_contact_data.contact_name = "Admin User"

    with pytest.raises(
        ValidationError, match="Contact name contains restricted words."
    ):
        await contact_service_validation.validate_contact_creation(mock_contact_data)


@pytest.mark.asyncio
async def test_validate_contact_creation_duplicate_email(
    contact_service_validation, dummy_db, mock_contact_data
):
    """
    Test that validation fails when a contact with the same email already exists.
    """
    dummy_db.query.return_value.filter_by.return_value.first.return_value = MagicMock(
        spec=Contact
    )  # Simulate duplicate

    with pytest.raises(
        DuplicateResourceError, match="Contact with this email already exists."
    ):
        await contact_service_validation.validate_contact_creation(mock_contact_data)
