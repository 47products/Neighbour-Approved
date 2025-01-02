"""Association tables for model relationships."""

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.database import Base

# Contact and Category association
contact_categories = Table(
    "contact_categories",
    Base.metadata,
    Column(
        "contact_id",
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "category_id",
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)

# Contact and Service association
contact_services = Table(
    "contact_services",
    Base.metadata,
    Column(
        "contact_id",
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "service_id",
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)

# Community and Contact association
community_contacts = Table(
    "community_contacts",
    Base.metadata,
    Column(
        "community_id",
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "contact_id",
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)

# User and Role association
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "role_id",
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)

# User and Community association
user_communities = Table(
    "user_communities",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "community_id",
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)

# Community relationships (self-referential)
community_relationships = Table(
    "community_relationships",
    Base.metadata,
    Column(
        "community_a_id",
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "community_b_id",
        Integer,
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
