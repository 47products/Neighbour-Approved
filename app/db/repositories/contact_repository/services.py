"""
Contact Services Module.

This module provides the `ContactServicesMixin` class which encapsulates methods
to manage the association between contacts and services. It includes functionality
to add or remove a service from a contact's offerings.

Usage Example:
    from app.db.repositories.contact_repository.services import ContactServicesMixin

    class MyRepository(ContactServicesMixin, BaseRepository):
        pass

Dependencies:
    - SQLAlchemy (for transaction management)
    - app.db.models.service_model.Service (Service model)
    - app.db.errors.IntegrityError (Custom error for integrity issues)
"""

from sqlalchemy.exc import SQLAlchemyError

from app.db.models.service_model import Service
from app.db.errors import IntegrityError


class ContactServicesMixin:
    """
    Mixin class for managing contact-service relationships.

    Provides methods to add and remove services from a contact.
    """

    async def add_service(self, contact_id: int, service_id: int) -> bool:
        """
        Add a service to a contact's offerings.

        Args:
            contact_id (int): The unique identifier of the contact.
            service_id (int): The unique identifier of the service to add.

        Returns:
            bool: True if the service was successfully added, False otherwise.

        Raises:
            IntegrityError: If the operation fails due to a database error.
        """
        try:
            contact = await self.get(contact_id)
            service = await self.db.get(Service, service_id)

            if not contact or not service:
                return False

            if service not in contact.services:
                contact.services.append(service)
                await self.db.commit()
                return True

            return False
        except SQLAlchemyError as e:
            # Roll back any pending transaction before raising an error.
            await self.db.rollback()
            self._logger.error(
                "add_service_failed",
                contact_id=contact_id,
                service_id=service_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to add service to contact",
                details={
                    "contact_id": contact_id,
                    "service_id": service_id,
                    "error": str(e),
                },
            ) from e

    async def remove_service(self, contact_id: int, service_id: int) -> bool:
        """
        Remove a service from a contact's offerings.

        Args:
            contact_id (int): The unique identifier of the contact.
            service_id (int): The unique identifier of the service to remove.

        Returns:
            bool: True if the service was successfully removed, False otherwise.

        Raises:
            IntegrityError: If the operation fails due to a database error.
        """
        try:
            contact = await self.get(contact_id)
            service = await self.db.get(Service, service_id)

            if not contact or not service:
                return False

            if service in contact.services:
                contact.services.remove(service)
                await self.db.commit()
                return True

            return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            self._logger.error(
                "remove_service_failed",
                contact_id=contact_id,
                service_id=service_id,
                error=str(e),
            )
            raise IntegrityError(
                message="Failed to remove service from contact",
                details={
                    "contact_id": contact_id,
                    "service_id": service_id,
                    "error": str(e),
                },
            ) from e
