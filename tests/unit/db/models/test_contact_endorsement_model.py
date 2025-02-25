"""
Unit tests for the ContactEndorsement model.

This module tests all aspects of the ContactEndorsement model, including:
- Object instantiation
- Relationship handling
- Property methods
- Instance methods
- Class methods
- Constraint validation

The tests leverage shared fixtures for mock database sessions, repositories, and test data.

Typical usage example:
    pytest tests/unit/test_db/test_models/test_contact_endorsement_model.py
"""

import pytest
from unittest.mock import MagicMock
from app.db.models.contact_endorsement_model import (
    ContactEndorsement,
    EndorsementCreate,
)


@pytest.fixture
def test_endorsement():
    """
    Create a test ContactEndorsement instance.

    Returns:
        ContactEndorsement: A test endorsement instance.
    """
    return ContactEndorsement(
        id=1,
        contact_id=100,
        user_id=200,
        community_id=300,
        endorsed=True,
        rating=4,
        comment="Great service!",
        is_verified=True,
        verification_notes="Checked by admin",
        is_public=True,
    )


def test_contact_endorsement_creation(test_endorsement):
    """
    Test that a ContactEndorsement object is correctly instantiated.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    assert test_endorsement.id == 1
    assert test_endorsement.contact_id == 100
    assert test_endorsement.user_id == 200
    assert test_endorsement.community_id == 300
    assert test_endorsement.endorsed is True
    assert test_endorsement.rating == 4
    assert test_endorsement.comment == "Great service!"
    assert test_endorsement.is_verified is True
    assert test_endorsement.verification_notes == "Checked by admin"
    assert test_endorsement.is_public is True


def test_contact_endorsement_create():
    """
    Test that the create class method correctly instantiates a ContactEndorsement from EndorsementCreate.

    This test ensures that data is correctly mapped from the DTO to the ContactEndorsement model.
    """
    endorsement_data = EndorsementCreate(
        contact_id=101,
        user_id=201,
        community_id=301,
        endorsed=False,
        rating=5,
        comment="Outstanding work!",
        is_public=False,
    )
    new_endorsement = ContactEndorsement.create(endorsement_data)

    assert new_endorsement.contact_id == 101
    assert new_endorsement.user_id == 201
    assert new_endorsement.community_id == 301
    assert new_endorsement.endorsed is False
    assert new_endorsement.rating == 5
    assert new_endorsement.comment == "Outstanding work!"
    assert new_endorsement.is_public is False


def test_contact_endorsement_update_rating(test_endorsement):
    """
    Test that update_rating correctly updates the rating and optional comment.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    test_endorsement.update_rating(5, "Excellent service!")

    assert test_endorsement.rating == 5
    assert test_endorsement.comment == "Excellent service!"


def test_contact_endorsement_update_rating_invalid(test_endorsement):
    """
    Test that update_rating raises a ValueError for an invalid rating.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
        test_endorsement.update_rating(6)  # Invalid rating


def test_contact_endorsement_update_rating_none(test_endorsement):
    """
    Test that update_rating allows setting rating to None.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    test_endorsement.update_rating(None)

    assert test_endorsement.rating is None


def test_contact_endorsement_verification_status_unverified(test_endorsement):
    """
    Test that verification_status returns 'Unverified' when the endorsement is not verified.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    test_endorsement.is_verified = False
    assert test_endorsement.verification_status == "Unverified"


def test_contact_endorsement_verification_status_verified(test_endorsement):
    """
    Test that verification_status returns 'Verified' when the endorsement is verified.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    test_endorsement.is_verified = True
    test_endorsement.verification_notes = None
    assert test_endorsement.verification_status == "Verified"


def test_contact_endorsement_verification_status_with_notes(test_endorsement):
    """
    Test that verification_status returns notes when verification_notes exist.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    assert (
        test_endorsement.verification_status == "Verified with notes: Checked by admin"
    )


def test_contact_endorsement_formatted_rating(test_endorsement):
    """
    Test that formatted_rating correctly returns a formatted rating string.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    assert test_endorsement.formatted_rating == "4/5 stars"


def test_contact_endorsement_formatted_rating_none(test_endorsement):
    """
    Test that formatted_rating returns None when no rating is set.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    test_endorsement.rating = None
    assert test_endorsement.formatted_rating is None


def test_contact_endorsement_repr(test_endorsement):
    """
    Test that the __repr__ method correctly formats the string representation.

    Args:
        test_endorsement (ContactEndorsement): A test endorsement instance.
    """
    assert (
        repr(test_endorsement)
        == "ContactEndorsement(id=1, contact_id=100, user_id=200)"
    )
