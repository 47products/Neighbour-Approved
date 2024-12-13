"""
This module defines the schemas for user-related data.

The schemas define the structure of user data required for creating a new user,
updating an existing user, and returning user data in API responses.

The schemas also define the structure of user data as stored in the database.

Classes:
    ContactResponse: Schema for contact data returned in user-related responses.
    UserCreate: Schema for user data required for creating a new user.
    UserResponse: Schema for user data returned in API responses.
    UserUpdate: Schema for user data required for updating an existing user.
    UserInDB: Schema for user data as stored in the database.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.services.phone_validator import validate_phone_number


class ContactResponse(BaseModel):
    """
    ContactResponse Schema.

    Defines the structure of contact data returned in user-related responses.

    Attributes:
        id (int): Unique identifier of the contact.
        name (str): Name of the contact.
        service (str): Type of service provided by the contact.
        rating (float): Average rating of the contact.
    """

    id: int
    name: str
    service: str
    rating: float

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """
    UserCreate Schema.

    Defines the structure of user data required for creating a new user.

    Attributes:
        email (EmailStr): Unique email address of the user.
        password (str): Plain-text password of the user.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        mobile_number (Optional[str]): Mobile number of the user in E.164 format (e.g., +123456789).
        postal_address (Optional[str]): Postal address of the user.
        physical_address (Optional[str]): Physical address of the user.
        country (Optional[str]): Country of the user.
    """

    email: EmailStr = Field(..., description="Unique email address of the user.")
    password: str = Field(
        ..., min_length=8, description="Plain-text password of the user."
    )
    first_name: str = Field(..., max_length=50, description="First name of the user.")
    last_name: str = Field(..., max_length=50, description="Last name of the user.")
    mobile_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Mobile number of the user in E.164 format (e.g., +123456789).",
    )
    postal_address: Optional[str] = Field(
        None, max_length=200, description="Postal address of the user."
    )
    physical_address: Optional[str] = Field(
        None, max_length=200, description="Physical address of the user."
    )
    country: Optional[str] = Field(
        None, max_length=50, description="Country of the user."
    )

    @field_validator("mobile_number")
    def validate_mobile_number(cls, v):
        """Validate the mobile number using the phone number validator."""
        return validate_phone_number(v)


class UserResponse(BaseModel):
    """
    UserResponse Schema.

    Defines the structure of user data returned in API responses.

    Attributes:
        id (int): Unique identifier of the user.
        email (EmailStr): Unique email address of the user.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        mobile_number (Optional[str]): Mobile number of the user in E.164 format.
        postal_address (Optional[str]): Postal address of the user.
        physical_address (Optional[str]): Physical address of the user.
        country (Optional[str]): Country of the user.
        created_at (Optional[str]): Timestamp when the user was created.
        updated_at (Optional[str]): Timestamp when the user was last updated.
        is_active (bool): Indicates whether the user account is active.
        contacts (List[ContactResponse]): List of contacts associated with the user.
    """

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    mobile_number: Optional[str]
    postal_address: Optional[str]
    physical_address: Optional[str]
    country: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_active: bool
    contacts: List[ContactResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """
    UserUpdate Schema.

    Defines the structure of user data for updating an existing user.

    Attributes:
        email (Optional[EmailStr]): Unique email address of the user.
        password (Optional[str]): New plain-text password of the user.
        first_name (Optional[str]): First name of the user.
        last_name (Optional[str]): Last name of the user.
        mobile_number (Optional[str]): Mobile number of the user in E.164 format.
        postal_address (Optional[str]): Postal address of the user.
        physical_address (Optional[str]): Physical address of the user.
        country (Optional[str]): Country of the user.
        is_active (Optional[bool]): Indicates whether the user account is active.
    """

    email: Optional[EmailStr] = Field(
        None, description="Unique email address of the user."
    )
    password: Optional[str] = Field(
        None, min_length=8, description="New plain-text password of the user."
    )
    first_name: Optional[str] = Field(
        None, max_length=50, description="First name of the user."
    )
    last_name: Optional[str] = Field(
        None, max_length=50, description="Last name of the user."
    )
    mobile_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Mobile number of the user in E.164 format (e.g., +123456789).",
    )
    postal_address: Optional[str] = Field(
        None, max_length=200, description="Postal address of the user."
    )
    physical_address: Optional[str] = Field(
        None, max_length=200, description="Physical address of the user."
    )
    country: Optional[str] = Field(
        None, max_length=50, description="Country of the user."
    )
    is_active: Optional[bool] = Field(
        None, description="Indicates whether the user account is active."
    )

    @field_validator("mobile_number")
    # pylint: disable=no-self-argument
    def validate_mobile_number(cls, v):
        """Validate the mobile number using the phone number validator."""
        return validate_phone_number(v)


class UserInDB(BaseModel):
    """
    UserInDB Schema.

    Defines the structure of user data as stored in the database.

    Attributes:
        id (int): Unique identifier of the user.
        email (EmailStr): Unique email address of the user.
        password (str): Hashed password of the user.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        mobile_number (Optional[str]): Mobile number of the user in E.164 format.
        postal_address (Optional[str]): Postal address of the user.
        physical_address (Optional[str]): Physical address of the user.
        country (Optional[str]): Country of the user.
        created_at (Optional[str]): Timestamp when the user was created.
        updated_at (Optional[str]): Timestamp when the user was last updated.
        is_active (bool): Indicates whether the user account is active.
        contacts (List[ContactResponse]): List of contacts associated with the user.
    """

    id: int
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    mobile_number: Optional[str]
    postal_address: Optional[str]
    physical_address: Optional[str]
    country: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_active: bool
    contacts: List[ContactResponse] = []

    model_config = ConfigDict(from_attributes=True)
