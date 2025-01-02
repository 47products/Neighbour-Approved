"""Base mixins for SQLAlchemy models."""

from datetime import datetime
from typing import Optional, TypeVar
from sqlalchemy import Boolean, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.types import TZDateTime

T = TypeVar("T")


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""

    created_at: Mapped[datetime] = mapped_column(
        TZDateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of creation",
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TZDateTime(timezone=True),
        onupdate=func.now(),
        doc="Timestamp of last update",
    )


class ActiveMixin:
    """Mixin for adding active status to models."""

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the entity is currently active",
    )


class NameMixin:
    """Mixin for adding standardized name fields to models."""

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Name of the entity",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        doc="Description of the entity",
    )


class SlugMixin:
    """Mixin for adding slug field to models."""

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        doc="URL-friendly version of the name",
    )


class OrderMixin:
    """Mixin for adding sort order to models."""

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Position in display order",
    )


class VerificationMixin:
    """Mixin for adding verification status to models."""

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the entity is verified",
    )
    verification_date: Mapped[Optional[datetime]] = mapped_column(
        TZDateTime(timezone=True),
        doc="When verification occurred",
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(
        String(200),
        doc="Notes about verification",
    )


class VisibilityMixin:
    """Mixin for adding public/private visibility to models."""

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the entity is publicly visible",
    )


class CounterMixin:
    """Mixin for adding common counter fields to models."""

    total_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total count of related items",
    )
    active_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Count of active related items",
    )
