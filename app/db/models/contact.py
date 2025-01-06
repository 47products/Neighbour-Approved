"""Contact model definition module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Index, Integer, String, ForeignKey, text
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.database import Base
from app.db.types import create_email_check_constraint
from app.db.utils import (
    EMAIL_LENGTH,
    NAME_LENGTH,
    PHONE_LENGTH,
    SHORT_STRING_LENGTH,
    create_phone_constraint,
)
from app.db.models.mixins import TimestampMixin, ActiveMixin
from app.db.models.associations import (
    contact_categories,
    contact_services,
    community_contacts,
)

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.community import Community
    from app.db.models.category import Category
    from app.db.models.service import Service
    from app.db.models.contact_endorsement import ContactEndorsement


@dataclass
class ContactCreate:
    """Data transfer object for creating a new Contact."""

    user_id: int
    contact_name: str
    primary_contact_first_name: str
    primary_contact_last_name: str
    email: Optional[str] = None
    contact_number: Optional[str] = None
    primary_contact_contact_number: Optional[str] = None


class Contact(TimestampMixin, ActiveMixin, Base):
    """
    Contact model for service providers.

    Represents service providers in the system, maintaining their professional details,
    service offerings, and community relationships.

    Attributes:
        id (int): Unique identifier
        user_id (int): ID of creating user
        contact_name (str): Business/organization name
        email (str, optional): Primary email address
        contact_number (str, optional): Primary phone number
        primary_contact_first_name (str): First name of main contact
        primary_contact_last_name (str): Last name of main contact
        primary_contact_contact_number (str, optional): Direct number for main contact
        endorsements_count (int): Total endorsements received
        average_rating (float, optional): Average rating from endorsements
        verified_endorsements_count (int): Number of verified endorsements

    Relationships:
        user: Creating user
        communities: Associated communities
        categories: Service categories
        services: Offered services
        endorsements: Received endorsements
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_name: Mapped[str] = mapped_column(
        String(NAME_LENGTH),
        nullable=False,
        index=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(EMAIL_LENGTH),
        unique=True,
        index=True,
    )
    contact_number: Mapped[Optional[str]] = mapped_column(String(PHONE_LENGTH))
    primary_contact_first_name: Mapped[str] = mapped_column(
        String(SHORT_STRING_LENGTH),
        nullable=False,
    )
    primary_contact_last_name: Mapped[str] = mapped_column(
        String(SHORT_STRING_LENGTH),
        nullable=False,
    )
    primary_contact_contact_number: Mapped[Optional[str]] = mapped_column(
        String(PHONE_LENGTH),
    )
    endorsements_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    average_rating: Mapped[Optional[float]] = mapped_column(
        Integer,
        comment="Average rating out of 5",
    )
    verified_endorsements_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="contacts",
        lazy="joined",
    )
    communities: Mapped[List[Community]] = relationship(
        "Community",
        secondary=community_contacts,
        back_populates="contacts",
        lazy="selectin",
        order_by="Community.name",
    )
    categories: Mapped[List[Category]] = relationship(
        "Category",
        secondary=contact_categories,
        back_populates="contacts",
        lazy="selectin",
        order_by="Category.name",
    )
    services: Mapped[List[Service]] = relationship(
        "Service",
        secondary=contact_services,
        back_populates="contacts",
        lazy="selectin",
        order_by="Service.name",
    )
    endorsements: Mapped[List[ContactEndorsement]] = relationship(
        "ContactEndorsement",
        back_populates="contact",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        create_email_check_constraint("email"),
        create_phone_constraint("contact_number"),
        create_phone_constraint("primary_contact_contact_number"),
        # Combined index for name-based searches
        # This improves performance when searching by full name or sorting by name
        Index(
            "idx_contacts_primary_contact_name",
            "primary_contact_last_name",
            "primary_contact_first_name",
        ),
        # Trigram index for fuzzy contact name searches
        # Note: This requires the pg_trgm extension to be installed
        Index(
            "idx_contacts_contact_name_trgm",
            text("contact_name gin_trgm_ops"),
            postgresql_using="gin",
        ),
        # Composite index for endorsement-related queries
        # This speeds up queries that filter by endorsement counts and ratings
        Index(
            "idx_contacts_endorsement_metrics",
            "endorsements_count",
            "average_rating",
            "verified_endorsements_count",
            "is_active",
        ),
    )

    @classmethod
    def create(cls, data: ContactCreate) -> Contact:
        """Create a new Contact from ContactCreate data."""
        return cls(**data.__dict__)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Contact(id={self.id}, name={self.contact_name})"

    @hybrid_property
    def primary_contact_full_name(self) -> str:
        """Get full name of primary contact person."""
        return f"{self.primary_contact_first_name} {self.primary_contact_last_name}"

    def add_endorsement(self, endorsement: ContactEndorsement) -> None:
        """
        Add endorsement and update metrics.

        Args:
            endorsement: New endorsement to add
        """
        self.endorsements.append(endorsement)
        self.endorsements_count += 1

        if endorsement.is_verified:
            self.verified_endorsements_count += 1

        if endorsement.rating:
            self._update_average_rating()

    def remove_endorsement(self, endorsement: ContactEndorsement) -> None:
        """
        Remove endorsement and update metrics.

        Args:
            endorsement: Endorsement to remove
        """
        if endorsement in self.endorsements:
            self.endorsements.remove(endorsement)
            self.endorsements_count -= 1

            if endorsement.is_verified:
                self.verified_endorsements_count -= 1

            if endorsement.rating:
                self._update_average_rating()

    def _update_average_rating(self) -> None:
        """Update average rating based on current endorsements."""
        rated_endorsements = [e for e in self.endorsements if e.rating is not None]
        if rated_endorsements:
            total_rating = sum(e.rating for e in rated_endorsements)
            self.average_rating = round(total_rating / len(rated_endorsements), 1)
        else:
            self.average_rating = None

    def verify_endorsement(self, endorsement: ContactEndorsement) -> None:
        """
        Mark endorsement as verified.

        Args:
            endorsement: Endorsement to verify

        Raises:
            ValueError: If endorsement doesn't belong to this contact
        """
        if endorsement not in self.endorsements:
            raise ValueError("Endorsement does not belong to this contact")

        if not endorsement.is_verified:
            endorsement.is_verified = True
            self.verified_endorsements_count += 1

    def get_services_by_category(self, category_id: int) -> List[Service]:
        """Get all services in specified category."""
        return [s for s in self.services if s.category_id == category_id]

    def is_endorsed_in_community(self, community_id: int) -> bool:
        """Check if contact has endorsements in specified community."""
        return any(e.community_id == community_id for e in self.endorsements)
