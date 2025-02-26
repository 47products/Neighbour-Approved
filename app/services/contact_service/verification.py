"""
Contact Service Verification Module.

This module handles verification-related operations for contacts, including
validating contacts against verification criteria and updating their status.

Key Components:
- ContactServiceVerification: Manages contact verification workflows.

Typical usage example:
    verification_service = ContactServiceVerification(db_session)
    await verification_service.verify_contact(contact_id=1, verified_by=2)
"""

from sqlalchemy.orm import Session
from datetime import datetime, UTC
from app.db.models.contact_model import Contact
from app.services.service_exceptions import (
    ResourceNotFoundError,
    ValidationError,
    StateError,
)


class ContactServiceVerification:
    """
    Manages verification workflows for contacts.

    This service provides methods for verifying contacts and ensuring they meet
    required verification criteria.

    Attributes:
        db (Session): Database session for verification-related queries.
    """

    def __init__(self, db: Session):
        """Initialize the verification management module.

        Args:
            db (Session): Database session for verification-related queries.
        """
        self.db = db

    async def verify_contact(self, contact_id: int, verified_by: int) -> bool:
        """Mark a contact as verified.

        Args:
            contact_id (int): The unique identifier of the contact.
            verified_by (int): The user ID performing the verification.

        Returns:
            bool: True if the contact was successfully verified.

        Raises:
            ResourceNotFoundError: If the contact is not found.
            ValidationError: If the contact does not meet verification criteria.
            StateError: If verification fails due to an unexpected state.
        """
        contact = self.db.query(Contact).filter_by(id=contact_id).first()
        if not contact:
            raise ResourceNotFoundError(f"Contact {contact_id} not found")

        if not self._meets_verification_criteria(contact):
            raise ValidationError("Contact does not meet verification requirements")

        try:
            contact.is_verified = True
            contact.verification_date = datetime.now(UTC)
            contact.verification_notes = (
                f"Verified by user {verified_by} on {datetime.now(UTC)}"
            )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise StateError(f"Failed to verify contact: {str(e)}")

    def _meets_verification_criteria(self, contact: Contact) -> bool:
        """Check if a contact meets verification criteria.

        A contact can be verified if it has required profile information,
        a minimum number of endorsements, and is linked to active communities.

        Args:
            contact (Contact): The contact to evaluate.

        Returns:
            bool: True if the contact meets verification criteria, False otherwise.
        """
        if not contact.is_active:
            return False

        if not all(
            [
                contact.email,
                contact.contact_number,
                contact.primary_contact_contact_number,
            ]
        ):
            return False

        if contact.endorsements_count < 3:
            return False

        if not contact.communities:
            return False

        return True
