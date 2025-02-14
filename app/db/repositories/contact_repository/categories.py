"""
Contact Categories Module.

This module provides the `ContactCategoriesMixin` class which encapsulates methods
to manage the association between contacts and categories. It includes functionality
to add or remove a category from a contact.

Usage Example:
    from app.db.repositories.contact_repository.categories import ContactCategoriesMixin

    class MyRepository(ContactCategoriesMixin, BaseRepository):
        pass

Dependencies:
    - SQLAlchemy (for transaction management)
    - app.db.models.category_model.Category (Category model)
    - app.db.errors.IntegrityError (Custom error for integrity issues)
"""

from sqlalchemy.exc import SQLAlchemyError

from app.db.models.category_model import Category
from app.db.errors import IntegrityError


class ContactCategoriesMixin:
    """
    Mixin class for managing contact-category relationships.

    Provides methods to add and remove categories from a contact.
    """

    async def add_category(self, contact_id: int, category_id: int) -> bool:
        """
        Add a category to a contact.

        Args:
            contact_id (int): The unique identifier of the contact.
            category_id (int): The unique identifier of the category to add.

        Returns:
            bool: True if the category was successfully added, False otherwise.

        Raises:
            IntegrityError: If the operation fails due to a database error.
        """
        try:
            contact = await self.get(contact_id)
            category = await self.db.get(Category, category_id)

            if not contact or not category:
                return False

            if category not in contact.categories:
                contact.categories.append(category)
                await self.db.commit()
                return True

            return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "add_category_failed",
                contact_id=contact_id,
                category_id=category_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to add category to contact",
                details={
                    "contact_id": contact_id,
                    "category_id": category_id,
                    "error": str(e),
                },
            ) from e

    async def remove_category(self, contact_id: int, category_id: int) -> bool:
        """
        Remove a category from a contact.

        Args:
            contact_id (int): The unique identifier of the contact.
            category_id (int): The unique identifier of the category to remove.

        Returns:
            bool: True if the category was successfully removed, False otherwise.

        Raises:
            IntegrityError: If the operation fails due to a database error.
        """
        try:
            contact = await self.get(contact_id)
            category = await self.db.get(Category, category_id)

            if not contact or not category:
                return False

            if category in contact.categories:
                contact.categories.remove(category)
                await self.db.commit()
                return True

            return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "remove_category_failed",
                contact_id=contact_id,
                category_id=category_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to remove category from contact",
                details={
                    "contact_id": contact_id,
                    "category_id": category_id,
                    "error": str(e),
                },
            ) from e
