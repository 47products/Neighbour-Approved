"""
Unit tests for the UserService class of the Neighbour Approved application.

This module contains tests for the various methods of the UserService,
ensuring that business logic such as authentication, user creation, and updates
function as expected. The tests use dummy objects and an asynchronous dummy
database session to simulate real-world operations.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from app.api.v1.schemas.user_schema import UserCreate
from app.core.error_handling import ValidationError
from app.services.service_exceptions import (
    DuplicateResourceError,
    ResourceNotFoundError,
)
from app.services.user_service import UserService


class DummyUser:
    """
    Dummy user class for testing the UserService authentication.

    This class simulates a user model for the purpose of testing the
    authenticate method in UserService. It provides the minimum attributes and
    methods required for the test.

    Attributes:
        id (int): Unique identifier for the user.
        email (str): Email address of the user.
        is_active (bool): Indicates whether the user account is active.
        password (str): Stored (hashed) password.
        last_login (datetime or None): Timestamp of the last successful login.
        owned_communities (list): List of communities owned by the user.
        contacts (list): List of contacts associated with the user.
        contact_endorsements (list): List of contact endorsements.
        roles (list): List of roles assigned to the user.
        email_verified (bool): Flag indicating if the email is verified.
        first_name (str): User's first name.
        last_name (str): User's last name.
        country (str): User's country.
        failed_login_attempts (int): Count of consecutive failed login attempts.
        failed_login_lockout (datetime or None): Timestamp until which login is locked.
    """

    def __init__(self, id, email, is_active=True, password="hashed_password"):
        self.id = id
        self.email = email
        self.is_active = is_active
        self.password = password
        self.last_login = None
        # The following attributes simulate relationships and additional fields.
        self.owned_communities = []
        self.contacts = []
        self.contact_endorsements = []
        self.roles = []
        self.email_verified = False
        self.first_name = "Test"
        self.last_name = "User"
        self.country = "Testland"
        self.failed_login_attempts = 0
        self.failed_login_lockout = None

    def verify_password(self, password: str) -> bool:
        """
        Verify that the provided password matches the expected password.

        For testing purposes, this method returns True if the plain text
        password is 'correct_password'; otherwise, it returns False.

        Args:
            password (str): The plain text password to verify.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        return password == "correct_password"


