"""
Unit tests for the Authentication Service.

This module contains tests for verifying the functionality of the 
AuthenticationService class, including authentication workflows,
login tracking, and security measures.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
import pytest
from unittest.mock import AsyncMock
from app.services.service_exceptions import ValidationError
from app.db.models.user_model import User
from app.services.user_service.authentication import AuthenticationService


@pytest.mark.asyncio
async def test_authenticate_successful():
    """
    Test successful user authentication with valid credentials.

    This test verifies that:
    1. A user can authenticate with correct email and password
    2. Last login timestamp is updated
    3. Failed login attempts are reset
    4. The authenticated user is returned

    It uses mocked database and security service to isolate the test.
    """
    # Arrange
    test_email = "test@example.com"
    password = "securepassword"

    # Create mock user with the attributes defined in the model
    mock_user = User(
        id=1,
        email=test_email,
        password="hashed_password",
        first_name="John",
        last_name="Doe",
        is_active=True,
        email_verified=True,
        last_login=None,
    )

    # Add the attributes the authentication service needs to track
    mock_user.failed_login_attempts = 2
    mock_user.failed_login_lockout = None

    # Configure mock database with repository behavior using execute
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    # Create a mock result for the execute method.
    # Use MagicMock for scalar_one_or_none so that it returns mock_user synchronously.
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Configure security service
    mock_security = AsyncMock()
    mock_security.verify_password.return_value = True

    # Create service instance with mocked dependencies
    auth_service = AuthenticationService(mock_db, mock_security)

    # Act
    authenticated_user = await auth_service.authenticate(test_email, password)

    # Assert
    assert authenticated_user is not None
    assert authenticated_user.id == mock_user.id
    assert authenticated_user.email == test_email
    assert authenticated_user.is_active is True
    assert authenticated_user.last_login is not None
    assert authenticated_user.failed_login_attempts == 0
    assert authenticated_user.failed_login_lockout is None

    # Verify method calls
    mock_security.verify_password.assert_called_once_with(mock_user.password, password)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_authenticate_user_not_found():
    """
    Test authentication attempt with non-existent user.
    Verifies that authenticate returns None when user is not found.
    """
    # Arrange
    test_email = "nonexistent@example.com"
    password = "irrelevant"

    # Configure dummy database with repository behavior using execute
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    # Configure execute to return a result whose scalar_one_or_none returns None (user not found)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Configure dummy security service (no need to set a return value here since it shouldn't be called)
    mock_security = AsyncMock()

    # Create service instance with mocked dependencies
    auth_service = AuthenticationService(mock_db, mock_security)

    # Act
    authenticated_user = await auth_service.authenticate(test_email, password)

    # Assert that authentication returns None when no user is found.
    assert authenticated_user is None

    # Optionally verify that the security service's verify_password was not called.
    mock_security.verify_password.assert_not_called()


@pytest.mark.asyncio
async def test_authenticate_inactive_user():
    """
    Test authentication attempt with inactive user account.
    Verifies that authenticate returns None for inactive users.
    """
    # Arrange
    test_email = "inactive@example.com"
    password = "any_password"

    # Create a mock user that is inactive
    mock_user = User(
        id=1,
        email=test_email,
        password="hashed_password",
        first_name="John",
        last_name="Doe",
        is_active=False,  # User is inactive
        email_verified=True,
        last_login=None,
    )
    mock_user.failed_login_attempts = 0
    mock_user.failed_login_lockout = None

    # Configure mock database to simulate repository behavior using execute
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    # Create a mock result with scalar_one_or_none returning the inactive user
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Configure dummy security service; password verification should not be invoked
    mock_security = AsyncMock()

    # Create the authentication service with mocked dependencies
    auth_service = AuthenticationService(mock_db, mock_security)

    # Act: attempt to authenticate with an inactive user account
    authenticated_user = await auth_service.authenticate(test_email, password)

    # Assert: authentication should fail and return None
    assert authenticated_user is None
    # Ensure that verify_password was not called since the user is inactive
    mock_security.verify_password.assert_not_called()


@pytest.mark.asyncio
async def test_authenticate_invalid_password():
    """
    Test authentication attempt with incorrect password.
    Verifies that authenticate returns None and increments failed attempts.
    """
    # Arrange
    test_email = "test@example.com"
    wrong_password = "wrongpassword"
    initial_failed_attempts = 2

    # Create a mock active user with initial failed login attempts.
    mock_user = User(
        id=1,
        email=test_email,
        password="hashed_password",
        first_name="John",
        last_name="Doe",
        is_active=True,
        email_verified=True,
        last_login=None,
    )
    mock_user.failed_login_attempts = initial_failed_attempts
    mock_user.failed_login_lockout = None

    # Configure mock database with repository behavior using execute.
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    # Create a mock result for the execute method so that scalar_one_or_none returns the mock user.
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Configure security service so that verify_password returns False.
    mock_security = AsyncMock()
    mock_security.verify_password.return_value = False

    # Create the authentication service with mocked dependencies.
    auth_service = AuthenticationService(mock_db, mock_security)

    # Act
    result = await auth_service.authenticate(test_email, wrong_password)

    # Assert: authentication should fail and return None.
    assert result is None

    # Assert: failed login attempts have been incremented by 1.
    assert mock_user.failed_login_attempts == initial_failed_attempts + 1

    # Verify that verify_password was called with the correct arguments.
    mock_security.verify_password.assert_called_once_with(
        mock_user.password, wrong_password
    )

    # Verify that the database commit method was called (from _handle_failed_login).
    assert mock_db.commit.call_count >= 1


@pytest.mark.asyncio
async def test_authenticate_account_locked():
    """
    Test authentication attempt on locked account.
    Verifies that authenticate raises ValidationError when account is locked.
    """
    test_email = "locked@example.com"
    password = "any_password"

    lockout_until = datetime.now(UTC) + timedelta(minutes=15)
    mock_user = User(
        id=1,
        email=test_email,
        password="hashed_password",
        first_name="Locked",
        last_name="User",
        is_active=True,
        email_verified=True,
        last_login=None,
    )
    mock_user.failed_login_attempts = 3
    mock_user.failed_login_lockout = lockout_until

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    mock_security = AsyncMock()
    auth_service = AuthenticationService(mock_db, mock_security)

    # Assert that the expected ValidationError is raised
    with pytest.raises(ValidationError) as exc_info:
        await auth_service.authenticate(test_email, password)

    # Verify the correct error message is returned
    assert "Account temporarily locked" in str(exc_info.value)
    assert exc_info.value.details["lockout_until"] == lockout_until


@pytest.mark.asyncio
async def test_authenticate_user_successful():
    """
    Test successful user authentication with tracking enabled.

    This test verifies that:
    1. A user can authenticate with correct email and password.
    2. The last login timestamp is updated.
    3. Failed login attempts are reset.
    4. The authentication workflow properly returns the user and first login status.

    Uses mocked database and security service to isolate the test.
    """
    # Arrange
    test_email = "test@example.com"
    password = "securepassword"

    # Create mock user with expected attributes
    mock_user = User(
        id=1,
        email=test_email,
        password="hashed_password",
        first_name="John",
        last_name="Doe",
        is_active=True,
        email_verified=True,
        last_login=None,
    )

    # Initialize authentication-related attributes
    mock_user.failed_login_attempts = 2
    mock_user.failed_login_lockout = None

    # Configure mock database and repository behavior
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Configure security service mock
    mock_security = AsyncMock()
    mock_security.verify_password.return_value = True

    # Instantiate authentication service with mocked dependencies
    auth_service = AuthenticationService(mock_db, mock_security)

    # Act
    authenticated_user, is_first_login = await auth_service.authenticate_user(
        test_email, password
    )

    # Assert
    assert authenticated_user is not None
    assert authenticated_user.id == mock_user.id
    assert authenticated_user.email == test_email
    assert authenticated_user.is_active is True
    assert authenticated_user.last_login is not None
    assert authenticated_user.failed_login_attempts == 0
    assert authenticated_user.failed_login_lockout is None
    assert (
        is_first_login is True
    )  # Since last_login was None, this should be first login

    # Verify method calls
    mock_security.verify_password.assert_called_once_with(mock_user.password, password)
    mock_db.commit.assert_called_once()


# async def test_authenticate_user_first_login():
#     """
#     Test first-time user authentication.
#     Verifies that authenticate_user correctly identifies first login.
#     """


