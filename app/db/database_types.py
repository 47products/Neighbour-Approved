# pylint: disable=too-many-ancestors
"""Database type definitions for SQLAlchemy models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Union
from sqlalchemy import CheckConstraint, DateTime, TypeDecorator


class TZDateTime(TypeDecorator):
    """Custom SQLAlchemy type that enforces timezone-aware datetime fields."""

    impl = DateTime
    cache_ok = True

    def process_literal_param(self, value: Any, dialect: Any) -> Optional[str]:
        """Process literal parameters for the database."""
        if value is not None:
            return f"TIMESTAMP '{value}'"
        return None

    @property
    def python_type(self) -> type:
        """Return the Python type handled by this type decorator."""
        return datetime

    def process_bind_param(
        self, value: Optional[Union[datetime, Any]], dialect: Any
    ) -> Optional[datetime]:
        if value is not None:
            if not value.tzinfo:
                raise ValueError(
                    "Timezone aware datetime is required. Please provide a "
                    "datetime with tzinfo."
                )
            return value.astimezone(timezone.utc)
        return value

    def process_result_value(
        self, value: Optional[Union[datetime, Any]], dialect: Any
    ) -> Optional[datetime]:
        if value is not None:
            return value.replace(tzinfo=timezone.utc)
        return value


class PrivacyLevel(str, Enum):
    """Enumeration for community privacy levels."""

    PUBLIC = "public"
    PRIVATE = "private"
    INVITATION_ONLY = "invitation_only"

    @classmethod
    def values(cls):
        """Return all valid enum values."""
        return [e.value for e in cls]


def create_email_check_constraint(column_name: str) -> CheckConstraint:
    """Create a check constraint for email format validation."""
    return CheckConstraint(
        f"{column_name} IS NULL OR "
        f"{column_name} ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{{2,}}$'",
        name=f"valid_{column_name}_format",
    )
