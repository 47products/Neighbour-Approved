"""
Unit tests for ContactServiceService.

This test suite verifies contact-to-service association logic, ensuring:
- Services can be added and removed from contacts.
- Errors are correctly raised for non-existent contacts or services.
- Business rules (such as max service limit) are enforced.

Test Coverage:
- `add_service()`
- `remove_service()`

Typical usage example:
    pytest tests/unit/test_services/test_contact_service/test_contact_service_service.py
"""

import pytest
from unittest.mock import MagicMock
from app.services.contact_service.service import ContactServiceService
from app.services.service_exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


@pytest.mark.asyncio
async def test_add_service_success(
    contact_service_service, dummy_db, mock_contact, mock_service
):
    """
    Test adding a service to a contact successfully.
    """
    mock_contact.services = []
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_contact,
        mock_service,
    ]

    result = await contact_service_service.add_service(contact_id=1, service_id=10)

    assert result is True
    assert mock_service in mock_contact.services
    dummy_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_service_already_exists(
    contact_service_service, dummy_db, mock_contact, mock_service
):
    """
    Test that adding an already assigned service returns False.
    """
    mock_contact.services = [mock_service]
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_contact,
        mock_service,
    ]

    result = await contact_service_service.add_service(contact_id=1, service_id=10)

    assert result is False
    dummy_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_service_contact_not_found(
    contact_service_service, dummy_db, mock_service
):
    """
    Test that adding a service to a non-existent contact raises ResourceNotFoundError.
    """
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        None,
        mock_service,
    ]

    with pytest.raises(ResourceNotFoundError, match="Contact 1 not found"):
        await contact_service_service.add_service(contact_id=1, service_id=10)


@pytest.mark.asyncio
async def test_add_service_service_not_found(
    contact_service_service, dummy_db, mock_contact
):
    """
    Test that adding a non-existent service raises ResourceNotFoundError.
    """
    mock_contact.services = []
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_contact,
        None,
    ]

    with pytest.raises(ResourceNotFoundError, match="Service 10 not found"):
        await contact_service_service.add_service(contact_id=1, service_id=10)


@pytest.mark.asyncio
async def test_add_service_exceeds_limit(
    contact_service_service, dummy_db, mock_contact, mock_service
):
    """
    Test that adding a service fails if the max service limit is reached.
    """
    mock_contact.services = [
        MagicMock() for _ in range(ContactServiceService.MAX_SERVICES)
    ]
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_contact,
        mock_service,
    ]

    with pytest.raises(
        BusinessRuleViolationError,
        match="Contact has reached the maximum service limit",
    ):
        await contact_service_service.add_service(contact_id=1, service_id=10)


@pytest.mark.asyncio
async def test_remove_service_success(
    contact_service_service, dummy_db, mock_contact, mock_service
):
    """
    Test removing a service from a contact successfully.
    """
    mock_contact.services = [mock_service]
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_contact,
        mock_service,
    ]

    result = await contact_service_service.remove_service(contact_id=1, service_id=10)

    assert result is True
    assert mock_service not in mock_contact.services
    dummy_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_service_not_found(
    contact_service_service, dummy_db, mock_contact, mock_service
):
    """
    Test that removing a service that is not associated with the contact returns False.
    """
    mock_contact.services = []
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_contact,
        mock_service,
    ]

    result = await contact_service_service.remove_service(contact_id=1, service_id=10)

    assert result is False
    dummy_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_remove_service_contact_not_found(
    contact_service_service, dummy_db, mock_service
):
    """
    Test that removing a service from a non-existent contact raises ResourceNotFoundError.
    """
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        None,
        mock_service,
    ]

    with pytest.raises(ResourceNotFoundError, match="Contact 1 not found"):
        await contact_service_service.remove_service(contact_id=1, service_id=10)


@pytest.mark.asyncio
async def test_remove_service_service_not_found(
    contact_service_service, dummy_db, mock_contact
):
    """
    Test that removing a non-existent service raises ResourceNotFoundError.
    """
    mock_contact.services = [MagicMock()]
    dummy_db.query.return_value.filter_by.return_value.first.side_effect = [
        mock_contact,
        None,
    ]

    with pytest.raises(ResourceNotFoundError, match="Service 10 not found"):
        await contact_service_service.remove_service(contact_id=1, service_id=10)
