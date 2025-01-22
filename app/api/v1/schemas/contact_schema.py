"""
This module defines the schemas for contact-related data within the Neighbour Approved application.

The schemas facilitate data validation and serialization for creating new contacts,
updating existing contacts, and returning contact data in API responses.

Classes:
    ContactCreate: Schema for contact data required for creating a new contact.
    ContactUpdate: Schema for contact data required for updating an existing contact.
    ContactResponse: Schema for contact data returned in API responses.
    ContactInDB: Schema for contact data as stored in the database.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.services.phone_validation_service import validate_phone_number


class ContactCreate(BaseModel):
    """
    ContactCreate Schema.

    Defines the structure and validation rules for creating a new contact.

    Attributes:
        contact_name (str): Name of the contact.
        email (EmailStr): Unique email address of the contact.
        contact_number (Optional[str]): Mobile number of the contact in E.164
            format (e.g., +123456789).
        primary_contact_first_name (str): First name of the primary contact person.
        primary_contact_last_name (str): Last name of the primary contact person.
        primary_contact_contact_number (Optional[str]): Mobile number of the primary contact person
            in E.164 format.
        categories (str): Categories associated with the contact.
        services (str): Services offered by the contact.
        user_id (int): ID of the user associated with this contact.
    """

    contact_name: str = Field(..., max_length=100, description="Name of the contact.")
    email: EmailStr = Field(..., description="Unique email address of the contact.")
    contact_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Mobile number of the contact in E.164 format (e.g., +123456789).",
    )
    primary_contact_first_name: str = Field(
        ..., max_length=50, description="First name of the primary contact person."
    )
    primary_contact_last_name: str = Field(
        ..., max_length=50, description="Last name of the primary contact person."
    )
    primary_contact_contact_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Mobile number of the primary contact person in E.164 format.",
    )
    categories: str = Field(..., description="Categories associated with the contact.")
    services: str = Field(..., description="Services offered by the contact.")
    user_id: int = Field(
        ..., description="ID of the user associated with this contact."
    )

    @field_validator("contact_number", "primary_contact_contact_number")
    def validate_contact_fields(cls, v, field):
        """Validate the mobile number using the phone number validator."""
        return validate_phone_number(v, field)


class ContactUpdate(BaseModel):
    """
    ContactUpdate Schema.

    Defines the structure and validation rules for updating an existing contact.

    Attributes:
        contact_name (Optional[str]): Name of the contact.
        email (Optional[EmailStr]): Unique email address of the contact.
        contact_number (Optional[str]): Mobile number of the contact in E.164 format.
        primary_contact_first_name (Optional[str]): First name of the primary contact person.
        primary_contact_last_name (Optional[str]): Last name of the primary contact person.
        primary_contact_contact_number (Optional[str]): Mobile number of the primary contact person
            in E.164 format.
        categories (Optional[str]): Categories associated with the contact.
        services (Optional[str]): Services offered by the contact.
        endorsements (Optional[int]): Number of endorsements for the contact.
    """

    contact_name: Optional[str] = Field(
        None, max_length=100, description="Name of the contact."
    )
    email: Optional[EmailStr] = Field(
        None, description="Unique email address of the contact."
    )
    contact_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Mobile number of the contact in E.164 format (e.g., +123456789).",
    )
    primary_contact_first_name: Optional[str] = Field(
        None, max_length=50, description="First name of the primary contact person."
    )
    primary_contact_last_name: Optional[str] = Field(
        None, max_length=50, description="Last name of the primary contact person."
    )
    primary_contact_contact_number: Optional[str] = Field(
        None,
        max_length=20,
        description="Mobile number of the primary contact person in E.164 format.",
    )
    categories: Optional[str] = Field(
        None, description="Categories associated with the contact."
    )
    services: Optional[str] = Field(
        None, description="Services offered by the contact."
    )
    endorsements: Optional[int] = Field(
        None, description="Number of endorsements for the contact."
    )

    @field_validator("contact_number", "primary_contact_contact_number")
    def validate_contact_fields(cls, v, field):
        """Validate the mobile number using the phone number validator."""
        return validate_phone_number(v, field)


class ContactResponse(BaseModel):  # pylint: disable=missing-class-docstring
    """
    ContactResponse Schema.

    Defines the structure of contact data returned in API responses.

    Attributes:
        id (int): Unique identifier of the contact.
        contact_name (str): Name of the contact.
        email (EmailStr): Unique email address of the contact.
        contact_number (Optional[str]): Mobile number of the contact in E.164 format.
        primary_contact_first_name (str): First name of the primary contact person.
        primary_contact_last_name (str): Last name of the primary contact person.
        primary_contact_contact_number (Optional[str]): Mobile number of the primary contact person
            in E.164 format.
        categories (str): Categories associated with the contact.
        services (str): Services offered by the contact.
        endorsements (int): Number of endorsements for the contact.
        user_id (int): ID of the user associated with this contact.
    """

    id: int
    contact_name: str
    email: EmailStr
    contact_number: Optional[str]
    primary_contact_first_name: str
    primary_contact_last_name: str
    primary_contact_contact_number: Optional[str]
    categories: str
    services: str
    endorsements: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class ContactInDB(BaseModel):  # pylint: disable=missing-class-docstring
    """
    ContactInDB Schema.

    Defines the structure of contact data as stored in the database.

    Attributes:
        id (int): Unique identifier of the contact.
        contact_name (str): Name of the contact.
        email (EmailStr): Unique email address of the contact.
        contact_number (Optional[str]): Mobile number of the contact in E.164 format.
        primary_contact_first_name (str): First name of the primary contact person.
        primary_contact_last_name (str): Last name of the primary contact person.
        primary_contact_contact_number (Optional[str]): Mobile number of the primary contact person
            in E.164 format.
        categories (str): Categories associated with the contact.
        services (str): Services offered by the contact.
        endorsements (int): Number of endorsements for the contact.
        user_id (int): ID of the user associated with this contact.
    """

    id: int
    contact_name: str
    email: EmailStr
    contact_number: Optional[str]
    primary_contact_first_name: str
    primary_contact_last_name: str
    primary_contact_contact_number: Optional[str]
    categories: str
    services: str
    endorsements: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
