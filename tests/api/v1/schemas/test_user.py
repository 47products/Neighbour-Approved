"""
Test cases for the User schemas.

This module contains test cases for the UserCreate, UserUpdate, UserResponse, and UserInDB schemas.

Classes:
    TestUserCreate: Test cases for the UserCreate schema.
    TestUserResponse: Test cases for the UserResponse schema.
    TestUserUpdate: Test cases for the UserUpdate schema.
    TestUserInDB: Test cases for the UserInDB schema.
"""

from datetime import datetime, timezone
import pytest
from app.api.v1.schemas.user import UserCreate, UserUpdate, UserResponse, UserInDB


class TestUserCreate:
    """
    Test cases for the UserCreate schema.
    """

    @pytest.mark.parametrize(
        "user_data",
        [
            {
                "email": "testuser@example.com",
                "password": "StrongPass123!",
                "first_name": "Test",
                "last_name": "User",
                "mobile_number": "+14155552671",
                "postal_address": "123 Postal St",
                "physical_address": "456 Physical St",
                "country": "USA",
            },
        ],
    )
    def test_valid_user_create(self, user_data):
        """
        Validate the successful creation of a UserCreate instance with valid data.
        """
        user = UserCreate(**user_data)
        assert user.email == user_data["email"]
        assert user.first_name == user_data["first_name"]
        assert user.last_name == user_data["last_name"]

    def test_invalid_mobile_number(self):
        """
        Validate that an invalid mobile number raises a ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            UserCreate(
                email="invaliduser@example.com",
                password="AnotherStrongPass!",
                first_name="Invalid",
                last_name="User",
                mobile_number="InvalidNumber",
                postal_address="123 Postal St",
                physical_address="456 Physical St",
                country="USA",
            )
        assert "Phone number must be a valid international format" in str(
            exc_info.value
        )


class TestUserResponse:
    """
    Test cases for the UserResponse schema.
    """

    def test_response_schema(self):
        """
        Validate the correct population of the UserResponse schema.
        """
        user_data = {
            "id": 1,
            "email": "response@example.com",
            "first_name": "Response",
            "last_name": "Test",
            "mobile_number": "+14155552671",
            "postal_address": "Postal Address",
            "physical_address": "Physical Address",
            "country": "USA",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "contacts": [],
        }
        user_response = UserResponse(**user_data)
        assert user_response.id == 1
        assert user_response.email == "response@example.com"


class TestUserUpdate:
    """
    Test cases for the UserUpdate schema.
    """

    def test_partial_update(self):
        """
        Validate updating only a subset of UserUpdate fields.
        """
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
        }
        user_update = UserUpdate(**update_data)
        assert user_update.first_name == "Updated"
        assert user_update.last_name == "User"
        assert user_update.email is None


class TestUserInDB:
    """
    Test cases for the UserInDB schema.
    """

    def test_in_db_schema(self):
        """
        Validate the creation of a UserInDB instance with all required fields.
        """
        in_db_data = {
            "id": 1,
            "email": "indb@example.com",
            "password": "hashed_password",
            "first_name": "DB",
            "last_name": "User",
            "mobile_number": "+14155552671",
            "postal_address": "Postal Address",
            "physical_address": "Physical Address",
            "country": "USA",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_active": True,
            "contacts": [],
        }
        user_in_db = UserInDB(**in_db_data)
        assert user_in_db.email == "indb@example.com"
        assert user_in_db.password == "hashed_password"
