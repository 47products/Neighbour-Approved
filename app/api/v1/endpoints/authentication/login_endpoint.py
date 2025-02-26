"""
Login Endpoint Module for Neighbour Approved Authentication.

This module defines the POST /api/v1/auth/login endpoint, which authenticates a user
using provided credentials and returns a JWT access token. This endpoint adheres to the
Neighbour Approved API design and documentation standards.

Endpoint:
    POST /login: Authenticate a user and return an access token.

Dependencies:
    - FastAPI for endpoint routing and error handling.
    - Pydantic schemas (LoginRequest, TokenResponse) for request validation and response serialization.
    - User service function (authenticate_user) for performing user authentication.
"""

from fastapi import APIRouter, HTTPException, status
from app.api.v1.schemas.auth_schema import LoginRequest, TokenResponse
from app.services.user_service.authentication import authenticate_user

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and get access token",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "User authenticated successfully and access token returned."
        },
        401: {"description": "Invalid credentials or authentication failure."},
    },
)
def login_endpoint(login_request: LoginRequest) -> TokenResponse:
    """
    Authenticate a user and return a JWT access token.

    This endpoint accepts user credentials in the form of a LoginRequest, verifies the
    credentials via the user authentication service, and returns a JWT access token along
    with token metadata. This token can then be used for subsequent authenticated requests.

    Args:
        login_request (LoginRequest): A Pydantic model containing:
            - email (str): The user's email address.
            - password (str): The user's plain-text password.

    Returns:
        TokenResponse: A Pydantic model containing:
            - access_token (str): The JWT access token.
            - token_type (str): The type of token (typically "bearer").
            - expires_in (int): Token expiration time in seconds.

    Raises:
        HTTPException: If authentication fails due to invalid email or password.

    Example:
        **Request:**
            POST /api/v1/auth/login
            {
                "email": "user@example.com",
                "password": "securepassword123"
            }

        **Response:**
            {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
    """
    token_data = authenticate_user(login_request.email, login_request.password)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return token_data
