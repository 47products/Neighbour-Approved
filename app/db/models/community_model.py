"""Community model definition module."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional
from dataclasses import dataclass

from sqlalchemy import ForeignKey, Integer, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.database_engine import Base
from app.db.models.base_mixins import (
    TimestampMixin,
    ActiveMixin,
    NameMixin,
    CounterMixin,
)
from app.db.models.association_tables import (
    community_contacts,
    community_relationships,
    user_communities,
)

if TYPE_CHECKING:
    from app.db.models.user_model import User
    from app.db.models.contact_model import Contact
    from app.db.models.contact_endorsement_model import ContactEndorsement


class PrivacyLevel(str, enum.Enum):
    """Enumeration for community privacy levels."""

    PUBLIC = "public"
    PRIVATE = "private"
    INVITATION_ONLY = "invitation_only"


@dataclass
class CommunityCreate:
    """Data transfer object for creating a new Community."""

    name: str
    owner_id: int
    description: Optional[str] = None
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC


class Community(
    TimestampMixin,
    ActiveMixin,
    NameMixin,
    CounterMixin,
    Base,
):
    """
    Community model for organizing users and contacts.

    Communities serve as organizational units that connect users and their contacts,
    enabling shared resources and collaborative endorsements.

    Attributes:
        id (int): Unique identifier
        name (str): Community name
        description (str, optional): Community description
        owner_id (int): ID of community owner
        privacy_level (PrivacyLevel): Access control level
        total_count (int): Total member count
        active_count (int): Active member count
        is_active (bool): Whether community is active

    Relationships:
        owner: User who owns the community
        members: Users who belong to community
        contacts: Contacts in the community
        related_communities: Connected communities
        contact_endorsements: Endorsements within community
    """

    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of community owner",
    )
    privacy_level: Mapped[PrivacyLevel] = mapped_column(
        SQLAlchemyEnum(PrivacyLevel, name="privacy_level_enum"),
        default=PrivacyLevel.PUBLIC,
        nullable=False,
        doc="Access control level",
    )

    # Relationships
    owner: Mapped[User] = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_communities",
        lazy="joined",
    )
    members: Mapped[List[User]] = relationship(
        "User",
        secondary=user_communities,
        back_populates="communities",
        lazy="selectin",
        order_by="User.last_name",
    )
    contacts: Mapped[List[Contact]] = relationship(
        "Contact",
        secondary=community_contacts,
        back_populates="communities",
        lazy="selectin",
        order_by="Contact.contact_name",
    )
    related_communities: Mapped[List[Community]] = relationship(
        "Community",
        secondary=community_relationships,
        primaryjoin=id == community_relationships.c.community_a_id,
        secondaryjoin=id == community_relationships.c.community_b_id,
        back_populates="related_to_communities",
        lazy="selectin",
        order_by="Community.name",
    )
    related_to_communities: Mapped[List[Community]] = relationship(
        "Community",
        secondary=community_relationships,
        primaryjoin=id == community_relationships.c.community_b_id,
        secondaryjoin=id == community_relationships.c.community_a_id,
        back_populates="related_communities",
        lazy="selectin",
        order_by="Community.name",
    )
    contact_endorsements: Mapped[List[ContactEndorsement]] = relationship(
        "ContactEndorsement",
        back_populates="community",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @classmethod
    def create(cls, data: CommunityCreate) -> Community:
        """Create a new Community instance from CommunityCreate data."""
        return cls(**data.__dict__)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Community(id={self.id}, name={self.name})"

    def add_member(self, user: User) -> None:
        """
        Add a user as a member.

        Args:
            user: User to add

        Raises:
            ValueError: If user is already a member
        """
        if user in self.members:
            raise ValueError(f"User {user.id} is already a member")
        self.members.append(user)
        self.total_count += 1
        if user.is_active:
            self.active_count += 1

    def remove_member(self, user: User) -> None:
        """
        Remove a user from membership.

        Args:
            user: User to remove

        Raises:
            ValueError: If user is not a member
        """
        if user not in self.members:
            raise ValueError(f"User {user.id} is not a member")
        self.members.remove(user)
        self.total_count -= 1
        if user.is_active:
            self.active_count -= 1

    def add_related_community(self, community: Community) -> None:
        """
        Establish relationship with another community.

        Args:
            community: Community to relate to

        Raises:
            ValueError: If already related
        """
        if community in self.related_communities:
            raise ValueError(f"Already related to community {community.id}")
        self.related_communities.append(community)

    def can_user_access(self, user: Optional[User]) -> bool:
        """
        Check if a user can access this community.

        Args:
            user: User to check access for

        Returns:
            bool: Whether user has access
        """
        if self.privacy_level == PrivacyLevel.PUBLIC:
            return True
        if not user:
            return False
        if user.id == self.owner_id:
            return True
        return user in self.members