@pytest.mark.asyncio
async def test_authenticate_user_not_found(dummy_db):
    """
    Test that the UserService.authenticate method returns None when no user is found.

    This test simulates the scenario where a user lookup by email yields no results.
    The repository's get_by_email method is set to return None, mimicking a missing user.
    The expected behavior is that the authenticate method returns None without performing
    any database commit.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture.

    Returns:
        None

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """
    # Arrange:
    # Instantiate the UserService with the dummy database session.
    service = UserService(dummy_db)

    # Override the repository's get_by_email method to return None,
    # simulating that the user is not found in the database.
    service.repository.get_by_email = AsyncMock(return_value=None)

    # Act:
    # Call the authenticate method with an email that does not exist.
    result = await service.authenticate("nonexistent@example.com", "any_password")

    # Assert:
    # Verify that the method returns None, as the user is not found.
    assert result is None

    # Also verify that the database commit is not called since no update is needed.
    dummy_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_inactive_user(dummy_db):
    """
    Test that the UserService.authenticate method returns None when the user is inactive.

    This test simulates the scenario where a user is found in the database but is not active.
    Even if the password verification would succeed, the service should not allow authentication
    for an inactive user. The expected behavior is that the method returns None and does not perform
    a database commit.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture simulating the DB.

    Returns:
        None

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """

    # Arrange:
    # Create a dummy user object with the 'is_active' attribute set to False.
    class DummyUser:
        """
        Dummy user class for testing inactive user authentication.

        Attributes:
            id (int): Unique identifier.
            email (str): Email address.
            is_active (bool): Active status flag.
            password (str): Simulated stored (hashed) password.
            last_login (datetime or None): Timestamp of last successful login.
            Additional attributes simulate required fields.
        """

        def __init__(self, id, email, is_active, password="hashed_password"):
            self.id = id
            self.email = email
            self.is_active = is_active
            self.password = password
            self.last_login = None
            self.owned_communities = []
            self.contacts = []
            self.contact_endorsements = []
            self.roles = []
            self.email_verified = False
            self.first_name = "Test"
            self.last_name = "User"
            self.country = "Testland"
            self.failed_login_attempts = 0
            self.failed_login_lockout = None

        def verify_password(self, password: str) -> bool:
            """
            Simulate password verification.

            For testing purposes, return True if the password equals "correct_password".

            Args:
                password (str): The plain text password to verify.

            Returns:
                bool: True if the password is "correct_password", False otherwise.
            """
            return password == "correct_password"

    # Create a dummy inactive user.
    inactive_user = DummyUser(id=2, email="inactive@example.com", is_active=False)

    # Instantiate the UserService with the dummy database session.
    service = UserService(dummy_db)

    # Override the repository's get_by_email method to return the inactive user.
    service.repository.get_by_email = AsyncMock(return_value=inactive_user)

    # Act:
    # Call the authenticate method using the inactive user's email and a correct password.
    result = await service.authenticate("inactive@example.com", "correct_password")

    # Assert:
    # Since the user is inactive, the method should return None.
    assert result is None

    # Also, verify that no database commit was performed since no user data was updated.
    dummy_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_incorrect_password(dummy_db):
    """
    Test that the UserService.authenticate method returns None when the provided password is incorrect.

    This test simulates the scenario where a user is found and is active, but the password verification fails.
    The dummy user's verify_password method is implemented to always return False, thereby simulating an incorrect password.
    The expected behavior is that the authenticate method returns None without performing a database commit.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture simulating the database operations.

    Returns:
        None

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """

    # Arrange:
    # Define a dummy user class to simulate the user model for this test.
    class DummyUser:
        """
        Dummy user class for testing incorrect password authentication.

        Attributes:
            id (int): Unique identifier.
            email (str): Email address.
            is_active (bool): Active status flag.
            password (str): Simulated stored (hashed) password.
            last_login (datetime or None): Timestamp of the last successful login.
            Additional attributes simulate required fields for service methods.
        """

        def __init__(self, id, email, is_active, password="hashed_password"):
            self.id = id
            self.email = email
            self.is_active = is_active
            self.password = password
            self.last_login = None
            self.owned_communities = []
            self.contacts = []
            self.contact_endorsements = []
            self.roles = []
            self.email_verified = False
            self.first_name = "Test"
            self.last_name = "User"
            self.country = "Testland"
            self.failed_login_attempts = 0
            self.failed_login_lockout = None

        def verify_password(self, password: str) -> bool:
            """
            Simulate password verification.

            For this test, always return False to simulate an incorrect password.

            Args:
                password (str): The plain text password to verify.

            Returns:
                bool: False indicating that the password does not match.
            """
            return False

    # Create a dummy active user.
    active_user = DummyUser(id=3, email="active@example.com", is_active=True)

    # Instantiate the UserService with the dummy database session.
    service = UserService(dummy_db)

    # Override the repository's get_by_email method to return the active user.
    service.repository.get_by_email = AsyncMock(return_value=active_user)

    # Act:
    # Call the authenticate method using the active user's email and an incorrect password.
    result = await service.authenticate("active@example.com", "wrong_password")

    # Assert:
    # Since the password is incorrect, the method should return None.
    assert result is None

    # Verify that the database commit was not called since no user data was updated.
    dummy_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_success(dummy_db):
    """
    Test that the UserService.authenticate method successfully authenticates an active user
    when the correct password is provided.

    This test simulates a scenario where:
    - The repository's get_by_email method returns a dummy active user.
    - The dummy user's verify_password method returns True for the provided password.
    - The user's last_login attribute is updated to a datetime instance.
    - The database commit method is called to persist the change.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture simulating the DB operations.

    Returns:
        None

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """

    # Arrange:
    # Define a dummy user class to simulate the required attributes and methods for authentication.
    class DummyUser:
        """
        Dummy user class for testing successful authentication.

        Attributes:
            id (int): Unique identifier.
            email (str): User's email address.
            is_active (bool): Flag indicating if the user is active.
            password (str): Simulated stored (hashed) password.
            last_login (datetime or None): Timestamp of the last successful login.
            Additional attributes simulate relationships and required fields.
        """

        def __init__(self, id, email, is_active, password="hashed_password"):
            self.id = id
            self.email = email
            self.is_active = is_active
            self.password = password
            self.last_login = None
            self.owned_communities = []
            self.contacts = []
            self.contact_endorsements = []
            self.roles = []
            self.email_verified = False
            self.first_name = "Test"
            self.last_name = "User"
            self.country = "Testland"
            self.failed_login_attempts = 0
            self.failed_login_lockout = None

        def verify_password(self, password: str) -> bool:
            """
            Simulate password verification by returning True if the password matches 'correct_password'.

            Args:
                password (str): The plain text password to verify.

            Returns:
                bool: True if the provided password is 'correct_password', False otherwise.
            """
            return password == "correct_password"

    # Create a dummy active user.
    dummy_user = DummyUser(id=1, email="test@example.com", is_active=True)

    # Instantiate the UserService with the dummy database session.
    service = UserService(dummy_db)

    # Override the repository's get_by_email method to return our dummy active user.
    service.repository.get_by_email = AsyncMock(return_value=dummy_user)

    # Act:
    # Call the authenticate method using the active user's email and the correct password.
    result = await service.authenticate("test@example.com", "correct_password")

    # Assert:
    # Verify that the returned user is the dummy user.
    assert result is dummy_user

    # Confirm that the database's commit method was called to update the last_login attribute.
    dummy_db.commit.assert_awaited_once()

    # Check that the last_login attribute was updated to a datetime instance.
    assert isinstance(dummy_user.last_login, datetime)