# async def test_authenticate_user_locked():
#     """
#     Test authentication attempt on locked account with tracking.
#     Verifies that authenticate_user raises ValidationError for locked accounts.
#     """


# async def test_track_successful_login():
#     """
#     Test successful login tracking updates.
#     Verifies that login timestamp and attempt tracking are updated correctly.
#     """


# async def test_handle_failed_login_first_attempt():
#     """
#     Test handling of first failed login attempt.
#     Verifies that failed attempt is recorded without lockout.
#     """


# async def test_handle_failed_login_multiple_attempts():
#     """
#     Test handling of multiple failed login attempts.
#     Verifies progressive lockout policy implementation.
#     """


# async def test_handle_failed_login_extended_lockout():
#     """
#     Test handling of extended lockout after numerous failures.
#     Verifies maximum lockout duration is applied correctly.
#     """


# @pytest.mark.asyncio
# async def test_authenticate_database_error(dummy_db: AsyncMock):
#     """
#     Test authentication handling of database errors.

#     This test verifies that the `authenticate` method properly handles and logs database
#     errors that occur during user lookup. When the repository raises a SQLAlchemy
#     error, the service should catch it, log the error, and raise an AuthenticationError.

#     Args:
#         dummy_db: A dummy asynchronous database session fixture.

#     Raises:
#         AuthenticationError: Expected to be raised when database error occurs.
#     """
