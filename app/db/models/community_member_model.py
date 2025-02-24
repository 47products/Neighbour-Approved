"""Community member association model definition module."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database_engine import Base
from app.db.database_types import TZDateTime
from app.db.models.base_mixins import TimestampMixin


class CommunityMember(TimestampMixin, Base):
    """
    Association model for community membership.

    This model represents the relationship between users and communities,
    tracking membership details including roles and assignment history.

    Attributes:
        community_id (int): ID of the community
        user_id (int): ID of the member user
        role (str): Member's role in the community
        joined_at (datetime): When the user joined
        role_assigned_at (datetime, optional): When current role was assigned
        role_assigned_by (int, optional): ID of user who assigned the role
        is_active (bool): Whether membership is active
    """

    __tablename__ = "community_members"

    community_id: Mapped[int] = mapped_column(
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="member",
    )
    joined_at: Mapped[datetime] = mapped_column(
        TZDateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    role_assigned_at: Mapped[Optional[datetime]] = mapped_column(
        TZDateTime(timezone=True),
    )
    role_assigned_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    def __init__(
        self,
        community_id: int,
        user_id: int,
        role: str = "member",
        is_active: bool = True,
        joined_at: Optional[datetime] = None,
        role_assigned_at: Optional[datetime] = None,
        role_assigned_by: Optional[int] = None,
    ):
        """Explicitly set default values when instantiated in Python."""
        self.community_id = community_id
        self.user_id = user_id
        self.role = role
        self.is_active = is_active
        self.joined_at = joined_at or datetime.now(timezone.utc)
        self.role_assigned_at = role_assigned_at
        self.role_assigned_by = role_assigned_by

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"CommunityMember(community_id={self.community_id}, "
            f"user_id={self.user_id}, role={self.role})"
        )
