"""
Unit tests for the ContactServiceEndorsement module.

This test suite verifies endorsement-related operations for contacts, including:
- Retrieving endorsements for a contact.
- Handling cases where the contact does not exist.

Test Coverage:
- Ensures `get_contact_endorsements` returns the correct endorsements.
- Verifies `get_contact_endorsements` raises an error for non-existent contacts.

Typical usage example:
    pytest tests/unit/test_services/test_contact_service/test_contact_service_endorsement.py
"""

import pytest
from unittest.mock import MagicMock
from app.db.models.contact_model import Contact
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.services.service_exceptions import ResourceNotFoundError


@pytest.mark.asyncio
async def test_get_contact_endorsements_success(contact_service_endorsement, mock_db):
    """
    Test retrieving endorsements for a valid contact.

    Ensures the method returns the expected list of endorsements.
    """
    mock_contact = MagicMock(spec=Contact)
    mock_contact.id = 1
    mock_contact.endorsements = [
        MagicMock(spec=ContactEndorsement, id=1),
        MagicMock(spec=ContactEndorsement, id=2),
    ]

    # Mock database query behavior
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_contact

    endorsements = await contact_service_endorsement.get_contact_endorsements(
        contact_id=1
    )

    assert isinstance(endorsements, list), "Expected endorsements to be a list"
    assert len(endorsements) == 2, "Expected two endorsements to be returned"
    assert endorsements[0].id == 1, "Unexpected endorsement ID"
    assert endorsements[1].id == 2, "Unexpected endorsement ID"


@pytest.mark.asyncio
async def test_get_contact_endorsements_contact_not_found(
    contact_service_endorsement, mock_db
):
    """
    Test that `get_contact_endorsements` raises an error when the contact does not exist.

    Ensures `ResourceNotFoundError` is raised for invalid contact IDs.
    """
    # Mock database query to return None
    mock_db.query.return_value.filter_by.return_value.first.return_value = None

    with pytest.raises(ResourceNotFoundError, match="Contact 99 not found"):
        await contact_service_endorsement.get_contact_endorsements(contact_id=99)
