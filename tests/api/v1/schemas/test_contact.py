"""
Test cases for the Contact schemas.

This module contains test cases for the ContactCreate, ContactUpdate, ContactResponse, and ContactInDB schemas.

Classes:
    TestContactCreate: Test cases for the ContactCreate schema.
    TestContactResponse: Test cases for the ContactResponse schema.
    TestContactUpdate: Test cases for the ContactUpdate schema.
    TestContactInDB: Test cases for the ContactInDB schema.
"""

import pytest
from app.api.v1.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactInDB,
)


class TestContactCreate:
    """
    Test cases for the ContactCreate schema.
    """

    @pytest.mark.parametrize(
        "contact_data",
        [
            {
                "contact_name": "John's Plumbing",
                "email": "contact@example.com",
                "contact_number": "+14155552671",
                "primary_contact_first_name": "John",
                "primary_contact_last_name": "Doe",
                "primary_contact_number": "+14155552671",
                "categories": "Plumbing",
                "services": "Pipe repair",
                "user_id": 1,
            },
        ],
    )
    def test_valid_contact_create(self, contact_data):
        """
        Validate the successful creation of a ContactCreate instance with valid data.
        """
        contact = ContactCreate(**contact_data)
        assert contact.contact_name == contact_data["contact_name"]
        assert contact.email == contact_data["email"]
        assert contact.categories == contact_data["categories"]


class TestContactResponse:
    """
    Test cases for the ContactResponse schema.
    """

    def test_response_schema(self):
        """
        Validate the correct population of the ContactResponse schema.
        """
        contact_data = {
            "id": 1,
            "contact_name": "John's Plumbing",
            "email": "contact@example.com",
            "contact_number": "+1234567890",
            "primary_contact_first_name": "John",
            "primary_contact_last_name": "Doe",
            "primary_contact_contact_number": "+9876543210",
            "categories": "Plumbing",
            "services": "Pipe repair",
            "endorsements": 10,
            "user_id": 1,
        }
        contact_response = ContactResponse(**contact_data)
        assert contact_response.id == 1
        assert contact_response.contact_name == "John's Plumbing"


class TestContactUpdate:
    """
    Test cases for the ContactUpdate schema.
    """

    def test_partial_update(self):
        """
        Validate updating only a subset of ContactUpdate fields.
        """
        update_data = {
            "contact_name": "Updated Plumbing",
            "services": "New pipe repair",
        }
        contact_update = ContactUpdate(**update_data)
        assert contact_update.contact_name == "Updated Plumbing"
        assert contact_update.services == "New pipe repair"
        assert contact_update.email is None


class TestContactInDB:
    """
    Test cases for the ContactInDB schema.
    """

    def test_in_db_schema(self):
        """
        Validate the creation of a ContactInDB instance with all required fields.
        """
        in_db_data = {
            "id": 1,
            "contact_name": "John's Plumbing",
            "email": "contact@example.com",
            "contact_number": "+1234567890",
            "primary_contact_first_name": "John",
            "primary_contact_last_name": "Doe",
            "primary_contact_contact_number": "+9876543210",
            "categories": "Plumbing",
            "services": "Pipe repair",
            "endorsements": 10,
            "user_id": 1,
        }
        contact_in_db = ContactInDB(**in_db_data)
        assert contact_in_db.contact_name == "John's Plumbing"
        assert contact_in_db.user_id == 1
