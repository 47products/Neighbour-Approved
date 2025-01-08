"""User model definition module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.database_configuration import Base
from app.db.models.base_mixins import TimestampMixin, ActiveMixin
from app.db.models.association_tables import (
    user_roles,
    user_communities,
)
from app.db.database_utils import (
    EMAIL_LENGTH,
    SHORT_STRING_LENGTH,
    POSTAL_LENGTH,
    PHONE_LENGTH,
    create_email_constraint,
    create_phone_constraint,
)

if TYPE_CHECKING:
    from app.db.models.contact_model import Contact
    from app.db.models.role_model import Role
    from app.db.models.community_model import Community
    from app.db.models.contact_endorsement_model import ContactEndorsement


@dataclass
class UserCreate:
    """Data transfer object for creating a new User."""

    email: str
    password: str
    first_name: str
    last_name: str
    mobile_number: Optional[str] = None
    postal_address: Optional[str] = None
    physical_address: Optional[str] = None
    country: Optional[str] = None


class User(TimestampMixin, ActiveMixin, Base):
    """
    User model for system authentication and authorization.

    Central entity for user management, containing personal information,
    authentication details, and relationships with other entities.

    Attributes:
        id (int): Unique identifier
        email (str): Email address (unique)
        password (str): Hashed password
        first_name (str): First name
        last_name (str): Last name
        mobile_number (str, optional): Mobile phone
        postal_address (str, optional): Mailing address
        physical_address (str, optional): Physical location
        country (str, optional): Country of residence
        email_verified (bool): Whether email is verified
        last_login (datetime, optional): Last login timestamp

    Relationships:
        contacts: User's contacts
        roles: Assigned roles
        communities: Member communities
        contact_endorsements: Given endorsements
        owned_communities: Owned communities
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(EMAIL_LENGTH),
        unique=True,
        index=True,
        nullable=False,
    )
    password: Mapped[str] = mapped_column(
        String(EMAIL_LENGTH),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(SHORT_STRING_LENGTH),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(SHORT_STRING_LENGTH),
        nullable=False,
    )
    mobile_number: Mapped[Optional[str]] = mapped_column(
        String(PHONE_LENGTH),
    )
    postal_address: Mapped[Optional[str]] = mapped_column(
        String(POSTAL_LENGTH),
    )
    physical_address: Mapped[Optional[str]] = mapped_column(
        String(POSTAL_LENGTH),
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(SHORT_STRING_LENGTH),
    )
    email_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    # Relationships
    contacts: Mapped[List[Contact]] = relationship(
        "Contact",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Contact.contact_name",
    )
    roles: Mapped[List[Role]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
        order_by="Role.name",
    )
    communities: Mapped[List[Community]] = relationship(
        "Community",
        secondary=user_communities,
        back_populates="members",
        lazy="selectin",
        order_by="Community.name",
    )
    contact_endorsements: Mapped[List[ContactEndorsement]] = relationship(
        "ContactEndorsement",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ContactEndorsement.created_at.desc()",
    )
    owned_communities: Mapped[List[Community]] = relationship(
        "Community",
        primaryjoin="User.id == Community.owner_id",
        back_populates="owner",
        lazy="select",
        order_by="Community.name",
    )

    __table_args__ = (
        create_email_constraint("email"),
        create_phone_constraint("mobile_number"),
    )

    @classmethod
    def create(cls, data: UserCreate) -> User:
        """Create a new User from UserCreate data."""
        return cls(**data.__dict__)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"User(id={self.id}, email={self.email})"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def record_login(self) -> None:
        """Record current timestamp as last login."""
        self.last_login = datetime.now()

    def verify_email(self) -> None:
        """Mark email as verified."""
        self.email_verified = True

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has specific permission through any role.

        Args:
            permission: Permission to check

        Returns:
            bool: Whether user has permission
        """
        return any(
            role.has_permission(permission) for role in self.roles if role.is_active
        )

    def is_member_of(self, community_id: int) -> bool:
        """
        Check if user is member of community.

        Args:
            community_id: ID of community

        Returns:
            bool: Whether user is member
        """
        return any(c.id == community_id for c in self.communities)

    def owns_community(self, community_id: int) -> bool:
        """
        Check if user owns community.

        Args:
            community_id: ID of community

        Returns:
            bool: Whether user is owner
        """
        return any(c.id == community_id for c in self.owned_communities)

    def has_role(self, role_name: str) -> bool:
        """
        Check if user has specific role.

        Args:
            role_name: Name of role

        Returns:
            bool: Whether user has role
        """
        return any(r.name == role_name for r in self.roles if r.is_active)
