"""
This module contains test cases for the phone_validator module.

Functions:
    - None

Classes:
    - TestValidatePhoneNumber: Test cases for the validate_phone_number function.

Exceptions:
    - None

Constants:
    - None
"""

import pytest
from pydantic.fields import FieldInfo
from app.services.phone_validator import validate_phone_number


class MockField:
    """
    A mock object to simulate a Pydantic Field with a `name` attribute.
    """

    def __init__(self, name: str):
        self.name = name


class TestValidatePhoneNumber:
    """
    Test cases for the validate_phone_number function.
    """

    def test_valid_phone_number(self):
        """
        Validate that a valid E.164 formatted phone number is returned as is.
        """
        valid_number = "+14155552671"
        result = validate_phone_number(valid_number)
        assert result == valid_number

    def test_valid_phone_number_with_formatting(self):
        """
        Validate that a valid but formatted phone number is normalized to E.164.
        """
        formatted_number = "(415) 555-2671"
        expected = "+14155552671"  # Assuming default country code is '1' (US)
        result = validate_phone_number(formatted_number)
        assert result == expected

    def test_invalid_phone_number(self):
        """
        Validate that an invalid phone number raises a ValueError.
        """
        invalid_number = "12345"
        with pytest.raises(ValueError) as exc_info:
            validate_phone_number(invalid_number)
        assert (
            "Phone number must be a valid international format (e.g., +14155552671)."
            in str(exc_info.value)
        )

    def test_invalid_phone_number_with_field(self):
        """
        Validate that an invalid phone number raises a ValueError with field context.
        """
        invalid_number = "12345"
        mock_field = MockField(name="mobile_number")
        with pytest.raises(ValueError) as exc_info:
            validate_phone_number(invalid_number, mock_field)
        assert (
            "Phone number for field mobile_number must be a valid international format"
            in str(exc_info.value)
        )

    def test_valid_phone_number_with_field(self):
        """
        Validate that a valid phone number is returned with no error when a field is provided.
        """
        valid_number = "+14155552671"
        field = FieldInfo(name="mobile_number")
        result = validate_phone_number(valid_number, field)
        assert result == valid_number

    def test_empty_phone_number(self):
        """
        Validate that None is returned when no phone number is provided.
        """
        result = validate_phone_number(None)
        assert result is None

    def test_numberparse_exception(self):
        """
        Validate that a NumberParseException is handled correctly.
        """
        invalid_number = "InvalidNumber"
        with pytest.raises(ValueError) as exc_info:
            validate_phone_number(invalid_number)
        assert "Phone number must be a valid international format" in str(
            exc_info.value
        )
