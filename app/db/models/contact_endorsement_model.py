"""Contact Endorsement model definition module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
    Index,
    Integer,
    String,
    ForeignKey,
    text,
)
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.database_engine import Base
from app.db.models.base_mixins import (
    TimestampMixin,
    VerificationMixin,
    VisibilityMixin,
)
from app.db.database_utils import (
    COMMENT_LENGTH,
    create_check_constraint,
    create_unique_constraint,
)

if TYPE_CHECKING:
    from app.db.models.user_model import User
    from app.db.models.community_model import Community
    from app.db.models.contact_model import Contact


@dataclass
class EndorsementCreate:
    """Data transfer object for creating a new ContactEndorsement."""

    contact_id: int
    user_id: int
    community_id: int
    endorsed: bool = True
    rating: Optional[int] = None
    comment: Optional[str] = None
    is_public: bool = True


class ContactEndorsement(
    TimestampMixin,
    VerificationMixin,
    VisibilityMixin,
    Base,
):
    """
    Model for contact endorsements within communities.

    Represents recommendations and ratings that users provide for contacts within
    specific communities. Includes verification status and visibility controls.

    Attributes:
        id (int): Unique identifier
        contact_id (int): ID of endorsed contact
        user_id (int): ID of endorsing user
        community_id (int): ID of community context
        endorsed (bool): Whether endorsement is positive
        rating (int, optional): Numerical rating (1-5)
        comment (str, optional): Detailed endorsement text
        is_verified (bool): Whether endorsement is verified
        verification_date (datetime): When endorsement was verified
        verification_notes (str, optional): Notes about verification
        is_public (bool): Whether endorsement is publicly visible

    Relationships:
        user: User who provided endorsement
        community: Community context
        contact: Contact being endorsed
    """

    __tablename__ = "contact_endorsements"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    community_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    endorsed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Indicates if this is a positive endorsement",
    )
    rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        doc="Optional rating from 1 to 5",
    )
    comment: Mapped[Optional[str]] = mapped_column(
        String(COMMENT_LENGTH),
        doc="Optional detailed endorsement comment",
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="contact_endorsements",
        lazy="joined",
    )
    community: Mapped[Community] = relationship(
        "Community",
        back_populates="contact_endorsements",
        lazy="joined",
    )
    contact: Mapped[Contact] = relationship(
        "Contact",
        back_populates="endorsements",
        lazy="joined",
    )

    __table_args__ = (
        create_unique_constraint(
            "user_id",
            "contact_id",
            "community_id",
            name="uq_user_contact_community_endorsement",
        ),
        create_check_constraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="valid_rating_range",
        ),
        # Optimize verified endorsement queries
        Index(
            "idx_contact_endorsements_verified",
            "contact_id",
            "is_verified",
            "rating",
            postgresql_where=text("is_verified = true"),
        ),
        # Optimize community-based endorsement queries with included columns
        # The INCLUDE clause adds columns to the index leaf nodes without making them part of the key
        Index(
            "idx_contact_endorsements_community",
            "community_id",
            "created_at",
            postgresql_include=["rating", "is_verified"],
        ),
    )

    @classmethod
    def create(cls, data: EndorsementCreate) -> ContactEndorsement:
        """Create a new ContactEndorsement from EndorsementCreate data."""
        return cls(**data.__dict__)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ContactEndorsement(id={self.id}, "
            f"contact_id={self.contact_id}, "
            f"user_id={self.user_id})"
        )

    def update_rating(
        self,
        new_rating: Optional[int],
        comment: Optional[str] = None,
    ) -> None:
        """
        Update rating and optionally comment.

        Args:
            new_rating: New rating value (1-5) or None
            comment: Optional new comment text

        Raises:
            ValueError: If rating is invalid
        """
        if new_rating is not None and not 1 <= new_rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        self.rating = new_rating
        if comment is not None:
            self.comment = comment

    @property
    def verification_status(self) -> str:
        """Get human-readable verification status."""
        if not self.is_verified:
            return "Unverified"
        if self.verification_notes:
            return f"Verified with notes: {self.verification_notes}"
        return "Verified"

    @property
    def formatted_rating(self) -> Optional[str]:
        """Get formatted display of rating."""
        if self.rating is None:
            return None
        return f"{self.rating}/5 stars"
