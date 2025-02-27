"""
Login Endpoint Module for Neighbour Approved Authentication.

This module defines the POST /auth/login endpoint, which authenticates a user
using provided credentials and returns a JWT access token. The endpoint validates
incoming requests using the LoginRequest schema and delegates the authentication
logic to the AuthenticationService. Upon successful authentication, a JWT token is
generated and returned in a TokenResponse.

Endpoint:
    POST /auth/login: Authenticate a user and return an access token.

Dependencies:
    - FastAPI for routing and error handling.
    - Pydantic schemas (LoginRequest, TokenResponse) for request validation and response serialization.
    - AuthenticationService for performing authentication operations.
    - SecurityService for password verification.
    - Database session dependency.
    - Application settings for token generation.
"""

from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, HTTPException, status, Depends
from app.api.v1.schemas.authentication_schema import LoginRequest, TokenResponse
from app.core.config import get_settings
from app.services.user_service.authentication import AuthenticationService
from app.db.database_session_management import get_db
from app.services.user_service.security import SecurityService

router = APIRouter()


def create_access_token(subject: str, expires_delta: timedelta, settings) -> str:
    """
    Create a JWT access token.

    Args:
        subject (str): The subject claim, typically the user ID.
        expires_delta (timedelta): Time delta for token expiration.
        settings: Application settings, providing SECRET_KEY and ALGORITHM.

    Returns:
        str: Encoded JWT token.
    """
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire}
    token = jwt.encode(
        to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM
    )
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


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
async def login_endpoint(
    login_request: LoginRequest,
    db=Depends(get_db),
    security_service: SecurityService = Depends(),
):
    """Authenticate a user and return a JWT access token."""
    settings = get_settings()
    # Instantiate the authentication service with dependencies
    auth_service = AuthenticationService(db, security_service)
    try:
        user, is_first_login = await auth_service.authenticate_user(
            login_request.email, login_request.password
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from e

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    # Generate JWT token using the user's ID as the subject
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=expires_delta, settings=settings
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds()),
    )
