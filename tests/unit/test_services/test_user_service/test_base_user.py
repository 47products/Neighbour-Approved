"""
Unit tests for the BaseUserService class.

This test module verifies the core user retrieval and update operations
provided by the BaseUserService class. The tests ensure that business logic,
error handling, and database interactions function as expected.

Tested Methods:
- get_user: Retrieve a user by ID.
- update_user: Update user information with transaction handling.
- get_user_communities: Fetch communities associated with a user.
- _validate_update: Validate user update data.

Dependencies:
    - pytest
    - pytest-asyncio
    - unittest.mock

Example usage:
    pytest tests/unit/test_services/test_base_user.py
"""

import pytest
from unittest.mock import AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1.schemas.user_schema import UserUpdate
from app.db.models.community_model import Community
from app.db.models.user_model import User
from app.services.service_exceptions import (
    ResourceNotFoundError,
    ValidationError,
    BusinessRuleViolationError,
)


@pytest.mark.asyncio
async def test_get_user_success(base_user_service, mock_user):
    """Test retrieving an existing user successfully."""
    base_user_service.get = AsyncMock(return_value=mock_user)

    user = await base_user_service.get_user(user_id=1)

    assert user == mock_user
    base_user_service.get.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_user_not_found(base_user_service):
    """Test retrieving a non-existent user raises ResourceNotFoundError."""
    base_user_service.get = AsyncMock(return_value=None)

    with pytest.raises(ResourceNotFoundError, match="User 1 not found"):
        await base_user_service.get_user(user_id=1)


@pytest.mark.asyncio
async def test_update_user_success(base_user_service, mock_user, dummy_db):
    """Test successfully updating user information."""
    # Setup mocks
    base_user_service.get_user = AsyncMock(return_value=mock_user)
    base_user_service._validate_update = AsyncMock()

    # Create update data
    update_data = UserUpdate(email="new@example.com")

    # Execute update
    result = await base_user_service.update_user(user_id=1, data=update_data)

    # Verify results
    assert result == mock_user
    assert result.email == "new@example.com"

    # Verify method calls
    base_user_service.get_user.assert_awaited_once_with(1)
    base_user_service._validate_update.assert_awaited_once()
    dummy_db.commit.assert_awaited_once()
    dummy_db.refresh.assert_awaited_once_with(mock_user)


@pytest.mark.asyncio
async def test_update_user_not_found(base_user_service):
    """Test updating a non-existent user raises ResourceNotFoundError."""
    base_user_service.get_user = AsyncMock(
        side_effect=ResourceNotFoundError("User 1 not found")
    )

    update_data = UserUpdate(email="new@example.com")

    with pytest.raises(ResourceNotFoundError, match="User 1 not found"):
        await base_user_service.update_user(user_id=1, data=update_data)


@pytest.mark.asyncio
async def test_update_user_validation_error(base_user_service, mock_user):
    """Test updating a user with invalid data raises ValidationError."""
    base_user_service.get_user = AsyncMock(return_value=mock_user)
    base_user_service._validate_update = AsyncMock(
        side_effect=ValidationError("Invalid email")
    )

    update_data = UserUpdate(email="invalid@example.com")

    with pytest.raises(ValidationError, match="Invalid email"):
        await base_user_service.update_user(user_id=1, data=update_data)


@pytest.mark.asyncio
async def test_update_user_sqlalchemy_error(base_user_service, mock_user, dummy_db):
    """Test handling of SQLAlchemy errors during user update."""
    base_user_service.get_user = AsyncMock(return_value=mock_user)
    base_user_service._validate_update = AsyncMock(return_value=None)
    dummy_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))
    dummy_db.rollback = AsyncMock()

    update_data = UserUpdate(email="new@example.com")

    with pytest.raises(BusinessRuleViolationError, match="Failed to update user 1"):
        await base_user_service.update_user(user_id=1, data=update_data)

    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_communities_success(base_user_service, mock_user):
    """Test retrieving a user's associated communities successfully."""
    mock_user.communities = [Community(id=1, name="Test Community")]
    base_user_service.get_user = AsyncMock(return_value=mock_user)

    result = await base_user_service.get_user_communities(user_id=1)

    assert result == mock_user.communities
    base_user_service.get_user.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_user_communities_not_found(base_user_service):
    """Test retrieving communities for a non-existent user raises an error."""
    base_user_service.get_user = AsyncMock(
        side_effect=ResourceNotFoundError("User 1 not found")
    )

    with pytest.raises(ResourceNotFoundError, match="User 1 not found"):
        await base_user_service.get_user_communities(user_id=1)


