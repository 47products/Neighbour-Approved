"""Service model definition module."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Index,
    Integer,
    String,
    ForeignKey,
    Numeric,
    text,
)
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.database import Base
from app.db.utils import (
    COMMENT_LENGTH,
    SHORT_STRING_LENGTH,
)
from app.db.models.mixins import (
    TimestampMixin,
    ActiveMixin,
    NameMixin,
)
from app.db.models.associations import contact_services

if TYPE_CHECKING:
    from app.db.models.category import Category
    from app.db.models.contact import Contact


@dataclass
class ServiceCreate:
    """Data transfer object for creating a new Service."""

    name: str
    category_id: int
    description: Optional[str] = None
    base_price: Optional[Decimal] = None
    price_unit: Optional[str] = None
    requires_consultation: bool = False
    is_remote_available: bool = False
    minimum_hours: Optional[int] = None
    maximum_hours: Optional[int] = None


# pylint: disable=too-many-instance-attributes
class Service(TimestampMixin, ActiveMixin, NameMixin, Base):
    """
    Service model for offerings that contacts can provide.

    Represents specific services that can be offered by contacts. Each service
    belongs to a category and includes detailed pricing and availability information.

    Attributes:
        id (int): Unique identifier
        name (str): Service name
        description (str, optional): Detailed description
        category_id (int): ID of category
        base_price (Decimal, optional): Base price
        price_unit (str, optional): Unit for price (e.g., 'hour', 'project')
        minimum_hours (int, optional): Minimum booking duration
        maximum_hours (int, optional): Maximum booking duration
        requires_consultation (bool): Whether consultation is required
        is_remote_available (bool): Whether service can be provided remotely
        is_active (bool): Whether service is currently available

    Relationships:
        category: Service category
        contacts: Providers offering this service
    """

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    base_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        comment="Base price for the service",
    )
    price_unit: Mapped[Optional[str]] = mapped_column(
        String(SHORT_STRING_LENGTH),
        comment="Unit of measurement for the price",
    )
    minimum_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Minimum duration in hours",
    )
    maximum_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Maximum duration in hours",
    )
    requires_consultation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_remote_available: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Override from NameMixin to specify different length
    description: Mapped[Optional[str]] = mapped_column(
        String(COMMENT_LENGTH),
        doc="Detailed service description",
    )

    # Relationships
    category: Mapped[Category] = relationship(
        "Category",
        back_populates="services",
        lazy="joined",
    )
    contacts: Mapped[List[Contact]] = relationship(
        "Contact",
        secondary=contact_services,
        back_populates="services",
        lazy="selectin",
        order_by="Contact.contact_name",
    )

    __table_args__ = (
        # Existing constraints remain...
        # Optimize price-based service searches
        # This partial index only includes active services
        Index(
            "idx_services_price",
            "category_id",
            "base_price",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
        # Optimize availability-based queries
        Index(
            "idx_services_availability",
            "is_remote_available",
            "requires_consultation",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    @classmethod
    def create(cls, data: ServiceCreate) -> Service:
        """Create a new Service from ServiceCreate data."""
        return cls(**data.__dict__)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Service(id={self.id}, name={self.name})"

    def get_formatted_price(self) -> Optional[str]:
        """Get formatted price string."""
        if self.base_price is None or self.price_unit is None:
            return None
        return f"${self.base_price:.2f} per {self.price_unit}"

    def calculate_price(self, hours: Optional[int] = None) -> Optional[Decimal]:
        """
        Calculate total price for duration.

        Args:
            hours: Number of hours requested

        Returns:
            Calculated price or None if pricing unavailable

        Raises:
            ValueError: If hours outside allowed range
        """
        if self.base_price is None:
            return None

        if self.price_unit != "hour" or hours is None:
            return self.base_price

        if self.minimum_hours and hours < self.minimum_hours:
            raise ValueError(f"Minimum booking duration is {self.minimum_hours} hours")

        if self.maximum_hours and hours > self.maximum_hours:
            raise ValueError(f"Maximum booking duration is {self.maximum_hours} hours")

        return self.base_price * Decimal(str(hours))

    def is_available_for_duration(self, hours: int) -> bool:
        """Check if service can be booked for duration."""
        if not self.is_active:
            return False

        if self.minimum_hours and hours < self.minimum_hours:
            return False

        if self.maximum_hours and hours > self.maximum_hours:
            return False

        return True

    @property
    def duration_constraints(self) -> Optional[str]:
        """Get human-readable duration constraints."""
        if not (self.minimum_hours or self.maximum_hours):
            return None

        if self.minimum_hours and self.maximum_hours:
            return f"Duration: {self.minimum_hours}-{self.maximum_hours} hours"

        if self.minimum_hours:
            return f"Minimum duration: {self.minimum_hours} hours"

        return f"Maximum duration: {self.maximum_hours} hours"
