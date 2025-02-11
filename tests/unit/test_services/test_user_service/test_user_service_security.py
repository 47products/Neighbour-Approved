"""
Unit tests for the SecurityService module.

This module tests the SecurityService class, which manages password hashing,
verification, and strength validation for secure user authentication.

Tested Methods:
    - hash_password: Generates a bcrypt hash for a given plaintext password.
      Tests cover successful hashing, password strength validation failures,
      and exception handling.
    - verify_password: Checks whether a plaintext password matches a stored hash.
      Tests cover successful verification and error handling when exceptions occur.
    - _validate_password_strength: Validates that a password meets security criteria.
      Tests cover valid passwords as well as various failure conditions such as:
        * Too short
        * Missing uppercase letters
        * Missing lowercase letters
        * Missing digits
        * Missing special characters

To run the tests, use:
    pytest path/to/test_security.py

Dependencies:
    - pytest
    - bcrypt (used internally by SecurityService)
    - unittest.mock for monkeypatching
"""

import bcrypt
import pytest
from app.services.user_service.user_service_security import SecurityService
from app.services.service_exceptions import ValidationError


# --- Tests for hash_password ---


def test_hash_password_valid():
    """
    Test that hash_password returns a valid bcrypt hash when the password meets all requirements.

    Verifies that:
      - The returned hash is a string.
      - The hash can be verified by bcrypt.checkpw.
    """
    service = SecurityService()
    password = "SecureP@ssw0rd!"
    hashed = service.hash_password(password)
    assert isinstance(hashed, str)
    # Verify that the hash matches the password using bcrypt.checkpw.
    assert bcrypt.checkpw(password.encode(), hashed.encode())


def test_hash_password_invalid():
    """
    Test that hash_password raises a ValidationError if the password does not meet requirements.

    Uses a password that is too short and missing several required character types.
    """
    service = SecurityService()
    invalid_password = "short"
    with pytest.raises(ValidationError) as exc_info:
        service.hash_password(invalid_password)
    # Verify that the exception details mention the minimum length requirement.
    assert any("at least" in failure for failure in exc_info.value.details)


def test_hash_password_exception(monkeypatch):
    """
    Test that hash_password raises a ValueError if an unexpected error occurs during password hashing.

    This is simulated by monkeypatching _validate_password_strength to raise a RuntimeError.
    """
    service = SecurityService()

    def fake_validate(_):
        raise RuntimeError("Unexpected error")

    monkeypatch.setattr(service, "_validate_password_strength", fake_validate)
    with pytest.raises(ValueError, match="Password hashing failed"):
        service.hash_password("AnyValidP@ss1!")


# --- Tests for verify_password ---


def test_verify_password_success():
    """
    Test that verify_password returns True when the password matches the stored hash.

    Hashes a valid password and then verifies it.
    """
    service = SecurityService()
    password = "SecureP@ssw0rd!"
    hashed = service.hash_password(password)
    result = service.verify_password(hashed, password)
    assert result is True


def test_verify_password_failure():
    """
    Test that verify_password returns False when the password does not match the stored hash.

    Uses a correct hash but provides an incorrect password.
    """
    service = SecurityService()
    password = "SecureP@ssw0rd!"
    wrong_password = "WrongPassword1!"
    hashed = service.hash_password(password)
    result = service.verify_password(hashed, wrong_password)
    assert result is False


def test_verify_password_exception(monkeypatch):
    """
    Test that verify_password returns False if an exception occurs during password verification.

    This is simulated by monkeypatching bcrypt.checkpw to raise a RuntimeError.
    """
    service = SecurityService()

    def fake_checkpw(a, b):
        raise RuntimeError("Simulated error")

    monkeypatch.setattr(
        "app.services.user_service.user_service_security.bcrypt.checkpw", fake_checkpw
    )
    result = service.verify_password("fakehash", "anyPassword")
    assert result is False


# --- Tests for _validate_password_strength ---


def test_validate_password_strength_valid():
    """
    Test that _validate_password_strength returns valid=True for a strong password.

    The password meets all criteria.
    """
    service = SecurityService()
    password = "StrongP@ssw0rd!"
    result = service._validate_password_strength(password)
    assert result["valid"] is True
    assert result["failures"] == []


def test_validate_password_strength_too_short():
    """
    Test that _validate_password_strength returns valid=False for a password that is too short.

    The failure message should indicate the minimum length requirement.
    """
    service = SecurityService()
    password = "S@1a"  # Too short
    result = service._validate_password_strength(password)
    assert result["valid"] is False
    assert any("at least" in failure for failure in result["failures"])


def test_validate_password_strength_missing_uppercase():
    """
    Test that _validate_password_strength returns valid=False if the password is missing an uppercase letter.
    """
    service = SecurityService()
    password = "securep@ssw0rd!"
    result = service._validate_password_strength(password)
    assert result["valid"] is False
    assert any("uppercase" in failure for failure in result["failures"])


def test_validate_password_strength_missing_lowercase():
    """
    Test that _validate_password_strength returns valid=False if the password is missing a lowercase letter.
    """
    service = SecurityService()
    password = "SECUREP@SSW0RD!"
    result = service._validate_password_strength(password)
    assert result["valid"] is False
    assert any("lowercase" in failure for failure in result["failures"])


def test_validate_password_strength_missing_digit():
    """
    Test that _validate_password_strength returns valid=False if the password is missing a number.
    """
    service = SecurityService()
    password = "SecureP@ssword!"
    result = service._validate_password_strength(password)
    assert result["valid"] is False
    assert any("number" in failure for failure in result["failures"])


def test_validate_password_strength_missing_special():
    """
    Test that _validate_password_strength returns valid=False if the password is missing a special character.
    """
    service = SecurityService()
    password = "SecurePassw0rd"
    result = service._validate_password_strength(password)
    assert result["valid"] is False
    assert any("special" in failure for failure in result["failures"])
