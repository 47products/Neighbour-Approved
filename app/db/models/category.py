"""Category model definition module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.db.database import Base
from app.db.models.associations import contact_categories
from app.db.models.mixins import (
    TimestampMixin,
    ActiveMixin,
    NameMixin,
    SlugMixin,
    OrderMixin,
)
from app.db.utils import DEFAULT_STRING_LENGTH

if TYPE_CHECKING:
    from app.db.models.contact import Contact
    from app.db.models.service import Service


@dataclass
class CategoryCreate:
    """Data transfer object for creating a new Category."""

    name: str
    slug: str
    description: Optional[str] = None
    parent: Optional[Category] = None
    sort_order: int = 0


class Category(
    TimestampMixin,
    ActiveMixin,
    NameMixin,
    SlugMixin,
    OrderMixin,
    Base,
):
    """
    Category model for hierarchical classification.

    Categories form a hierarchical structure for organizing contacts and services.
    Each category can have multiple child categories and belongs to a single
    parent category, enabling detailed taxonomies for resource classification.

    Attributes:
        id (int): Unique identifier
        name (str): Category name (unique)
        description (str, optional): Detailed category description
        slug (str): URL-friendly version of the name
        parent_id (int, optional): ID of parent category
        is_active (bool): Whether category is active
        sort_order (int): Display order position
        depth (int): Level in hierarchy (0 for root)
        path (str): Full path from root to this category

    Relationships:
        parent: Parent category (if any)
        children: Child categories
        contacts: Assigned contacts
        services: Associated services
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
    )
    depth: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Level in hierarchy (0 for root)",
    )
    path: Mapped[str] = mapped_column(
        String(DEFAULT_STRING_LENGTH),
        nullable=False,
        doc="Full path from root to this category",
    )

    # Relationships
    parent: Mapped[Optional[Category]] = relationship(
        "Category",
        back_populates="children",
        remote_side=[id],
        lazy="joined",
    )
    children: Mapped[List[Category]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Category.sort_order",
    )
    contacts: Mapped[List[Contact]] = relationship(
        "Contact",
        secondary=contact_categories,
        back_populates="categories",
        lazy="selectin",
    )
    services: Mapped[List[Service]] = relationship(
        "Service",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Service.name",
    )

    @classmethod
    def create(cls, data: CategoryCreate) -> Category:
        """Create a new Category instance from CategoryCreate data."""
        instance = cls(**data.__dict__)
        instance.update_hierarchy_info()
        return instance

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Category(id={self.id}, name={self.name})"

    def update_hierarchy_info(self) -> None:
        """Update hierarchy information (depth and path)."""
        if self.parent:
            self.depth = self.parent.depth + 1
            self.path = f"{self.parent.path}/{self.slug}"
        else:
            self.depth = 0
            self.path = self.slug

    def get_ancestors(self) -> List[Category]:
        """Get all ancestor categories in order from root to parent."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self) -> List[Category]:
        """Get all descendant categories in depth-first order."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def is_ancestor_of(self, category: Category) -> bool:
        """Check if this category is an ancestor of another category."""
        return self.path in category.path.split("/")

    def is_descendant_of(self, category: Category) -> bool:
        """Check if this category is a descendant of another category."""
        return category.path in self.path.split("/")

    def move_to_parent(self, new_parent: Optional[Category]) -> None:
        """
        Move this category to a new parent.

        Args:
            new_parent: New parent category or None for root

        Raises:
            ValueError: If move would create circular reference
        """
        if new_parent and (self == new_parent or new_parent.is_descendant_of(self)):
            raise ValueError("Cannot move category to one of its descendants")

        self.parent = new_parent
        self.update_hierarchy_info()

        for descendant in self.get_descendants():
            descendant.update_hierarchy_info()
