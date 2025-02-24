"""Role model definition module."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.database_engine import Base
from app.db.models.base_mixins import (
    TimestampMixin,
    ActiveMixin,
    NameMixin,
)
from app.db.models.association_tables import user_roles
from app.db.database_utils import (
    SHORT_STRING_LENGTH,
    COMMENT_LENGTH,
    create_check_constraint,
)

if TYPE_CHECKING:
    from app.db.models.user_model import User


@dataclass
class RoleCreate:
    """Data transfer object for creating a new Role."""

    name: str
    description: Optional[str] = None
    permissions: Optional[str] = None
    is_system_role: bool = False


class Role(TimestampMixin, ActiveMixin, NameMixin, Base):
    """
    Role model for user permissions.

    Defines sets of permissions and access levels that can be assigned to users.
    Supports both system-defined and custom roles.

    Attributes:
        id (int): Unique identifier
        name (str): Role name (unique)
        description (str, optional): Role description
        permissions (str, optional): JSON string of permissions
        is_system_role (bool): Whether this is a system-managed role
        is_active (bool): Whether role is currently active

    Relationships:
        users: Users assigned this role
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(SHORT_STRING_LENGTH),
        unique=True,
        index=True,
        nullable=False,
    )
    permissions: Mapped[Optional[str]] = mapped_column(
        String(COMMENT_LENGTH),
        doc="JSON string containing role permissions",
    )
    is_system_role: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="Indicates if this is a system-managed role",
    )

    # Override from NameMixin for different length
    description: Mapped[Optional[str]] = mapped_column(
        String(COMMENT_LENGTH),
        doc="Detailed role description",
    )

    # Relationships
    users: Mapped[List[User]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        lazy="selectin",
        order_by="User.last_name",
    )

    __table_args__ = (
        create_check_constraint(
            "permissions IS NULL OR json_typeof(permissions::json) = 'array'",
            name="valid_permissions_json",
        ),
    )

    @classmethod
    def create(cls, data: RoleCreate) -> Role:
        """Create a new Role from RoleCreate data."""
        return cls(**data.__dict__)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Role(id={self.id}, name={self.name})"

    def has_permission(self, permission: str) -> bool:
        """
        Check if role has specific permission.

        Args:
            permission: Permission to check

        Returns:
            bool: Whether role has permission
        """
        if not self.permissions or not self.is_active:
            return False

        try:
            permissions = json.loads(self.permissions)
            return permission in permissions
        except (json.JSONDecodeError, TypeError):
            return False

    def grant_permission(self, permission: str) -> None:
        """
        Grant new permission to role.

        Args:
            permission: Permission to grant
        """
        try:
            permissions = json.loads(self.permissions) if self.permissions else []
        except (json.JSONDecodeError, TypeError):
            permissions = []

        if permission not in permissions:
            permissions.append(permission)
            self.permissions = json.dumps(permissions)

    def revoke_permission(self, permission: str) -> None:
        """
        Revoke permission from role.

        Args:
            permission: Permission to revoke
        """
        try:
            permissions = json.loads(self.permissions) if self.permissions else []
        except (json.JSONDecodeError, TypeError):
            return

        if permission in permissions:
            permissions.remove(permission)
            self.permissions = json.dumps(permissions)

    def list_permissions(self) -> List[str]:
        """
        Get list of all granted permissions.

        Returns:
            list: Current permissions
        """
        try:
            return json.loads(self.permissions) if self.permissions else []
        except (json.JSONDecodeError, TypeError):
            return []
