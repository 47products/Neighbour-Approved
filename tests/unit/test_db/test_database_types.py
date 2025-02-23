"""
Unit tests for the database_types module in the Neighbour Approved application.

This module tests:
- TZDateTime: A custom SQLAlchemy TypeDecorator that enforces timezone-aware datetimes,
  ensuring values are stored in UTC.
- PrivacyLevel: An enumeration representing community privacy levels.
- create_email_check_constraint: A helper function that returns a CheckConstraint
  for validating email addresses.

Typical usage example:
    pytest tests/unit/test_database_types.py

Dependencies:
    - pytest
    - SQLAlchemy
    - The database_types module under test
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import Table, MetaData, Column, text, CheckConstraint
from sqlalchemy.types import DateTime
from app.db.database_types import (
    TZDateTime,
    PrivacyLevel,
    create_email_check_constraint,
)


def test_tzdatetime_python_type():
    """
    Test that TZDateTime.python_type returns datetime.
    """
    tz_type = TZDateTime()
    assert tz_type.python_type == datetime


def test_tzdatetime_process_bind_param_naive():
    """
    Test that process_bind_param raises ValueError if datetime is naive.
    """
    tz_type = TZDateTime()
    naive_dt = datetime(2024, 1, 1, 12, 0, 0)  # No tzinfo

    with pytest.raises(ValueError, match="Timezone aware datetime is required"):
        tz_type.process_bind_param(naive_dt, dialect=None)


def test_tzdatetime_process_bind_param_aware():
    """
    Test that process_bind_param converts aware datetimes to UTC.
    """
    tz_type = TZDateTime()

    # E.g., US/Eastern is UTC-5 or UTC-4 depending on DST, but let's just pick an offset
    offset_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
    result = tz_type.process_bind_param(offset_dt, dialect=None)

    # Should be converted to UTC
    assert result.utcoffset() == timedelta(0)
    assert result.hour == 17  # 12 - (-5) = 17 in 24-hour time


def test_tzdatetime_process_bind_param_none():
    """
    Test that process_bind_param returns None if the value is None.
    """
    tz_type = TZDateTime()
    assert tz_type.process_bind_param(None, dialect=None) is None


def test_tzdatetime_process_bind_param_return_none():
    """
    Explicitly cover the path where value is None,
    triggering the final 'return value' line (line 43).
    """
    tz_type = TZDateTime()
    result = tz_type.process_bind_param(None, dialect=None)
    assert result is None


def test_tzdatetime_process_result_value():
    """
    Test that process_result_value returns a datetime with UTC tzinfo.
    """
    tz_type = TZDateTime()

    # Suppose the DB returned a naive datetime (common in many DBs):
    db_value = datetime(2024, 1, 1, 10, 30, 0)
    result = tz_type.process_result_value(db_value, dialect=None)
    assert result.tzinfo == timezone.utc
    assert result.year == 2024
    assert result.hour == 10


def test_tzdatetime_process_literal_param():
    """
    Test that process_literal_param formats a datetime as TIMESTAMP literal
    (or None if the value is None).
    """
    tz_type = TZDateTime()
    aware_dt = datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    literal = tz_type.process_literal_param(aware_dt, dialect=None)
    # Check that it's something like TIMESTAMP '2024-01-01 09:00:00'
    assert "TIMESTAMP '2024-01-01 09:00:00" in literal

    # None case
    assert tz_type.process_literal_param(None, dialect=None) is None


def test_tzdatetime_in_table():
    """
    Test that TZDateTime can be used in a SQLAlchemy table definition.
    Verifies that the column is recognized as a DateTime at the DB level.
    """
    metadata = MetaData()
    col = Column("created_at", TZDateTime())
    table = Table("test_table_tz", metadata, col)

    # Confirm the column is recognized
    assert "created_at" in table.c
    assert isinstance(table.c.created_at.type.impl, DateTime)


def test_privacy_level_enum_values():
    """
    Test that PrivacyLevel enum has expected members and that .values() returns the list of strings.
    """
    assert PrivacyLevel.PUBLIC.value == "public"
    assert PrivacyLevel.PRIVATE.value == "private"
    assert PrivacyLevel.INVITATION_ONLY.value == "invitation_only"

    all_values = PrivacyLevel.values()
    assert sorted(all_values) == ["invitation_only", "private", "public"]


def test_create_email_check_constraint():
    """
    Test that create_email_check_constraint returns a CheckConstraint with the expected name and expression.
    """
    c = create_email_check_constraint("email_field")
    assert isinstance(c, CheckConstraint)
    assert c.name == "valid_email_field_format"
    # Ensure we see the case-insensitive regex operator
    assert "email_field ~*" in c.sqltext.text
    # Also confirm it allows NULL or a valid email pattern
    assert "IS NULL" in c.sqltext.text
