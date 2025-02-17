"""
Unit tests for the Contact model.

This module tests all aspects of the Contact model, including:
- Object instantiation
- Relationship handling
- Property methods
- Instance methods
- Class methods
- Constraint validation

The tests leverage shared fixtures for mock database sessions, repositories, and test data.

Typical usage example:
    pytest tests/unit/test_db/test_models/test_contact_model.py
"""

import pytest
from unittest.mock import MagicMock
from app.db.models.contact_model import Contact, ContactCreate


@pytest.fixture
def test_contact():
    """
    Create a test Contact instance.

    Returns:
        Contact: A Contact instance with test data.
    """
    return Contact(
        id=1,
        user_id=10,
        contact_name="Test Business",
        email="contact@example.com",
        contact_number="1234567890",
        primary_contact_first_name="John",
        primary_contact_last_name="Doe",
        primary_contact_contact_number="0987654321",
        endorsements_count=3,
        average_rating=4.5,
        verified_endorsements_count=2,
        is_active=True,
    )


def test_contact_creation(test_contact):
    """
    Test that a Contact object is correctly instantiated.

    Args:
        test_contact (Contact): A test contact instance.
    """
    assert test_contact.id == 1
    assert test_contact.user_id == 10
    assert test_contact.contact_name == "Test Business"
    assert test_contact.email == "contact@example.com"
    assert test_contact.contact_number == "1234567890"
    assert test_contact.primary_contact_first_name == "John"
    assert test_contact.primary_contact_last_name == "Doe"
    assert test_contact.primary_contact_contact_number == "0987654321"
    assert test_contact.endorsements_count == 3
    assert test_contact.average_rating == 4.5
    assert test_contact.verified_endorsements_count == 2
    assert test_contact.is_active is True


def test_contact_create():
    """
    Test that the create class method correctly instantiates a Contact from ContactCreate.

    This test ensures that data is correctly mapped from the DTO to the Contact model.
    """
    contact_data = ContactCreate(
        user_id=20,
        contact_name="New Contact",
        primary_contact_first_name="Jane",
        primary_contact_last_name="Smith",
        email="new@example.com",
        contact_number="5551234567",
        primary_contact_contact_number="5557654321",
    )
    new_contact = Contact.create(contact_data)

    assert new_contact.user_id == 20
    assert new_contact.contact_name == "New Contact"
    assert new_contact.primary_contact_first_name == "Jane"
    assert new_contact.primary_contact_last_name == "Smith"
    assert new_contact.email == "new@example.com"
    assert new_contact.contact_number == "5551234567"
    assert new_contact.primary_contact_contact_number == "5557654321"


def test_contact_primary_contact_full_name(test_contact):
    """
    Test that the primary_contact_full_name property returns the correct full name.

    Args:
        test_contact (Contact): A test contact instance.
    """
    assert test_contact.primary_contact_full_name == "John Doe"


def test_contact_add_endorsement(test_contact):
    """
    Test that add_endorsement correctly updates endorsement metrics.

    Args:
        test_contact (Contact): A test contact instance.
    """
    mock_endorsement = MagicMock()
    mock_endorsement.is_verified = True
    mock_endorsement.rating = 5

    initial_count = test_contact.endorsements_count
    initial_verified = test_contact.verified_endorsements_count

    test_contact.add_endorsement(mock_endorsement)

    assert test_contact.endorsements_count == initial_count + 1  # Adjusted expectation
    assert test_contact.verified_endorsements_count == initial_verified + 1


def test_contact_remove_endorsement(test_contact):
    """
    Test that remove_endorsement correctly updates endorsement metrics.

    Args:
        test_contact (Contact): A test contact instance.
    """
    mock_endorsement = MagicMock()
    mock_endorsement.is_verified = True
    mock_endorsement.rating = 5

    test_contact.endorsements = [mock_endorsement]
    test_contact.endorsements_count = 1
    test_contact.verified_endorsements_count = 1
    test_contact.average_rating = 5.0

    test_contact.remove_endorsement(mock_endorsement)

    assert test_contact.endorsements_count == 0
    assert test_contact.verified_endorsements_count == 0
    assert test_contact.average_rating is None


def test_contact_verify_endorsement(test_contact):
    """
    Test that verify_endorsement correctly updates endorsement status.

    Args:
        test_contact (Contact): A test contact instance.
    """
    mock_endorsement = MagicMock()
    mock_endorsement.is_verified = False

    test_contact.endorsements = [mock_endorsement]
    test_contact.verified_endorsements_count = 0

    test_contact.verify_endorsement(mock_endorsement)

    assert mock_endorsement.is_verified is True
    assert test_contact.verified_endorsements_count == 1


