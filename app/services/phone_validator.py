"""
This module provides utilities for validating and formatting phone numbers.

The main function, `validate_phone_number`, ensures that phone numbers conform
to the E.164 international standard. It checks the validity of the provided
phone number and formats it accordingly. If the phone number is invalid, a
detailed error is raised, optionally including the context of the field being
validated.

Functions:
    validate_phone_number: Validates and formats phone numbers in E.164 format.

Dependencies:
    - phonenumbers: Library for parsing, formatting, and validating phone numbers.
"""

from typing import Optional
import phonenumbers
from pydantic import Field


def validate_phone_number(
    v: Optional[str], field: Optional[Field] = None
) -> Optional[str]:
    """
    Validates and formats a phone number in E.164 international format.
    """
    if v:
        try:
            # Attempt to parse the phone number with a default region.
            parsed_number = phonenumbers.parse(v, "US")
            if not phonenumbers.is_valid_number(parsed_number):
                # Extract field name if present, or default to an empty string.
                field_name = f" for field {getattr(field, 'name', '')}" if field else ""
                raise ValueError(
                    f"Phone number{field_name} must be a valid international "
                    "format (e.g., +14155552671)."
                )
        except phonenumbers.NumberParseException as exc:
            # Include the field name in the error message if available.
            field_name = f" for field {getattr(field, 'name', '')}" if field else ""
            raise ValueError(
                f"Phone number{field_name} must be a valid international "
                "format (e.g., +14155552671)."
            ) from exc
        # Return the number formatted in E.164 format.
        return phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.E164
        )
    # Return None if no number is provided.
    return v
