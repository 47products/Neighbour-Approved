"""
Dependencies Module for Authentication and Common Endpoints.

This module provides dependency functions for the Neighbour Approved API,
including authentication dependencies that retrieve and validate JWT tokens
to identify the current authenticated user. These dependencies are used across
the authentication endpoints as well as in other protected endpoints.

Functions:
    get_token_from_header(authorization: Optional[str]) -> str
        Extracts the JWT token from the Authorization header.

    get_current_user(token: str) -> Dict[str, Any]
        Decodes and validates the JWT token to return the current user's details.
"""

from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
import jwt  # PyJWT library is assumed to be installed
from app.core.config import get_settings

settings = get_settings()  # Assumes settings.SECRET_KEY and settings.ALGORITHM exist


def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract the JWT token from the Authorization header.

    Args:
        authorization (Optional[str]): The value of the Authorization header.
            Expected format: 'Bearer <token>'.

    Returns:
        str: The extracted JWT token.

    Raises:
        HTTPException: If the Authorization header is missing or is not in the correct format.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    parts = authorization.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'.",
        )
    return parts[1]


def get_current_user(token: str = Depends(get_token_from_header)) -> Dict[str, Any]:
    """
    Retrieve the current authenticated user by validating the provided JWT token.

    This dependency extracts the JWT token via the get_token_from_header dependency,
    decodes it using the application's secret key and algorithm, and returns the token payload,
    which should include user identification data (such as user ID and email).

    Args:
        token (str): The JWT token extracted from the Authorization header.

    Returns:
        Dict[str, Any]: A dictionary containing user information from the token payload.

    Raises:
        HTTPException: If the token has expired or is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
        )
    return payload
