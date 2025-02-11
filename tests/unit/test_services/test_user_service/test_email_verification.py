"""
Unit tests for the EmailVerificationService module.

This module tests the EmailVerificationService class, which manages the email
verification workflow in the application. It covers scenarios including:
  - Handling already verified emails.
  - Detecting ineligible users for verification.
  - Successful verification updates and post-verification processes.
  - Eligibility checks (_can_verify_email and _has_completed_onboarding).
  - Post-verification workflow (_handle_post_verification), including role assignment
    and error handling.

To run the tests, use:
    pytest tests/unit/test_services/test_user_service/test_email_verification.py

Dependencies:
    - pytest
    - SQLAlchemy (for session mocks)
    - AsyncMock, MagicMock from unittest.mock
    - EmailVerificationService and related exception classes.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.services.user_service.user_service_email_verification import (
    EmailVerificationService,
)
from app.services.service_exceptions import BusinessRuleViolationError, ValidationError
from app.db.models.role_model import Role


@pytest.mark.asyncio
async def test_verify_email_already_verified(dummy_db, mock_user):
    """
    Test that verify_email returns False when the user's email is already verified.

    This test simulates the case where the user has already verified their email.
    The verify_email method should log an informational message and return False without
    performing a commit to the database.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance.

    Expected Outcome:
        - The method returns False.
        - The database commit method is not called.
    """
    # Simulate an already verified user.
    mock_user.email_verified = True
    service = EmailVerificationService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.commit = AsyncMock()  # Stub out commit to verify it's not called.

    result = await service.verify_email(mock_user.id)
    assert result is False
    dummy_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_verify_email_ineligible(dummy_db, mock_user):
    """
    Test that verify_email raises a ValidationError and performs a rollback if the user is ineligible.

    In this test, the user's profile is incomplete (first_name is None), making them ineligible
    for verification. The method should raise a ValidationError with an appropriate message and
    execute a rollback on the database session.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with incomplete profile data.

    Expected Outcome:
        - A ValidationError is raised with a message about verification requirements.
        - The database rollback method is called exactly once.
    """
    # Simulate an ineligible user.
    mock_user.email_verified = False
    mock_user.first_name = None  # Incomplete profile
    service = EmailVerificationService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    dummy_db.rollback = AsyncMock()  # Stub out rollback.

    with pytest.raises(
        ValidationError, match="User does not meet verification requirements"
    ):
        await service.verify_email(mock_user.id)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_verify_email_success(dummy_db, mock_user):
    """
    Test that verify_email successfully verifies an eligible user.

    This test sets up a user with complete and valid profile data, making them eligible
    for email verification. The method should update the user's verification status,
    record the verification date, trigger post-verification processing, and commit the changes.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with complete profile and onboarding data.

    Expected Outcome:
        - The method returns True.
        - The user's email_verified flag is set to True.
        - The user's verification_date is set to a valid datetime.
        - The database commit method is called exactly once.
    """
    # Configure an eligible user.
    mock_user.email_verified = False
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    mock_user.country = "USA"  # Onboarding complete.
    service = EmailVerificationService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    service._handle_post_verification = AsyncMock()  # Stub out post-verification.
    dummy_db.commit = AsyncMock()  # Stub out commit.

    result = await service.verify_email(mock_user.id)
    assert result is True
    assert mock_user.email_verified is True
    assert isinstance(mock_user.verification_date, datetime)
    dummy_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_verify_email_post_verification_failure(dummy_db, mock_user):
    """
    Test that verify_email rolls back and raises BusinessRuleViolationError if post-verification fails.

    In this scenario, the _handle_post_verification method is forced to raise an Exception,
    simulating a failure in the post-verification process. The verify_email method should then
    rollback the database transaction and raise a BusinessRuleViolationError.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with valid profile data.

    Expected Outcome:
        - A BusinessRuleViolationError is raised with a message indicating email verification failure.
        - The database rollback method is called exactly once.
    """
    # Configure an eligible user.
    mock_user.email_verified = False
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    mock_user.country = "USA"
    service = EmailVerificationService(dummy_db)
    service.get_user = AsyncMock(return_value=mock_user)
    service._handle_post_verification = AsyncMock(
        side_effect=Exception("Post verification error")
    )
    dummy_db.rollback = AsyncMock()  # Stub out rollback.

    with pytest.raises(BusinessRuleViolationError, match="Email verification failed"):
        await service.verify_email(mock_user.id)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_can_verify_email_no_email(dummy_db, mock_user):
    """
    Test that _can_verify_email returns False when the user has no email address.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with an empty email.

    Expected Outcome:
        - The method returns False.
    """
    mock_user.email = ""
    service = EmailVerificationService(dummy_db)
    result = await service._can_verify_email(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_can_verify_email_inactive(dummy_db, mock_user):
    """
    Test that _can_verify_email returns False when the user account is inactive.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with is_active set to False.

    Expected Outcome:
        - The method returns False.
    """
    mock_user.email = "test@example.com"
    mock_user.is_active = False
    service = EmailVerificationService(dummy_db)
    result = await service._can_verify_email(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_can_verify_email_incomplete_profile(dummy_db, mock_user):
    """
    Test that _can_verify_email returns False when the user's profile is incomplete.

    This test simulates an incomplete profile by omitting the first name.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance missing the first name.

    Expected Outcome:
        - The method returns False.
    """
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.first_name = None  # Missing first name.
    service = EmailVerificationService(dummy_db)
    result = await service._can_verify_email(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_can_verify_email_incomplete_onboarding(dummy_db, mock_user):
    """
    Test that _can_verify_email returns False when required onboarding is incomplete.

    In this test, the user's country is None to simulate incomplete onboarding.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with incomplete onboarding data.

    Expected Outcome:
        - The method returns False.
    """
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    mock_user.country = None  # Onboarding incomplete.
    service = EmailVerificationService(dummy_db)
    result = await service._can_verify_email(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_can_verify_email_success(dummy_db, mock_user):
    """
    Test that _can_verify_email returns True when the user meets all verification requirements.

    The user is set with a valid email, active status, complete profile, and complete onboarding.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with complete and valid information.

    Expected Outcome:
        - The method returns True.
    """
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    mock_user.country = "USA"
    service = EmailVerificationService(dummy_db)
    result = await service._can_verify_email(mock_user)
    assert result is True


@pytest.mark.asyncio
async def test_has_completed_onboarding_complete(dummy_db, mock_user):
    """
    Test that _has_completed_onboarding returns True when all required onboarding fields are present.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with complete onboarding data.

    Expected Outcome:
        - The method returns True.
    """
    mock_user.email = "test@example.com"
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    mock_user.country = "USA"
    service = EmailVerificationService(dummy_db)
    result = await service._has_completed_onboarding(mock_user)
    assert result is True


@pytest.mark.asyncio
async def test_has_completed_onboarding_incomplete(dummy_db, mock_user):
    """
    Test that _has_completed_onboarding returns False if a required onboarding field is missing.

    Here, the country field is missing from the user's data.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance with incomplete onboarding data.

    Expected Outcome:
        - The method returns False.
    """
    mock_user.email = "test@example.com"
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    mock_user.country = None
    service = EmailVerificationService(dummy_db)
    result = await service._has_completed_onboarding(mock_user)
    assert result is False


@pytest.mark.asyncio
async def test_handle_post_verification_assign_role(dummy_db, mock_user):
    """
    Test that _handle_post_verification assigns the "verified_user" role if not already present.

    This test simulates a scenario where the user has no roles and a valid "verified_user"
    role is found via a database query. We configure dummy_db.query as a MagicMock so that it
    returns an object with a .filter() method. The filter chain's .first() method is then stubbed
    to return the mock role asynchronously.

    Expected Outcome:
        - The "verified_user" role is appended to the user's roles.
    """
    # Ensure the user starts with an empty roles list.
    mock_user.roles = []
    service = EmailVerificationService(dummy_db)

    # Create a mock verified role.
    mock_role = Role(id=1, name="verified_user", is_active=True)

    # Set up dummy_db.query to simulate a role lookup:
    # dummy_db.query(Role) returns query_mock (a MagicMock) with a .filter() method.
    query_mock = MagicMock()
    query_mock.filter.return_value.first = AsyncMock(return_value=mock_role)
    dummy_db.query = MagicMock(return_value=query_mock)

    # Invoke the method under test.
    await service._handle_post_verification(mock_user)

    # Verify that the role has been assigned.
    assert any(role.name == "verified_user" for role in mock_user.roles)


@pytest.mark.asyncio
async def test_handle_post_verification_no_role_found(dummy_db, mock_user):
    """
    Test that _handle_post_verification does not modify the user's roles if no verified role is found.

    This test simulates the scenario where the query for the "verified_user" role returns None.
    We configure dummy_db.query as a MagicMock so that it returns an object with a .filter() method.
    The filter chain's .first() method is stubbed to return None asynchronously.

    Expected Outcome:
        - The user's roles remain unchanged (i.e., no "verified_user" role is added).
    """
    # Ensure the user starts with an empty roles list.
    mock_user.roles = []
    service = EmailVerificationService(dummy_db)

    # Set up dummy_db.query to simulate a role lookup that returns None.
    query_mock = MagicMock()
    query_mock.filter.return_value.first = AsyncMock(return_value=None)
    dummy_db.query = MagicMock(return_value=query_mock)

    # Invoke the method under test.
    await service._handle_post_verification(mock_user)

    # Verify that no verified role has been added.
    assert not any(role.name == "verified_user" for role in mock_user.roles)


@pytest.mark.asyncio
async def test_handle_post_verification_failure(dummy_db, mock_user):
    """
    Test that _handle_post_verification raises a BusinessRuleViolationError if an exception occurs during post-verification.

    In this test, dummy_db.query is configured to raise an Exception, simulating a database error.
    The method should catch the exception, log an error, and raise a BusinessRuleViolationError.

    Args:
        dummy_db (AsyncMock): A mock representing the asynchronous database session.
        mock_user (User): A mocked User instance.

    Expected Outcome:
        - A BusinessRuleViolationError is raised with a message indicating failure in post-verification.
    """
    mock_user.roles = []
    service = EmailVerificationService(dummy_db)
    dummy_db.query = MagicMock(side_effect=Exception("DB query error"))

    with pytest.raises(
        BusinessRuleViolationError,
        match="Failed to complete post-verification workflow",
    ):
        await service._handle_post_verification(mock_user)


@pytest.mark.asyncio
async def test_handle_post_verification_already_has_role(dummy_db, mock_user):
    """
    Test that _handle_post_verification does nothing when the user already has the "verified_user" role.

    This test simulates the scenario where the user already possesses the "verified_user" role.
    In that case, the method should skip querying the database and simply log the completion of post‐verification
    without modifying the user's roles.

    Expected Outcome:
        - The user's roles remain unchanged.
        - No database query is performed (i.e. dummy_db.query is not used).
    """
    # Pre-assign the verified_user role.
    preexisting_role = Role(id=1, name="verified_user", is_active=True)
    mock_user.roles = [preexisting_role]
    service = EmailVerificationService(dummy_db)
    # Override dummy_db.query with a MagicMock that should not be used.
    dummy_db.query = MagicMock()

    await service._handle_post_verification(mock_user)

    # Ensure that the roles list remains unchanged.
    assert len(mock_user.roles) == 1
    assert mock_user.roles[0].name == "verified_user"


@pytest.mark.asyncio
async def test_verify_email_user_not_found(dummy_db):
    """
    Test that verify_email raises a BusinessRuleViolationError when the user is not found.

    This test simulates the scenario where get_user fails (e.g. because the user does not exist).
    In that case, the exception from get_user should trigger the generic exception branch in verify_email.
    The method must rollback the database transaction and then raise a BusinessRuleViolationError
    with the message "Email verification failed".

    Expected Outcome:
        - A BusinessRuleViolationError is raised with the appropriate error message.
        - The database rollback method is called exactly once.
    """
    service = EmailVerificationService(dummy_db)
    # Simulate get_user throwing an exception (user not found)
    service.get_user = AsyncMock(side_effect=Exception("User not found"))
    dummy_db.rollback = AsyncMock()

    with pytest.raises(BusinessRuleViolationError, match="Email verification failed"):
        await service.verify_email(999)
    dummy_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_can_verify_email_exception_handling(dummy_db, mock_user):
    """
    Test that _can_verify_email returns False when an exception occurs during its execution.

    This test simulates an exception by patching the _has_completed_onboarding method to raise
    an exception. The except block should catch this error, log it, and cause _can_verify_email to
    return False.

    Expected Outcome:
        - _can_verify_email returns False.
    """
    service = EmailVerificationService(dummy_db)
    # Patch _has_completed_onboarding to raise an exception.
    service._has_completed_onboarding = AsyncMock(
        side_effect=Exception("Simulated error")
    )

    # Configure mock_user with valid data so that if no error occurred, verification would pass.
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"

    result = await service._can_verify_email(mock_user)
    assert result is False
