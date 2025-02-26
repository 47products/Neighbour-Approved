"""
Unit tests for the dependencies module in the Neighbour Approved API.

This module tests the functionality of:
    - get_token_from_header: Extracts the JWT token from the Authorization header.
    - get_current_user: Decodes and validates the JWT token to retrieve the current user.

These tests verify both successful extraction/decoding and error cases.

Note:
    These tests require the PyJWT library. Ensure that PyJWT is installed and that
    no conflicting jwt packages are present.
"""

import pytest
from fastapi import HTTPException, status
from jwt import encode, ExpiredSignatureError, InvalidTokenError
from app.api.v1.dependencies import get_token_from_header, get_current_user
from app.core.config import get_settings


@pytest.fixture
def settings():
    """
    Fixture to retrieve the application settings.

    Returns:
        Settings: The application configuration settings.
    """
    return get_settings()


@pytest.fixture
def valid_payload():
    """
    Fixture to provide a valid token payload.

    Returns:
        dict: A dictionary containing user information.
    """
    return {"user_id": 1, "email": "test@example.com"}


@pytest.fixture
def valid_token(settings, valid_payload):
    """
    Fixture to generate a valid JWT token using the settings' secret and algorithm.

    Args:
        settings: The application settings fixture.
        valid_payload: A valid payload dictionary fixture.

    Returns:
        str: A JWT token string.
    """
    token = encode(
        valid_payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def test_get_token_from_header_missing():
    """
    Test that get_token_from_header raises an HTTPException when the header is missing.
    """
    with pytest.raises(HTTPException) as exc_info:
        get_token_from_header(None)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Missing Authorization header." in str(exc_info.value.detail)


def test_get_token_from_header_invalid_format():
    """
    Test that get_token_from_header raises an HTTPException for an improperly formatted header.
    """
    # Case: Header does not start with "Bearer"
    header_value = "Basic sometoken"
    with pytest.raises(HTTPException) as exc_info:
        get_token_from_header(header_value)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid Authorization header format" in str(exc_info.value.detail)

    # Case: Header has too many parts
    header_value = "Bearer token extra"
    with pytest.raises(HTTPException) as exc_info:
        get_token_from_header(header_value)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid Authorization header format" in str(exc_info.value.detail)


def test_get_token_from_header_valid():
    """
    Test that get_token_from_header successfully extracts the token from a correctly formatted header.
    """
    token = "sampletoken"
    header_value = f"Bearer {token}"
    result = get_token_from_header(header_value)
    assert result == token


def test_get_current_user_valid(settings, valid_token, valid_payload):
    """
    Test that get_current_user returns the correct payload when provided with a valid token.

    Args:
        settings: The application settings fixture.
        valid_token: A valid JWT token fixture.
        valid_payload: The expected payload dictionary.
    """
    user = get_current_user(valid_token)
    assert user == valid_payload


def test_get_current_user_expired(monkeypatch, valid_token):
    """
    Test that get_current_user raises an HTTPException when the token has expired.

    Uses monkeypatch to simulate jwt.decode raising an ExpiredSignatureError.
    """

    def fake_decode(*args, **kwargs):
        raise ExpiredSignatureError("Token expired")

    monkeypatch.setattr("app.api.v1.dependencies.jwt.decode", fake_decode)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(valid_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired." in str(exc_info.value.detail)


def test_get_current_user_invalid(monkeypatch, valid_token):
    """
    Test that get_current_user raises an HTTPException when the token is invalid.

    Uses monkeypatch to simulate jwt.decode raising an InvalidTokenError.
    """

    def fake_decode(*args, **kwargs):
        raise InvalidTokenError("Invalid token")

    monkeypatch.setattr("app.api.v1.dependencies.jwt.decode", fake_decode)
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(valid_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid token." in str(exc_info.value.detail)
