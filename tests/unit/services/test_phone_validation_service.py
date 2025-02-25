"""
Unit tests for the phone_validation_service module.

This module tests the functionality of the `validate_phone_number` function,
which ensures that phone numbers conform to the E.164 international standard.
The tests cover valid inputs (both in national and E.164 formats), invalid inputs
that either fail validation or cannot be parsed, and the inclusion of field context
in error messages when provided.

Usage:
    $ pytest test_phone_validation_service.py

Dependencies:
    - pytest
    - phonenumbers
    - pydantic
"""

import pytest
import phonenumbers
from app.services.phone_validation_service import validate_phone_number


class DummyField:
    """
    Dummy field object to simulate a Pydantic Field with a name attribute.

    This is used to test that the error message correctly includes the field name.
    """

    def __init__(self, name: str):
        self.name = name


def test_valid_phone_number_national_format():
    """
    Test that a valid US phone number in national format is correctly formatted to E.164.

    Example:
        Input: "4155552671"
        Expected Output: "+14155552671"
    """
    input_number = "4155552671"
    expected = "+14155552671"
    result = validate_phone_number(input_number)
    assert result == expected, f"Expected {expected}, got {result}"


def test_valid_phone_number_e164_format():
    """
    Test that a valid phone number already in E.164 format is returned unchanged.

    Example:
        Input: "+14155552671"
        Expected Output: "+14155552671"
    """
    input_number = "+14155552671"
    expected = "+14155552671"
    result = validate_phone_number(input_number)
    assert result == expected, f"Expected {expected}, got {result}"


def test_invalid_phone_number_not_valid():
    """
    Test that a phone number that can be parsed but is not valid raises a ValueError.

    Example:
        Input: "123" (parsed but not a valid number)
    """
    input_number = "123"
    with pytest.raises(ValueError) as excinfo:
        validate_phone_number(input_number)
    expected_msg = (
        "Phone number must be a valid international format (e.g., +14155552671)."
    )
    assert expected_msg in str(
        excinfo.value
    ), "Error message did not match expected output."


def test_invalid_phone_number_with_field():
    """
    Test that an invalid phone number raises a ValueError including the field name when provided.

    The error message should include the field context, e.g., "for field phone".
    """
    input_number = "123"
    dummy_field = DummyField("phone")
    with pytest.raises(ValueError) as excinfo:
        validate_phone_number(input_number, field=dummy_field)
    expected_msg = "Phone number for field phone must be a valid international format (e.g., +14155552671)."
    assert expected_msg in str(
        excinfo.value
    ), "Error message does not include the field name as expected."


def test_phone_number_parse_exception():
    """
    Test that a phone number that cannot be parsed raises a ValueError.

    Example:
        Input: "abcd" should trigger phonenumbers.NumberParseException and be re-raised as ValueError.
    """
    input_number = "abcd"
    with pytest.raises(ValueError) as excinfo:
        validate_phone_number(input_number)
    expected_msg = (
        "Phone number must be a valid international format (e.g., +14155552671)."
    )
    assert expected_msg in str(
        excinfo.value
    ), "Error message for parse exception did not match expected output."


def test_none_input():
    """
    Test that if the input phone number is None, the function returns None.
    """
    result = validate_phone_number(None)
    assert result is None, "Expected None when input is None."


def test_empty_string_input():
    """
    Test that if the input phone number is an empty string, the function returns an empty string.
    """
    result = validate_phone_number("")
    assert result == "", "Expected an empty string when input is empty."