def test_contact_verify_endorsement_not_belonging(test_contact):
    """
    Test that verify_endorsement raises an error if the endorsement doesn't belong.

    Args:
        test_contact (Contact): A test contact instance.
    """
    mock_endorsement = MagicMock()
    test_contact.endorsements = []  # The endorsement is not part of this contact

    with pytest.raises(ValueError, match="Endorsement does not belong to this contact"):
        test_contact.verify_endorsement(mock_endorsement)


def test_contact_get_services_by_category(test_contact):
    """
    Test that get_services_by_category correctly filters services.

    Args:
        test_contact (Contact): A test contact instance.
    """
    mock_service1 = MagicMock()
    mock_service1.category_id = 1
    mock_service2 = MagicMock()
    mock_service2.category_id = 2

    test_contact.services = [mock_service1, mock_service2]

    assert test_contact.get_services_by_category(1) == [mock_service1]
    assert test_contact.get_services_by_category(2) == [mock_service2]
    assert test_contact.get_services_by_category(3) == []


def test_contact_is_endorsed_in_community(test_contact):
    """
    Test that is_endorsed_in_community correctly checks for endorsements.

    Args:
        test_contact (Contact): A test contact instance.
    """
    mock_endorsement1 = MagicMock()
    mock_endorsement1.community_id = 1
    mock_endorsement2 = MagicMock()
    mock_endorsement2.community_id = 2

    test_contact.endorsements = [mock_endorsement1, mock_endorsement2]

    assert test_contact.is_endorsed_in_community(1) is True
    assert test_contact.is_endorsed_in_community(2) is True
    assert test_contact.is_endorsed_in_community(3) is False


def test_contact_repr(test_contact):
    """
    Test that the __repr__ method correctly formats the string representation.

    Args:
        test_contact (Contact): A test contact instance.
    """
    assert repr(test_contact) == "Contact(id=1, name=Test Business)"


def test_contact_update_average_rating(test_contact):
    """
    Test that _update_average_rating correctly calculates and updates average rating.
    """
    # No endorsements -> average_rating should be None
    test_contact.endorsements = []
    test_contact._update_average_rating()
    assert test_contact.average_rating is None

    # Add endorsements with ratings
    mock_endorsement1 = MagicMock()
    mock_endorsement1.rating = 5
    mock_endorsement2 = MagicMock()
    mock_endorsement2.rating = 3

    test_contact.endorsements = [mock_endorsement1, mock_endorsement2]
    test_contact._update_average_rating()

    assert test_contact.average_rating == 4.0  # (5+3)/2


def test_contact_verify_endorsement_already_verified(test_contact):
    """
    Test that verify_endorsement does not increment if already verified.
    """
    mock_endorsement = MagicMock()
    mock_endorsement.is_verified = True

    # Ensure the endorsement is part of test_contact's endorsements
    test_contact.endorsements = [mock_endorsement]
    initial_verified = test_contact.verified_endorsements_count

    test_contact.verify_endorsement(mock_endorsement)

    # Should NOT increment verified count
    assert test_contact.verified_endorsements_count == initial_verified


def test_contact_verify_endorsement_first_time(test_contact):
    """
    Test that verify_endorsement correctly increments verified count when first verified.
    """
    mock_endorsement = MagicMock()
    mock_endorsement.is_verified = False

    # Ensure the endorsement is part of test_contact's endorsements
    test_contact.endorsements = [mock_endorsement]
    initial_verified = test_contact.verified_endorsements_count

    test_contact.verify_endorsement(mock_endorsement)

    assert mock_endorsement.is_verified is True
    assert test_contact.verified_endorsements_count == initial_verified + 1


def test_contact_update_average_rating_with_ratings(test_contact):
    """
    Test that _update_average_rating correctly calculates and updates average rating
    when valid ratings are present.
    """
    mock_endorsement1 = MagicMock()
    mock_endorsement1.rating = 5
    mock_endorsement2 = MagicMock()
    mock_endorsement2.rating = 3

    test_contact.endorsements = [mock_endorsement1, mock_endorsement2]
    test_contact._update_average_rating()

    assert test_contact.average_rating == 4.0  # (5+3)/2


def test_contact_update_average_rating_no_ratings(test_contact):
    """
    Test that _update_average_rating sets average_rating to None when no rated endorsements exist.
    """
    test_contact.endorsements = []  # No endorsements at all
    test_contact._update_average_rating()

    assert test_contact.average_rating is None


def test_contact_update_average_rating_all_none_ratings(test_contact):
    """
    Test that _update_average_rating sets average_rating to None when all ratings are None.
    """
    mock_endorsement1 = MagicMock()
    mock_endorsement1.rating = None
    mock_endorsement2 = MagicMock()
    mock_endorsement2.rating = None

    test_contact.endorsements = [mock_endorsement1, mock_endorsement2]
    test_contact._update_average_rating()

    assert test_contact.average_rating is None
