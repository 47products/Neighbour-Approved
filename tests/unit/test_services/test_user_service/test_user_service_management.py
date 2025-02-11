"""
Unit tests for the UserManagementService module.

This module tests the UserManagementService class, which is responsible for managing
user account creation and deletion operations within the application. The tests cover:
  - Successful user creation.
  - Duplicate email detection resulting in a DuplicateResourceError.
  - Exception handling in user creation (e.g. SQLAlchemy errors).
  - Successful deletion of a user.
  - Access denial when deletion is not permitted.
  - Exception handling in user deletion.
  - The internal _can_delete_user method, which enforces business rules for deletion.
    This includes checking:
      * Whether the user owns any active communities.
      * Whether the user has any active contacts.
      * Whether the user has pending endorsements.
      * Whether the user holds any active system roles.
    If any of these conditions hold, deletion is blocked.

To run the tests, use:
    pytest tests/unit/test_services/test_user_service/test_user_management.py

Dependencies:
    - pytest for testing.
    - AsyncMock and MagicMock from unittest.mock for simulating asynchronous operations.
    - The UserManagementService class, UserCreate schema, User model, and related exception classes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.services.user_service.user_service_user_management import UserManagementService
from app.api.v1.schemas.user_schema import UserCreate
from app.db.models.user_model import User
from app.services.service_exceptions import (
    DuplicateResourceError,
    AccessDeniedError,
)


# --- Fixture to add a model_copy method to UserCreate if not already present ---
# This avoids setting an instance attribute, which is disallowed by Pydantic.
@pytest.fixture(autouse=True)
def add_model_copy(monkeypatch):
    from app.api.v1.schemas.user_schema import UserCreate

    monkeypatch.setattr(
        UserCreate, "model_copy", lambda self: self.__class__(**self.model_dump())
    )


@pytest.mark.asyncio
async def test_create_user_success(dummy_db):
    """
    Test that create_user successfully creates a new user when no duplicate email exists.

    Workflow:
      1. The repository's get_by_email returns None.
      2. The security service's hash_password returns a hashed password.
      3. The inherited create method is patched to return a new User instance.
      4. The user data (obtained via model_copy) is updated with the hashed password.

    Expected Outcome:
      - The newly created user is returned.
      - get_by_email is awaited with the provided email.
      - hash_password is awaited with the plaintext password.
      - create is awaited with user data in which the password has been updated.
    """
    # Arrange
    data = UserCreate(
        email="user@example.com",
        password="PlainPassword123",
        first_name="John",
        last_name="Doe",
    )
    # data.model_copy() will now use the patched method from our fixture.
    new_user = User(id=1, email="user@example.com", is_active=True)

    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=None)

    fake_security = AsyncMock()
    fake_security.hash_password.return_value = "hashedpassword"

    service = UserManagementService(dummy_db, fake_security)
    service._repository = mock_repository
    # Patch the inherited create method to simulate creation.
    service.create = AsyncMock(return_value=new_user)

    # Act
    result = await service.create_user(data)

    # Assert
    # Build the expected data: the copy with the password updated to the hashed value.
    expected_data = data.model_copy()
    expected_data.password = "hashedpassword"
    assert result == new_user
    mock_repository.get_by_email.assert_awaited_once_with(data.email)
    fake_security.hash_password.assert_awaited_once_with(data.password)
    service.create.assert_awaited_once_with(expected_data)


@pytest.mark.asyncio
async def test_create_user_duplicate(dummy_db):
    """
    Test that create_user raises DuplicateResourceError if a user with the given email already exists.

    The repository's get_by_email method returns an existing user, so the method should raise an error.
    """
    data = UserCreate(
        email="duplicate@example.com",
        password="PlainPassword123",
        first_name="Jane",
        last_name="Doe",
    )
    # Ensure model_copy works (provided by our fixture)
    existing_user = User(id=2, email="duplicate@example.com", is_active=True)

    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=existing_user)

    fake_security = AsyncMock()
    # The security service should not be called if a duplicate exists.

    service = UserManagementService(dummy_db, fake_security)
    service._repository = mock_repository

    with pytest.raises(DuplicateResourceError, match="Email already registered"):
        await service.create_user(data)


@pytest.mark.asyncio
async def test_create_user_sqlalchemy_error(dummy_db):
    """
    Test that create_user propagates SQLAlchemyError when a database error occurs during creation.

    After validation passes, if the inherited create method (or subsequent commit)
    raises SQLAlchemyError, the error is propagated.
    """
    data = UserCreate(
        email="user2@example.com",
        password="PlainPassword123",
        first_name="Alice",
        last_name="Smith",
    )

    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=None)

    fake_security = AsyncMock()
    fake_security.hash_password.return_value = "hashedpassword"

    service = UserManagementService(dummy_db, fake_security)
    service._repository = mock_repository
    # Patch create to raise SQLAlchemyError.
    service.create = AsyncMock(side_effect=SQLAlchemyError("DB error"))

    with pytest.raises(SQLAlchemyError, match="DB error"):
        await service.create_user(data)


@pytest.mark.asyncio
async def test_delete_user_success(dummy_db, mock_user):
    """
    Test that delete_user successfully deletes a user.

    This test simulates a successful deletion by patching:
      - get_user to return the user.
      - _can_delete_user to return True.
      - delete (an inherited method) to call commit and return True.

    Expected Outcome:
      - The method returns True.
      - The delete method is awaited with the user's id.
      - The database commit method is called exactly once.
    """
    service = UserManagementService(dummy_db, None)
    service.get_user = AsyncMock(return_value=mock_user)
    service._can_delete_user = AsyncMock(return_value=True)

    # Define a fake delete method that simulates deletion and calls commit.
    async def fake_delete(user_id: int) -> bool:
        await dummy_db.commit()  # Simulate the deletion process performing a commit.
        return True

    service.delete = AsyncMock(side_effect=fake_delete)
    dummy_db.commit = AsyncMock()

    result = await service.delete_user(mock_user.id)
    assert result is True
    service.delete.assert_awaited_once_with(mock_user.id)
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_failure(dummy_db, mock_user):
    """
    Test that delete_user returns False when the deletion operation fails.

    Workflow:
      1. get_user returns the user.
      2. _can_delete_user returns True (indicating deletion is allowed).
      3. The inherited delete method returns False (simulating a deletion failure).
      4. The code skips logging "user_deleted" and returns False.

    Expected Outcome:
      - The method returns False.
      - The delete method is awaited with the correct user id.
      - The logger is not called for a successful deletion.
      - No database commit is performed.
    """
    service = UserManagementService(dummy_db, None)
    service.get_user = AsyncMock(return_value=mock_user)
    service._can_delete_user = AsyncMock(return_value=True)
    # Simulate deletion failure by having delete return False.
    service.delete = AsyncMock(return_value=False)
    dummy_db.commit = AsyncMock()

    result = await service.delete_user(mock_user.id)
    assert result is False
    service.delete.assert_awaited_once_with(mock_user.id)
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_user_access_denied(dummy_db, mock_user):
    """
    Test that delete_user raises AccessDeniedError when _can_delete_user returns False.

    This simulates that the user cannot be deleted due to business rule violations.
    """
    service = UserManagementService(dummy_db, None)
    service.get_user = AsyncMock(return_value=mock_user)
    service._can_delete_user = AsyncMock(return_value=False)

    with pytest.raises(
        AccessDeniedError, match="Cannot delete user with active communities"
    ):
        await service.delete_user(mock_user.id)


@pytest.mark.asyncio
async def test_delete_user_sqlalchemy_error(dummy_db, mock_user):
    """
    Test that delete_user propagates SQLAlchemyError if deletion fails.

    The test patches delete to raise SQLAlchemyError after _can_delete_user passes.
    """
    service = UserManagementService(dummy_db, None)
    service.get_user = AsyncMock(return_value=mock_user)
    service._can_delete_user = AsyncMock(return_value=True)
    service.delete = AsyncMock(side_effect=SQLAlchemyError("Deletion failed"))

    with pytest.raises(SQLAlchemyError, match="Deletion failed"):
        await service.delete_user(mock_user.id)


@pytest.mark.asyncio
async def test_can_delete_user_blocked_by_communities(
    dummy_db, mock_user, dummy_community
):
    """
    Test that _can_delete_user returns False when the user owns any active communities.

    The test simulates an active community by directly assigning to the user's
    owned_communities (via the __dict__) a list containing a DummyCommunity instance with active=True.

    Expected Outcome:
        - _can_delete_user returns False.
    """
    # Create an active dummy community and bypass SQLAlchemy instrumentation.
    mock_user.__dict__["owned_communities"] = [dummy_community(active=True)]
    # Ensure other properties that could block deletion are empty.
    mock_user.__dict__["contacts"] = []
    mock_user.__dict__["contact_endorsements"] = []
    mock_user.__dict__["roles"] = []

    service = UserManagementService(dummy_db, None)
    result = await service._can_delete_user(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_can_delete_user_blocked_by_contacts(dummy_db, mock_user):
    """
    Test that _can_delete_user returns False when the user has active contacts.

    This test simulates an active contact by directly assigning (via __dict__)
    a dummy contact (with is_active True) to the user's contacts list. Bypassing
    the standard attribute setter avoids SQLAlchemy instrumentation errors related
    to missing '_sa_instance_state' attributes.

    Expected Outcome:
      - _can_delete_user returns False.
    """
    # Create a dummy contact class with an is_active attribute.
    ActiveContact = type("Contact", (), {"is_active": True})

    # Bypass SQLAlchemy instrumentation by directly updating the instance's __dict__.
    mock_user.__dict__["owned_communities"] = []  # Ensure no active communities.
    mock_user.__dict__["contacts"] = [ActiveContact()]  # Set an active contact.
    mock_user.__dict__["contact_endorsements"] = []  # Ensure endorsements are empty.
    mock_user.__dict__["roles"] = []  # Ensure roles are empty.

    service = UserManagementService(dummy_db, None)
    result = await service._can_delete_user(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_can_delete_user_blocked_by_endorsements(dummy_db, mock_user):
    """
    Test that _can_delete_user returns False when the user has pending endorsements.

    A pending endorsement is simulated by adding a dummy object with is_verified False
    to the user's contact_endorsements list. To avoid SQLAlchemy instrumentation errors,
    the attribute is set directly via the instance's __dict__.

    Expected Outcome:
      - _can_delete_user returns False because pending endorsements block deletion.
    """
    # Define a dummy endorsement class without SQLAlchemy instrumentation.
    PendingEndorsement = type("Endorsement", (), {"is_verified": False})

    # Bypass the ORM's attribute setter by directly assigning to __dict__.
    mock_user.__dict__["owned_communities"] = []  # Ensure no active communities.
    mock_user.__dict__["contacts"] = []  # Ensure no active contacts.
    mock_user.__dict__["contact_endorsements"] = [PendingEndorsement()]
    mock_user.__dict__["roles"] = []  # Ensure no roles that could block deletion.

    service = UserManagementService(dummy_db, None)
    result = await service._can_delete_user(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_can_delete_user_blocked_by_system_role(dummy_db, mock_user):
    """
    Test that _can_delete_user returns False when the user holds an active system role.

    The test simulates a system role by creating a dummy role with attributes:
      - is_system_role: True
      - is_active: True
      - name: "admin"
    Instead of assigning to the user's roles using the property setter (which triggers SQLAlchemy instrumentation),
    we assign directly to the instance’s __dict__ to bypass the ORM's attribute events.

    Expected Outcome:
      - _can_delete_user returns False because the user holds an active system role.
    """
    # Define a dummy system role class.
    SystemRole = type(
        "Role", (), {"is_system_role": True, "is_active": True, "name": "admin"}
    )

    # Bypass ORM instrumentation by setting roles directly via __dict__.
    mock_user.__dict__["owned_communities"] = []  # Ensure no active communities.
    mock_user.__dict__["contacts"] = []  # Ensure no active contacts.
    mock_user.__dict__["contact_endorsements"] = []  # Ensure no pending endorsements.
    mock_user.__dict__["roles"] = [SystemRole()]

    service = UserManagementService(dummy_db, None)
    result = await service._can_delete_user(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_can_delete_user_success(dummy_db, mock_user):
    """
    Test that _can_delete_user returns True when the user meets all deletion criteria.

    The test simulates a user with no active communities, contacts, pending endorsements,
    or system roles.
    """
    mock_user.owned_communities = []
    mock_user.contacts = []
    mock_user.contact_endorsements = []
    mock_user.roles = []
    service = UserManagementService(dummy_db, None)
    result = await service._can_delete_user(mock_user)
    assert result is True


@pytest.mark.asyncio
async def test_delete_user_logs_on_success(dummy_db, mock_user):
    """
    Test that delete_user logs an info message when the deletion is successful.

    The deletion workflow in delete_user performs the following steps:
      1. Retrieves the user via get_user.
      2. Checks deletion eligibility with _can_delete_user.
      3. Calls the inherited delete method to perform deletion.
      4. If deletion is successful, logs an info message with "user_deleted".
      5. Returns the success status.

    This test patches:
      - get_user to return a valid user.
      - _can_delete_user to return True.
      - delete to return True.
      - The service's logger.info to capture the log call.

    Expected Outcome:
      - The method returns True.
      - The logger.info is called once with the expected parameters.
    """
    service = UserManagementService(dummy_db, None)
    service.get_user = AsyncMock(return_value=mock_user)
    service._can_delete_user = AsyncMock(return_value=True)
    service.delete = AsyncMock(return_value=True)
    # Patch the logger.info method to a MagicMock to capture its call.
    service._logger.info = MagicMock()
    dummy_db.commit = AsyncMock()

    result = await service.delete_user(mock_user.id)
    assert result is True
    service._logger.info.assert_called_once_with(
        "user_deleted",
        user_id=mock_user.id,
        email=mock_user.email,
    )