@pytest.mark.asyncio
async def test_validate_update_no_email(base_user_service, mock_user):
    """
    Test that if no email is provided in update data, _validate_update does nothing.
    (Assumes email is optional in UserUpdate.)
    """
    # Create update data without email (i.e. default values)
    update_data = UserUpdate()
    base_user_service._repository.get_by_email = AsyncMock()

    # No exception should be raised and no call should be made to get_by_email.
    await base_user_service._validate_update(mock_user, update_data)
    base_user_service._repository.get_by_email.assert_not_called()


@pytest.mark.asyncio
async def test_validate_update_same_email(base_user_service, mock_user):
    """
    Test that if the new email is the same as the current email, no uniqueness check is done.
    """
    update_data = UserUpdate(email=mock_user.email)
    base_user_service._repository.get_by_email = AsyncMock()

    await base_user_service._validate_update(mock_user, update_data)
    base_user_service._repository.get_by_email.assert_not_called()


@pytest.mark.asyncio
async def test_validate_update_new_email_no_conflict(base_user_service, mock_user):
    """
    Test that if the new email is different and the repository returns None,
    _validate_update passes without error.
    """
    new_email = "unique@example.com"
    update_data = UserUpdate(email=new_email)
    base_user_service._repository.get_by_email = AsyncMock(return_value=None)

    await base_user_service._validate_update(mock_user, update_data)
    base_user_service._repository.get_by_email.assert_awaited_once_with(new_email)


@pytest.mark.asyncio
async def test_validate_update_new_email_conflict(base_user_service, mock_user):
    """
    Test that if the new email is different and the repository returns a different user,
    _validate_update raises a ValidationError.
    """
    new_email = "conflict@example.com"
    update_data = UserUpdate(email=new_email)
    # Create a conflicting user with a different id.
    conflicting_user = User(id=999, email=new_email)
    base_user_service._repository.get_by_email = AsyncMock(
        return_value=conflicting_user
    )

    with pytest.raises(ValidationError, match="Email already registered"):
        await base_user_service._validate_update(mock_user, update_data)


@pytest.mark.asyncio
async def test_validate_update_new_email_same_user(base_user_service, mock_user):
    """
    Test that if the repository returns the same user (same id), no exception is raised.
    """
    new_email = "same@example.com"
    update_data = UserUpdate(email=new_email)
    # Simulate repository returning the same user.
    same_user = mock_user
    same_user.email = new_email
    base_user_service._repository.get_by_email = AsyncMock(return_value=same_user)

    await base_user_service._validate_update(mock_user, update_data)


@pytest.mark.asyncio
async def test_process_filters_active(base_user_service):
    """
    Test that process_filters converts a 'status' of 'active' to is_active True.
    """
    filters = {"status": "active", "other": "value"}
    processed = await base_user_service.process_filters(filters)

    assert processed.get("is_active") is True
    assert "status" not in processed
    assert processed.get("other") == "value"


@pytest.mark.asyncio
async def test_process_filters_inactive(base_user_service):
    """
    Test that process_filters converts a 'status' of 'inactive' to is_active False.
    """
    filters = {"status": "inactive", "other": "value"}
    processed = await base_user_service.process_filters(filters)

    assert processed.get("is_active") is False
    assert "status" not in processed
    assert processed.get("other") == "value"


@pytest.mark.asyncio
async def test_process_filters_no_status(base_user_service):
    """
    Test that process_filters returns the original filters if no status key is present.
    """
    filters = {"other": "value"}
    processed = await base_user_service.process_filters(filters)

    assert processed == filters
