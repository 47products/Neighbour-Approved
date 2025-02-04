"""
Unit tests for the BaseUserService module.

This module contains tests to validate the core user retrieval and update
operations implemented in the BaseUserService class.

Classes:
    TestBaseUserService: Test cases for the BaseUserService class.
"""

import pytest
from unittest.mock import AsyncMock
from app.services.base import BaseUserService
from app.db.models.user_model import User


class TestBaseUserService:
    """
    Test cases for the BaseUserService class.
    """

    @pytest.fixture
    def service(self, dummy_db):
        """
        Provide a BaseUserService instance with a mocked database.

        Args:
            dummy_db: Mocked database session fixture.

        Returns:
            BaseUserService: Instance of BaseUserService with a mock database.
        """
        return BaseUserService(db=dummy_db)

    @pytest.mark.asyncio
    async def test_get_user_existing(self, service):
        """
        Test retrieving an existing user.

        Ensures that get_user() returns a user object when a valid user_id
        is provided.

        Scenario:
            - A mock user exists in the database.
            - Calling get_user() should return the user.

        Expected Outcome:
            - The returned user matches the expected user.
        """
        mock_user = AsyncMock(spec=User)
        mock_user.id = 1
        service.get = AsyncMock(return_value=mock_user)

        user = await service.get_user(1)

        assert user is not None
        assert user.id == 1
        service.get.assert_called_once_with(1)
