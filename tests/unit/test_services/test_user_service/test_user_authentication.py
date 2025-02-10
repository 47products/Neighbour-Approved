"""
Unit tests for the Authentication Service.

This module contains tests for verifying the functionality of the 
AuthenticationService class, including authentication workflows,
login tracking, and security measures.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from sqlalchemy.exc import SQLAlchemyError
import pytest
from unittest.mock import AsyncMock
from app.core.error_handling import AuthenticationError
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


@pytest.mark.asyncio
async def test_authenticate_user_first_login():
    """
    Test first-time user authentication.

    This test verifies that:
    1. A user authenticates successfully with correct email and password.
    2. The user is identified as logging in for the first time.
    3. The last login timestamp is updated.
    4. Failed login attempts are reset.

    Uses mocked database and security service to isolate the test.
    """
    # Arrange
    test_email = "firstlogin@example.com"
    password = "newuserpassword"

    # Create a mock user who has never logged in before
    mock_user = User(
        id=2,
        email=test_email,
        password="hashed_password",
        first_name="Alice",
        last_name="Smith",
        is_active=True,
        email_verified=True,
        last_login=None,  # Indicates first login
    )

    # Initialize authentication-related attributes
    mock_user.failed_login_attempts = 1
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
    assert authenticated_user.last_login is not None  # Should be updated
    assert authenticated_user.failed_login_attempts == 0
    assert authenticated_user.failed_login_lockout is None
    assert is_first_login is True  # Confirming first login status

    # Verify method calls
    mock_security.verify_password.assert_called_once_with(mock_user.password, password)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_authenticate_user_locked():
    """
    Test authentication attempt on locked account with tracking.

    This test verifies that:
    1. If a user account is locked due to failed login attempts, authentication fails.
    2. The system raises a ValidationError indicating the lockout.
    3. The lockout expiry time is included in the error details.

    Uses mocked database and security service to isolate the test.
    """
    # Arrange
    test_email = "locked@example.com"
    password = "irrelevantpassword"

    # Set a future lockout expiry time
    lockout_until = datetime.now(UTC) + timedelta(minutes=15)

    # Create a mock user with an active lockout
    mock_user = User(
        id=3,
        email=test_email,
        password="hashed_password",
        first_name="Locked",
        last_name="User",
        is_active=True,
        email_verified=True,
        last_login=None,
    )
    mock_user.failed_login_attempts = 5
    mock_user.failed_login_lockout = lockout_until  # Account is locked

    # Configure mock database and repository behavior
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Configure security service mock (not used but included for consistency)
    mock_security = AsyncMock()

    # Instantiate authentication service with mocked dependencies
    auth_service = AuthenticationService(mock_db, mock_security)

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        await auth_service.authenticate_user(test_email, password)

    # Validate the raised exception
    assert "Account temporarily locked" in str(exc_info.value)
    assert exc_info.value.details["lockout_until"] == lockout_until

    # Ensure that password verification was not attempted
    mock_security.verify_password.assert_not_called()

    # Ensure that no database commit was attempted
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_track_successful_login():
    """
    Test successful login tracking updates.

    This test verifies that:
    1. The user's last login timestamp is updated upon successful authentication.
    2. Failed login attempts are reset to zero.
    3. The failed login lockout is cleared.
    4. The database commit is called to persist the changes.

    Uses a mocked database to isolate the test.
    """
    # Arrange
    test_email = "test@example.com"

    # Create a mock user with previous failed attempts
    mock_user = User(
        id=4,
        email=test_email,
        password="hashed_password",
        first_name="Track",
        last_name="Login",
        is_active=True,
        email_verified=True,
        last_login=None,  # Last login is None, meaning this could be the first tracked login
    )

    # Initialize authentication-related attributes
    mock_user.failed_login_attempts = 3
    mock_user.failed_login_lockout = None

    # Configure mock database
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    # Instantiate authentication service with mocked dependencies
    auth_service = AuthenticationService(mock_db, AsyncMock())

    # Act
    await auth_service._track_successful_login(mock_user)

    # Assert
    assert mock_user.last_login is not None  # Last login should be updated
    assert mock_user.failed_login_attempts == 0  # Failed attempts should be reset
    assert mock_user.failed_login_lockout is None  # Lockout should be cleared

    # Verify that commit was called to persist changes
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_handle_failed_login_first_attempt():
    """
    Test handling of first failed login attempt.

    This test verifies that:
    1. The user's failed login attempt count is incremented.
    2. No lockout is applied on the first failure.
    3. The database commit is called to persist the changes.

    Uses a mocked database to isolate the test.
    """
    # Arrange
    test_email = "test@example.com"

    # Create a mock user with no prior failed attempts
    mock_user = User(
        id=5,
        email=test_email,
        password="hashed_password",
        first_name="First",
        last_name="Attempt",
        is_active=True,
        email_verified=True,
        last_login=None,
    )

    # Initialize authentication-related attributes
    mock_user.failed_login_attempts = 0
    mock_user.failed_login_lockout = None

    # Configure mock database
    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    # Instantiate authentication service with mocked dependencies
    auth_service = AuthenticationService(mock_db, AsyncMock())

    # Act
    await auth_service._handle_failed_login(mock_user)

    # Assert
    assert mock_user.failed_login_attempts == 1  # Failed attempts should increase by 1
    assert mock_user.failed_login_lockout is None  # No lockout should be applied

    # Verify that commit was called to persist changes
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_authenticate_sqlalchemy_error(dummy_db):
    """
    Test that a SQLAlchemyError during commit in authenticate
    is caught and re-raised as an AuthenticationError.
    """
    test_email = "test@example.com"
    password = "correct_password"
    mock_user = User(id=1, email=test_email, password="hashed_password", is_active=True)
    mock_user.failed_login_attempts = 0
    mock_user.failed_login_lockout = None

    # Prepare a repository that returns the valid user.
    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=mock_user)
    # *** IMPORTANT: assign dummy_db to the repository's db attribute ***
    mock_repository.db = dummy_db

    # Security service returns True so that commit is reached.
    mock_security = AsyncMock()
    mock_security.verify_password.return_value = True

    auth_service = AuthenticationService(dummy_db, mock_security)
    auth_service._repository = mock_repository

    # Force the commit to raise SQLAlchemyError.
    dummy_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB error"))

    with pytest.raises(AuthenticationError, match="Authentication failed"):
        await auth_service.authenticate(test_email, password)


@pytest.mark.asyncio
async def test_authenticate_generic_exception(dummy_db):
    """
    Test that a generic exception (e.g. from verify_password)
    in authenticate is caught and re-raised as an AuthenticationError.
    """
    test_email = "test@example.com"
    password = "any_password"
    mock_user = User(id=2, email=test_email, password="hashed_password", is_active=True)
    mock_user.failed_login_attempts = 0
    mock_user.failed_login_lockout = None

    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=mock_user)

    mock_security = AsyncMock()
    mock_security.verify_password.side_effect = Exception("Unexpected error")

    auth_service = AuthenticationService(dummy_db, mock_security)
    auth_service._repository = mock_repository

    with pytest.raises(AuthenticationError, match="Authentication failed"):
        await auth_service.authenticate(test_email, password)


@pytest.mark.asyncio
async def test_authenticate_user_no_user(dummy_db):
    """
    Test that authenticate_user raises an AuthenticationError
    when no user is found by email.
    """
    test_email = "nonexistent@example.com"
    password = "irrelevant"
    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=None)
    mock_security = AsyncMock()

    auth_service = AuthenticationService(dummy_db, mock_security)
    auth_service._repository = mock_repository

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        await auth_service.authenticate_user(test_email, password)


@pytest.mark.asyncio
async def test_authenticate_user_invalid_password(dummy_db):
    """
    Test that authenticate_user (the full workflow) raises an AuthenticationError
    when password verification fails.
    """
    test_email = "test@example.com"
    password = "wrong_password"
    mock_user = User(
        id=3,
        email=test_email,
        password="hashed_password",
        is_active=True,
        last_login=datetime.now(UTC),
    )
    mock_user.failed_login_attempts = 0
    mock_user.failed_login_lockout = None

    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=mock_user)
    # IMPORTANT: Set the repository's db attribute so that self.db.commit() is awaitable.
    mock_repository.db = dummy_db

    mock_security = AsyncMock()
    # Return False to simulate an invalid password.
    mock_security.verify_password.return_value = False

    auth_service = AuthenticationService(dummy_db, mock_security)
    auth_service._repository = mock_repository

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        await auth_service.authenticate_user(test_email, password)


@pytest.mark.asyncio
async def test_authenticate_user_no_track(dummy_db):
    """
    Test that authenticate_user does not call _track_successful_login
    when track_login is set to False.
    """
    test_email = "test@example.com"
    password = "correct_password"
    mock_user = User(
        id=4,
        email=test_email,
        password="hashed_password",
        is_active=True,
        # Simulate a non-first login by setting last_login.
        last_login=datetime.now(UTC),
    )
    mock_user.failed_login_attempts = 0
    mock_user.failed_login_lockout = None

    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=mock_user)
    mock_security = AsyncMock()
    mock_security.verify_password.return_value = True

    auth_service = AuthenticationService(dummy_db, mock_security)
    auth_service._repository = mock_repository
    # Replace _track_successful_login with a mock to detect calls.
    auth_service._track_successful_login = AsyncMock()

    _, is_first_login = await auth_service.authenticate_user(
        test_email, password, track_login=False
    )
    auth_service._track_successful_login.assert_not_called()
    assert is_first_login is False


@pytest.mark.asyncio
async def test_authenticate_user_deactivated(dummy_db):
    """
    Test that authenticate_user raises an AuthenticationError with the message
    "Account is deactivated" when the user is inactive.
    """
    test_email = "inactive@example.com"
    password = "any_password"

    # Create a mock user that is inactive.
    mock_user = User(
        id=1,
        email=test_email,
        password="hashed_password",
        is_active=False,  # User is deactivated.
        last_login=datetime.now(UTC),
    )
    mock_user.failed_login_attempts = 0
    mock_user.failed_login_lockout = None

    # Prepare a mock repository that returns the inactive user.
    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(return_value=mock_user)
    # Ensure the repository's db attribute is set to dummy_db.
    mock_repository.db = dummy_db

    # Prepare a dummy security service (its verify_password should not be called in this case).
    mock_security = AsyncMock()

    # Instantiate the authentication service with the dummy DB and security service.
    auth_service = AuthenticationService(dummy_db, mock_security)
    auth_service._repository = mock_repository

    # Expect an AuthenticationError with the proper message.
    with pytest.raises(AuthenticationError, match="Account is deactivated"):
        await auth_service.authenticate_user(test_email, password)


@pytest.mark.asyncio
async def test_authenticate_user_get_by_email_exception(dummy_db):
    """
    Test that if repository.get_by_email raises an exception,
    authenticate_user propagates that exception.
    """
    test_email = "test@example.com"
    password = "any_password"
    mock_repository = MagicMock()
    mock_repository.get_by_email = AsyncMock(side_effect=Exception("DB failure"))
    mock_security = AsyncMock()

    auth_service = AuthenticationService(dummy_db, mock_security)
    auth_service._repository = mock_repository

    with pytest.raises(Exception, match="DB failure"):
        await auth_service.authenticate_user(test_email, password)


@pytest.mark.asyncio
async def test_handle_failed_login_lockout_15(dummy_db):
    """
    Test that a failed login attempt which brings the user's failed count
    to 4 applies a 15-minute lockout.
    """
    test_email = "test@example.com"
    mock_user = User(
        id=5,
        email=test_email,
        password="hashed_password",
        is_active=True,
    )
    # Set failed_login_attempts to 3 so that after increment it becomes 4.
    mock_user.failed_login_attempts = 3
    mock_user.failed_login_lockout = None

    dummy_db.commit = AsyncMock()
    auth_service = AuthenticationService(dummy_db, AsyncMock())
    await auth_service._handle_failed_login(mock_user)

    assert mock_user.failed_login_attempts == 4
    # Check that a lockout was applied (approximately 15 minutes from now).
    assert mock_user.failed_login_lockout is not None
    expected_lockout = datetime.now(UTC) + timedelta(minutes=15)
    diff = mock_user.failed_login_lockout - expected_lockout
    # Allow a tolerance of a few seconds.
    assert abs(diff.total_seconds()) < 5


@pytest.mark.asyncio
async def test_handle_failed_login_lockout_1hr(dummy_db):
    """
    Test that a failed login attempt which brings the user's failed count
    to 7 applies a 1-hour lockout.
    """
    test_email = "test@example.com"
    mock_user = User(
        id=6,
        email=test_email,
        password="hashed_password",
        is_active=True,
    )
    # Set failed_login_attempts to 6 so that after increment it becomes 7.
    mock_user.failed_login_attempts = 6
    mock_user.failed_login_lockout = None

    dummy_db.commit = AsyncMock()
    auth_service = AuthenticationService(dummy_db, AsyncMock())
    await auth_service._handle_failed_login(mock_user)

    assert mock_user.failed_login_attempts == 7
    # Check that a lockout was applied (approximately 1 hour from now).
    assert mock_user.failed_login_lockout is not None
    expected_lockout = datetime.now(UTC) + timedelta(hours=1)
    diff = mock_user.failed_login_lockout - expected_lockout
    assert abs(diff.total_seconds()) < 5
