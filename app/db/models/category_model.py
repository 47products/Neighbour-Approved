"""Category model definition module.

This module implements the Category model, which provides a hierarchical classification
system for organizing services and contacts. It includes optimized database indices
for efficient tree traversal and hierarchical queries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Index, Integer, String, ForeignKey, text
from sqlalchemy.orm import Mapped, relationship, mapped_column, declared_attr

from app.db.database_configuration import Base
from app.db.models.association_tables import contact_categories
from app.db.models.base_mixins import (
    TimestampMixin,
    ActiveMixin,
    NameMixin,
    SlugMixin,
    OrderMixin,
)
from app.db.database_utils import DEFAULT_STRING_LENGTH

if TYPE_CHECKING:
    from app.db.models.contact_model import Contact
    from app.db.models.service_model import Service


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
    """

    __tablename__ = "categories"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign Keys and Regular Columns
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

    @declared_attr
    def __table_args__(cls) -> tuple:
        """Define table arguments including indices.

        Using declared_attr ensures proper column reference resolution
        and fixes linting issues.
        """
        return (
            # Optimize tree traversal queries
            Index(
                "uq_category_parent_slug",
                cls.parent_id,
                cls.slug,
                unique=True,
                postgresql_where=text("is_active = true"),
            ),
            # Improve hierarchical path lookups
            Index(
                "idx_categories_hierarchy",
                cls.path,
                cls.is_active,
                postgresql_using="btree",
            ),
            # Optimize level-based category queries
            Index(
                "idx_categories_depth",
                cls.depth,
                cls.is_active,
                postgresql_using="btree",
            ),
            # Improve sibling ordering queries
            Index(
                "idx_categories_ordering",
                cls.parent_id,
                cls.sort_order,
                cls.is_active,
                postgresql_using="btree",
            ),
            # Optimize path-based lookups
            Index(
                "idx_categories_path_search",
                cls.path,
                postgresql_using="btree",
                postgresql_where=text("is_active = true"),
            ),
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
        """Move this category to a new parent."""
        if new_parent and (self == new_parent or new_parent.is_descendant_of(self)):
            raise ValueError("Cannot move category to one of its descendants")

        self.parent = new_parent
        self.update_hierarchy_info()

        for descendant in self.get_descendants():
            descendant.update_hierarchy_info()

    def get_siblings(self) -> List[Category]:
        """Get all categories that share the same parent."""
        if self.parent:
            return [child for child in self.parent.children if child != self]
        return []

    def get_root(self) -> Category:
        """Get the root category for this branch of the hierarchy."""
        current = self
        while current.parent:
            current = current.parent
        return current

    def get_full_path_names(self) -> List[str]:
        """Get the full path of category names from root to this category."""
        path_names = []
        current = self
        while current:
            path_names.insert(0, current.name)
            current = current.parent
        return path_names

    def is_leaf(self) -> bool:
        """Check if this category is a leaf node (has no children)."""
        return len(self.children) == 0

    def is_empty(self) -> bool:
        """Check if this category has any associated contacts or services."""
        return len(self.contacts) == 0 and len(self.services) == 0

    def get_active_services_count(self) -> int:
        """Get count of active services in this category."""
        return sum(1 for service in self.services if service.is_active)

    def get_sorted_children(self, *, active_only: bool = False) -> List[Category]:
        """Get children categories in proper sort order."""
        children = self.children
        if active_only:
            children = [child for child in children if child.is_active]
        return sorted(children, key=lambda x: x.sort_order)

    def validate_hierarchy(self) -> bool:
        """Validate the correctness of the category hierarchy."""
        calculated_depth = self.get_hierarchy_level()
        if calculated_depth != self.depth:
            raise ValueError(
                f"Depth mismatch: stored={self.depth}, "
                f"calculated={calculated_depth}"
            )

        calculated_path = "/".join(
            ancestor.slug for ancestor in self.get_ancestors() + [self]
        )
        if calculated_path != self.path:
            raise ValueError(
                f"Path mismatch: stored={self.path}, " f"calculated={calculated_path}"
            )

        visited = set()
        current = self
        while current:
            if current.id in visited:
                raise ValueError("Circular reference detected in category hierarchy")
            visited.add(current.id)
            current = current.parent

        return True

    def get_hierarchy_level(self) -> int:
        """Get the absolute level in the full category hierarchy."""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level

    def reorder_children(self, new_order: List[int]) -> None:
        """Reorder child categories based on provided order."""
        if set(new_order) != set(child.id for child in self.children):
            raise ValueError("New order must contain exactly the current child IDs")

        order_map = {id_: i for i, id_ in enumerate(new_order)}

        for child in self.children:
            child.sort_order = order_map[child.id]
