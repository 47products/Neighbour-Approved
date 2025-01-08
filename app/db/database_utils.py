"""Database utility functions and constants."""

from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)

# Common column lengths
DEFAULT_STRING_LENGTH = 255
SHORT_STRING_LENGTH = 50
MEDIUM_STRING_LENGTH = 100
LONG_STRING_LENGTH = 500
NAME_LENGTH = 100
DESCRIPTION_LENGTH = 255
COMMENT_LENGTH = 500
PHONE_LENGTH = 20
EMAIL_LENGTH = 255
POSTAL_LENGTH = 200
SLUG_LENGTH = 100


def create_foreign_key_column(
    target_table: str,
    *,
    nullable: bool = False,
    primary_key: bool = False,
    unique: bool = False,
    index: bool = True,
    doc: Optional[str] = None,
    ondelete: str = "CASCADE",
    name: Optional[str] = None,
) -> Column:
    """Create a standardized foreign key column.

    Args:
        target_table: Name of the referenced table
        nullable: Whether the column can be NULL
        primary_key: Whether this is a primary key
        unique: Whether values must be unique
        index: Whether to create an index
        doc: Column documentation
        ondelete: ON DELETE behavior ("CASCADE", "SET NULL", etc)
        name: Optional custom column name

    Returns:
        SQLAlchemy Column instance
    """
    column_name = name or f"{target_table.rstrip('s')}_id"
    return Column(
        column_name,
        Integer,
        ForeignKey(f"{target_table}.id", ondelete=ondelete),
        nullable=nullable,
        primary_key=primary_key,
        unique=unique,
        index=index,
        doc=doc,
    )


def create_string_column(
    length: int = DEFAULT_STRING_LENGTH,
    *,
    nullable: bool = True,
    unique: bool = False,
    index: bool = False,
    doc: Optional[str] = None,
) -> Column:
    """Create a standardized string column.

    Args:
        length: Maximum string length
        nullable: Whether the column can be NULL
        unique: Whether values must be unique
        index: Whether to create an index
        doc: Column documentation

    Returns:
        SQLAlchemy Column instance
    """
    return Column(
        String(length),
        nullable=nullable,
        unique=unique,
        index=index,
        doc=doc,
    )


def create_boolean_column(
    *,
    default: bool = False,
    nullable: bool = False,
    doc: Optional[str] = None,
) -> Column:
    """Create a standardized boolean column.

    Args:
        default: Default value if not specified
        nullable: Whether the column can be NULL
        doc: Column documentation

    Returns:
        SQLAlchemy Column instance
    """
    return Column(
        Boolean,
        default=default,
        nullable=nullable,
        doc=doc,
    )


def create_unique_constraint(
    *columns: str,
    name: Optional[str] = None,
) -> UniqueConstraint:
    """Create a named unique constraint.

    Args:
        *columns: Column names to include in constraint
        name: Optional constraint name

    Returns:
        SQLAlchemy UniqueConstraint instance
    """
    if name is None:
        name = f"uq_{'_'.join(columns)}"
    return UniqueConstraint(*columns, name=name)


def create_check_constraint(
    condition: str,
    name: Optional[str] = None,
) -> CheckConstraint:
    """Create a named check constraint.

    Args:
        condition: Check condition expression
        name: Optional constraint name

    Returns:
        SQLAlchemy CheckConstraint instance
    """
    return CheckConstraint(condition, name=name)


def validate_phone_number(value: Optional[str]) -> Optional[str]:
    """Validate and format a phone number.

    Args:
        value: Phone number to validate

    Returns:
        Formatted phone number or None

    Raises:
        ValueError: If phone number is invalid
    """
    if not value:
        return None

    # Remove any non-digit characters
    digits = "".join(filter(str.isdigit, value))

    # Basic validation - should be between 10 and 15 digits
    if not 10 <= len(digits) <= 15:
        raise ValueError("Phone number must be between 10 and 15 digits")

    return digits


def create_phone_constraint(column: str) -> CheckConstraint:
    """Create a check constraint for phone numbers.

    Args:
        column: Name of the phone number column

    Returns:
        SQLAlchemy CheckConstraint instance
    """
    return CheckConstraint(
        f"length(regexp_replace({column}, '[^0-9]', '', 'g')) BETWEEN 10 AND 15",
        name=f"valid_{column}_format",
    )


def create_email_constraint(column: str) -> CheckConstraint:
    """Create a check constraint for email addresses.

    Args:
        column: Name of the email column

    Returns:
        SQLAlchemy CheckConstraint instance
    """
    return CheckConstraint(
        f"{column} ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{{2,}}$'",
        name=f"valid_{column}_format",
    )
