"""
Contact Service Endorsement Module.

This module manages endorsement-related operations for contacts, including endorsement
calculations, retrieval, and verification workflows.

Key Components:
- ContactServiceEndorsement: Handles endorsement updates and retrieval.

Typical usage example:
    endorsement_service = ContactServiceEndorsement(db_session)
    endorsements = await endorsement_service.get_contact_endorsements(contact_id=1)
"""

from sqlalchemy.orm import Session
from app.db.models.contact_model import Contact
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.services.service_exceptions import ResourceNotFoundError


class ContactServiceEndorsement:
    """
    Manages endorsement-related operations for contacts.

    This service provides methods to retrieve, update, and verify endorsements.

    Attributes:
        db (Session): Database session for endorsement queries.
    """

    def __init__(self, db: Session):
        """Initialize the endorsement service.

        Args:
            db (Session): Database session for endorsement-related queries.
        """
        self.db = db

    async def get_contact_endorsements(
        self, contact_id: int
    ) -> list[ContactEndorsement]:
        """Retrieve all endorsements for a given contact.

        Args:
            contact_id (int): The unique identifier of the contact.

        Returns:
            list[ContactEndorsement]: A list of endorsements related to the contact.

        Raises:
            ResourceNotFoundError: If the contact is not found.
        """
        contact = self.db.query(Contact).filter_by(id=contact_id).first()
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        return contact.endorsements
