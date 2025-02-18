"""
Contact Service Category Module.

This module handles category-related operations for contacts, including adding
and removing categories associated with a contact.

Key Components:
- ContactServiceCategory: Manages contact-to-category associations.

Typical usage example:
    category_manager = ContactServiceCategory(db_session)
    await category_manager.add_category(contact_id=1, category_id=5)
"""

from sqlalchemy.orm import Session
from app.db.models.contact_model import Contact
from app.db.models.category_model import Category
from app.services.service_exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


class ContactServiceCategory:
    """
    Manages category assignments for contacts.

    This service allows adding and removing categories associated with a contact.

    Attributes:
        db (Session): Database session for category-related queries.
        MAX_CATEGORIES (int): Maximum allowed categories per contact.
    """

    MAX_CATEGORIES = 5

    def __init__(self, db: Session):
        """Initialize the category management module.

        Args:
            db (Session): Database session for category-related queries.
        """
        self.db = db

    async def add_category(self, contact_id: int, category_id: int) -> bool:
        """Add a category to a contact.

        Args:
            contact_id (int): The unique identifier of the contact.
            category_id (int): The unique identifier of the category.

        Returns:
            bool: True if the category was added, False if it was already present.

        Raises:
            ResourceNotFoundError: If the contact or category is not found.
            BusinessRuleViolationError: If the contact has reached the maximum category limit.
        """
        contact = await self.repository.get(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        category = await self.db.get(Category, category_id)
        if not category:
            raise ResourceNotFoundError(f"Category {category_id} not found")

        if category in contact.categories:
            return False  # Already added

        contact.categories.append(category)
        await self.db.commit()  # Ensure commit is awaited
        return True

    async def remove_category(self, contact_id: int, category_id: int) -> bool:
        """Remove a category from a contact.

        Args:
            contact_id (int): The unique identifier of the contact.
            category_id (int): The unique identifier of the category.

        Returns:
            bool: True if the category was removed, False if it was not found.

        Raises:
            ResourceNotFoundError: If the contact or category is not found.
        """
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        category = await self.db.get(Category, category_id)
        if not category:
            raise ResourceNotFoundError(f"Category {category_id} not found")

        if category not in contact.categories:
            return False

        contact.categories.remove(category)
        await self.db.commit()
        return True
