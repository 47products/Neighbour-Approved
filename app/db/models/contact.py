"""
This module contains the Contact model.

The Contact model represents a contact in the Neighbour Approved application.

Attributes:
    id (int): Primary key.
    contact_name (str): Name of the contact.
    email (str): Email address of the contact.
    contact_number (str): Contact number of the contact.
    primary_contact_first_name (str): First name of the primary contact person.
    primary_contact_last_name (str): Last name of the primary contact person.
    primary_contact_contact_number (str): Contact number of the primary contact person.
    categories (str): Categories associated with the contact.
    services (str): Services offered
    endorsements (int): Number of endorsements for the contact.
    user_id (int): Foreign key linking to the User model.
    user (User): The user associated with the contact.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class Contact(Base):
    """
    Contact Model.

    Represents a contact in the Neighbour Approved application.

    Attributes:
        id (int): Primary key.
        name (str): Name of the contact.
        service (str): Type of service provided by the contact.
        rating (float): Average rating of the contact.
        user_id (int): Foreign key linking to the User model.
        user (User): The user associated with the contact.
    """

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    contact_name = Column(String(100), index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    contact_number = Column(String(20))
    primary_contact_first_name = Column(String(50), nullable=False)
    primary_contact_last_name = Column(String(50), nullable=False)
    primary_contact_contact_number = Column(String(20))
    categories = Column(String, index=True, nullable=False)
    services = Column(String, index=True, nullable=False)
    endorsements = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Establishes a many-to-one relationship with the User model
    user = relationship("User", back_populates="contacts")
