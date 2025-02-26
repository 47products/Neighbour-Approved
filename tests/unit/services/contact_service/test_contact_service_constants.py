"""
Unit tests for the Contact Service Constants module.

This test suite verifies the integrity of constants used in the contact service,
including constraints, restricted words, and required fields.

Test Coverage:
- Ensures numeric constraints match expected limits.
- Validates the list of restricted words.
- Confirms required fields are correctly defined.

Typical usage example:
    pytest tests/unit/test_contact_service_constants.py
"""

from app.services.contact_service.constants import (
    MAX_CONTACTS_FREE,
    MAX_SERVICES,
    MAX_CATEGORIES,
    RESTRICTED_WORDS,
    REQUIRED_FIELDS,
)


def test_max_contacts_free():
    """
    Validate that the maximum number of contacts allowed for a free user is correct.
    """
    assert isinstance(MAX_CONTACTS_FREE, int), "MAX_CONTACTS_FREE should be an integer"
    assert MAX_CONTACTS_FREE == 10, "Unexpected value for MAX_CONTACTS_FREE"


def test_max_services(test_config):
    """
    Ensure that the maximum number of services a contact can have is correctly defined.
    """
    assert isinstance(MAX_SERVICES, int), "MAX_SERVICES should be an integer"
    assert MAX_SERVICES == test_config["max_services"]


def test_max_categories():
    """
    Verify that the maximum number of categories for a contact is correctly set.
    """
    assert isinstance(MAX_CATEGORIES, int), "MAX_CATEGORIES should be an integer"
    assert MAX_CATEGORIES == 5, "Unexpected value for MAX_CATEGORIES"


def test_restricted_words():
    """
    Check that the set of restricted words is correctly defined and immutable.
    """
    assert isinstance(RESTRICTED_WORDS, set), "RESTRICTED_WORDS should be a set"
    assert RESTRICTED_WORDS == {
        "admin",
        "system",
        "support",
        "test",
    }, "Unexpected restricted words"
    assert "admin" in RESTRICTED_WORDS, "'admin' should be a restricted word"
    assert "test" in RESTRICTED_WORDS, "'test' should be a restricted word"
    assert (
        "random" not in RESTRICTED_WORDS
    ), "'random' should not be in restricted words"


def test_required_fields():
    """
    Confirm that the set of required fields for contact creation is correctly defined.
    """
    expected_fields = {
        "contact_name",
        "primary_contact_first_name",
        "primary_contact_last_name",
        "email",
    }
    assert isinstance(REQUIRED_FIELDS, set), "REQUIRED_FIELDS should be a set"
    assert REQUIRED_FIELDS == expected_fields, "Unexpected required fields"
    assert "email" in REQUIRED_FIELDS, "'email' should be a required field"
    assert (
        "contact_name" in REQUIRED_FIELDS
    ), "'contact_name' should be a required field"
    assert "phone" not in REQUIRED_FIELDS, "'phone' should not be in required fields"
