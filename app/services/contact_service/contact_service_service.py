"""
Contact Service Management Module.

This module handles service-related operations for contacts, including adding
and removing services associated with a contact.

Key Components:
- ContactServiceService: Manages contact-to-service associations.

Typical usage example:
    service_manager = ContactServiceService(db_session)
    await service_manager.add_service(contact_id=1, service_id=10)
"""

from sqlalchemy.orm import Session
from app.db.models.contact_model import Contact
from app.db.models.service_model import Service
from app.services.service_exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


class ContactServiceService:
    """
    Manages service assignments for contacts.

    This service allows adding and removing services associated with a contact.

    Attributes:
        db (Session): Database session for service-related queries.
        MAX_SERVICES (int): Maximum allowed services per contact.
    """

    MAX_SERVICES = 20

    def __init__(self, db: Session):
        """Initialize the service management module.

        Args:
            db (Session): Database session for service-related queries.
        """
        self.db = db

    async def add_service(self, contact_id: int, service_id: int) -> bool:
        """Add a service to a contact.

        Args:
            contact_id (int): The unique identifier of the contact.
            service_id (int): The unique identifier of the service.

        Returns:
            bool: True if the service was added, False if it was already present.

        Raises:
            ResourceNotFoundError: If the contact or service is not found.
            BusinessRuleViolationError: If the contact has reached the maximum service limit.
        """
        contact = self.db.query(Contact).filter_by(id=contact_id).first()
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        service = self.db.query(Service).filter_by(id=service_id).first()
        if not service:
            raise ResourceNotFoundError(f"Service {service_id} not found")

        if len(contact.services) >= self.MAX_SERVICES:
            raise BusinessRuleViolationError(
                f"Contact has reached the maximum service limit ({self.MAX_SERVICES})"
            )

        if service in contact.services:
            return False

        contact.services.append(service)
        self.db.commit()
        return True

    async def remove_service(self, contact_id: int, service_id: int) -> bool:
        """Remove a service from a contact.

        Args:
            contact_id (int): The unique identifier of the contact.
            service_id (int): The unique identifier of the service.

        Returns:
            bool: True if the service was removed, False if it was not found.

        Raises:
            ResourceNotFoundError: If the contact or service is not found.
        """
        contact = self.db.query(Contact).filter_by(id=contact_id).first()
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        service = self.db.query(Service).filter_by(id=service_id).first()
        if not service:
            raise ResourceNotFoundError(f"Service {service_id} not found")

        if service not in contact.services:
            return False

        contact.services.remove(service)
        self.db.commit()
        return True