@pytest.mark.asyncio
async def test_authenticate_exception_in_user_lookup(dummy_db):
    """
    Test that the UserService.authenticate method re-raises an exception if an error occurs
    during user lookup via the repository's get_by_email method.

    This test simulates a scenario where an exception (e.g., RuntimeError) is raised while
    attempting to retrieve a user. The expected behavior is that the exception is caught,
    logged, and then re-raised by the authenticate method.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture simulating database operations.

    Returns:
        None

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """
    # Arrange:
    # Instantiate the UserService with the dummy database session.
    service = UserService(dummy_db)

    # Configure the repository's get_by_email method to raise a RuntimeError,
    # simulating an error during user lookup.
    service.repository.get_by_email = AsyncMock(
        side_effect=RuntimeError("Test Exception")
    )

    # Act & Assert:
    # Use pytest.raises to verify that the exception is re-raised by the authenticate method.
    with pytest.raises(RuntimeError, match="Test Exception"):
        await service.authenticate("error@example.com", "any_password")

    # Verify that no commit was attempted since the exception occurred during user lookup.
    dummy_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_exception_during_commit(dummy_db):
    """
    Test that the UserService.authenticate method re-raises an exception if an error occurs
    during the commit operation.

    This test simulates a scenario where:
    - An active user is found in the database.
    - The provided password is correct.
    - The user's last_login attribute is updated.
    - However, an exception is raised during the database commit operation.

    The expected behavior is that the exception is re-raised, causing the authenticate method to fail.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture simulating the DB operations.

    Returns:
        None

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """

    # Arrange:
    # Define a dummy user class to simulate the required attributes and methods.
    class DummyUser:
        """
        Dummy user class for testing commit failure during authentication.

        Attributes:
            id (int): Unique identifier.
            email (str): User's email address.
            is_active (bool): Indicates if the user account is active.
            password (str): Simulated stored (hashed) password.
            last_login (datetime or None): Timestamp of the last successful login.
            Additional attributes simulate required relationships and fields.
        """

        def __init__(self, id, email, is_active, password="hashed_password"):
            self.id = id
            self.email = email
            self.is_active = is_active
            self.password = password
            self.last_login = None
            self.owned_communities = []
            self.contacts = []
            self.contact_endorsements = []
            self.roles = []
            self.email_verified = False
            self.first_name = "Test"
            self.last_name = "User"
            self.country = "Testland"
            self.failed_login_attempts = 0
            self.failed_login_lockout = None

        def verify_password(self, password: str) -> bool:
            """
            Simulate password verification.

            Returns True if the provided password matches 'correct_password'.

            Args:
                password (str): The plain text password to verify.

            Returns:
                bool: True if the password is 'correct_password', False otherwise.
            """
            return password == "correct_password"

    # Create a dummy active user.
    dummy_user = DummyUser(id=4, email="commitfail@example.com", is_active=True)

    # Instantiate the UserService with the dummy database session.
    service = UserService(dummy_db)

    # Override the repository's get_by_email method to return the dummy user.
    service.repository.get_by_email = AsyncMock(return_value=dummy_user)

    # Simulate an exception during the commit operation.
    dummy_db.commit = AsyncMock(side_effect=RuntimeError("Commit failed"))

    # Act & Assert:
    # Use pytest.raises to verify that the exception during commit is re-raised.
    with pytest.raises(RuntimeError, match="Commit failed"):
        await service.authenticate("commitfail@example.com", "correct_password")

    # Optionally, assert that commit was indeed attempted.
    dummy_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(dummy_db):
    """
    Test that create_user raises DuplicateResourceError if a user with the same email exists.

    This test simulates the scenario where repository.get_by_email returns an existing user.
    The expected behavior is that create_user raises a DuplicateResourceError.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture.
    """
    service = UserService(dummy_db)
    # Simulate an existing user by having get_by_email return a dummy user.
    existing_user = DummyUser(id=1, email="duplicate@example.com")
    service.repository.get_by_email = AsyncMock(return_value=existing_user)

    # Create dummy user creation data with the duplicate email.
    user_data = UserCreate(
        email="duplicate@example.com",
        password="ValidPass1!",
        first_name="Test",
        last_name="User",
        country="Testland",
    )

    with pytest.raises(DuplicateResourceError) as exc_info:
        await service.create_user(user_data)
    assert "Email already registered" in str(exc_info.value)


