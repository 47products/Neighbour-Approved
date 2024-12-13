"""
This module contains the User model.

The User model represents a user in the Neighbour Approved application.

Attributes:
    id (int): Primary key.
    email (str): Unique email address of the user.
    password (str): Hashed password of the user.
    first_name (str): First name of the user.
    last_name (str): Last name of the user.
    mobile_number (str): Mobile number of the user.
    postal_address (str): Postal address of the user.
    physical_address (str): Physical address of the user.
    country (str): Country of the user.
    created_at (datetime): Timestamp when the user was created.
    updated_at (datetime): Timestamp when the user was last updated.
    is_active (bool): Indicates whether the user account is active.
    contacts (List[Contact]): List of contacts associated with the user.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    """
    User Model.

    Represents a user in the Neighbour Approved application.

    Attributes:
        id (int): Primary key.
        email (str): Unique email address of the user.
        password (str): Hashed password of the user.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        mobile_number (str): Mobile number of the user.
        postal_address (str): Postal address of the user.
        physical_address (str): Physical address of the user.
        country (str): Country of the user.
        created_at (datetime): Timestamp when the user was created.
        updated_at (datetime): Timestamp when the user was last updated.
        is_active (bool): Indicates whether the user account is active.
        contacts (List[Contact]): List of contacts associated with the user.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    mobile_number = Column(String(20))
    postal_address = Column(String(200))
    physical_address = Column(String(200))
    country = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Establishes a one-to-many relationship with the Contact model
    contacts = relationship(
        "Contact", back_populates="user", cascade="all, delete-orphan"
    )
