"""
Base Contact Service Module.

This module provides the foundational contact service class, handling basic 
contact-related operations such as creation, retrieval, updates, and deletions. 

Specialized operations (validation, endorsements, service assignments, etc.)
are delegated to separate modules.

Key Components:
- ContactService: Provides core CRUD operations for contacts.

Typical usage example:
    service = ContactService(db_session)
    contact = await service.get_contact(contact_id=1)
    await service.delete_contact(contact_id=1)
"""

from typing import Any
from sqlalchemy.orm import Session
from app.services.base import BaseService
from app.db.models.contact_model import Contact
from app.db.repositories.contact_repository import ContactRepository
from app.api.v1.schemas.contact_schema import ContactCreate, ContactUpdate
from app.services.service_exceptions import ResourceNotFoundError


class ContactService(BaseService[Contact, ContactCreate, ContactUpdate, Any]):
    """
    Base service for managing contact-related operations.

    This service provides CRUD operations for contacts but delegates complex business
    logic (endorsements, validation, service and category assignments) to specialized
    modules.

    Attributes:
        logger_name (str): Logger identifier for contact service operations.
    """

    def __init__(self, db: Session):
        """Initialize the contact service.

        Args:
            db (Session): Database session for repository operations.
        """
        super().__init__(
            model=Contact,
            repository=ContactRepository(db),
            logger_name="ContactService",
        )

    async def get_contact(self, contact_id: int) -> Contact:
        """Retrieve a contact by its ID.

        Args:
            contact_id (int): The unique identifier of the contact.

        Returns:
            Contact: The retrieved contact instance.

        Raises:
            ResourceNotFoundError: If the contact is not found.
        """
        contact = await self.get(contact_id)
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")
        return contact

    async def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact by its ID.

        Args:
            contact_id (int): The unique identifier of the contact.

        Returns:
            bool: True if the contact was deleted, False otherwise.

        Raises:
            ResourceNotFoundError: If the contact is not found.
        """
        contact = await self.get_contact(contact_id)
        return await self.delete(contact.id)