# @pytest.mark.asyncio
# async def test_validate_create_short_password(dummy_db):
#     """
#     Test that validate_create raises a ValidationError if the provided password is too short.

#     This test verifies that when the password is shorter than 8 characters, the service layer's
#     validate_create method raises a ValidationError with the expected message. To bypass Pydantic's
#     built‑in validation, we manually construct a UserCreate instance by bypassing its __init__.

#     Args:
#         dummy_db (AsyncMock): A dummy asynchronous database session fixture.

#     Returns:
#         None

#     Example:
#         Run this test with pytest:
#             pytest --maxfail=1 --disable-warnings -q
#     """
#     service = UserService(dummy_db)

#     # Manually create a UserCreate instance without triggering Pydantic's validation.
#     user_data = object.__new__(UserCreate)
#     # Manually set required attributes.
#     user_data.email = "new@example.com"
#     user_data.password = "short"  # Intentionally too short.
#     user_data.first_name = "Test"
#     user_data.last_name = "User"
#     user_data.country = "Testland"
#     # Optional fields can be set to None.
#     user_data.mobile_number = None
#     user_data.postal_address = None
#     user_data.physical_address = None

#     with pytest.raises(ValidationError) as exc_info:
#         await service.validate_create(user_data)
#     assert "Password must be at least 8 characters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_not_found(dummy_db):
    """
    Test that get_user raises ResourceNotFoundError when the user does not exist.

    This test simulates a scenario where the base service's get method returns None.
    The expected behavior is that get_user raises a ResourceNotFoundError.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture.
    """
    service = UserService(dummy_db)
    # Override the inherited get method to return None, simulating a missing user.
    service.get = AsyncMock(return_value=None)
    user_id = 123

    with pytest.raises(ResourceNotFoundError) as exc_info:
        await service.get_user(user_id)
    assert f"User {user_id} not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_user_success(dummy_db):
    """
    Test that get_user returns the correct user instance when the user is found.

    This test simulates a successful retrieval by overriding the base service's get method.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture.
    """
    service = UserService(dummy_db)
    dummy_user = DummyUser(id=1, email="found@example.com")
    service.get = AsyncMock(return_value=dummy_user)

    user = await service.get_user(dummy_user.id)
    assert user is dummy_user


@pytest.mark.asyncio
async def test_create_user_success(dummy_db):
    """
    Test that create_user successfully creates a new user when no duplicate exists.

    This test simulates the scenario where repository.get_by_email returns None,
    indicating that no user with the given email exists. In this case, the method should
    call self.create(data) to create a new user. The expected behavior is that create_user
    returns the newly created user instance.

    Args:
        dummy_db (AsyncMock): A dummy asynchronous database session fixture.

    Returns:
        None

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """
    # Arrange:
    # Instantiate the UserService with the dummy database session.
    service = UserService(dummy_db)
    # Override repository.get_by_email to simulate that no existing user is found.
    service.repository.get_by_email = AsyncMock(return_value=None)

    # Create dummy user creation data.
    user_data = UserCreate(
        email="new@example.com",
        password="ValidPass1!",
        first_name="New",
        last_name="User",
        country="Testland",
    )

    # Create a dummy user instance to simulate a successful creation.
    dummy_user = DummyUser(id=100, email="new@example.com")

    # Override the service.create method to simulate user creation.
    service.create = AsyncMock(return_value=dummy_user)

    # Act:
    # Call create_user with the provided user creation data.
    result = await service.create_user(user_data)

    # Assert:
    # The returned user should be the dummy user, and the create method should be called with the same data.
    assert result is dummy_user
    service.create.assert_awaited_once_with(user_data)
