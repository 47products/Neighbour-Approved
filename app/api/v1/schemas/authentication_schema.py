"""
Authentication Schema Module for Neighbour Approved API.

This module defines the Pydantic models used for user authentication. The models include:
    - LoginRequest: Validates user login credentials.
    - TokenResponse: Represents the JWT access token and its associated metadata returned
      upon successful authentication.

Classes:
    LoginRequest: Schema for user login credentials.
    TokenResponse: Schema for the JWT access token response.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Schema for user login credentials.

    Attributes:
        email (EmailStr): The user's email address.
        password (str): The user's plain-text password.
    """

    email: EmailStr = Field(..., description="The user's email address.")
    password: str = Field(
        ..., min_length=8, description="The user's plain-text password."
    )


class TokenResponse(BaseModel):
    """
    Schema for the JWT access token response.

    Attributes:
        access_token (str): The JWT access token.
        token_type (str): The token type, typically 'bearer'.
        expires_in (int): The token expiration time in seconds.
    """

    access_token: str = Field(..., description="The JWT access token.")
    token_type: str = Field(
        default="bearer", description="The type of token, typically 'bearer'."
    )
    expires_in: int = Field(..., description="Token expiration time in seconds.")
