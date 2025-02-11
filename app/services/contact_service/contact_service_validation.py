"""
Contact Service Validation Module.

This module handles validation logic for contact creation and updates, ensuring compliance
with business rules and preventing duplicate records.

Key Components:
- ContactServiceValidation: Provides validation methods for contact creation and updates.

Typical usage example:
    validator = ContactServiceValidation(db_session)
    await validator.validate_contact_creation(contact_data)
"""

from sqlalchemy.orm import Session
from app.services.service_exceptions import (
    ValidationError,
    DuplicateResourceError,
)
from app.db.models.contact_model import Contact


class ContactServiceValidation:
    """
    Provides validation methods for contact creation and updates.

    This class enforces required fields, restricts certain words, and ensures contact uniqueness.

    Attributes:
        db (Session): Database session for validation queries.
        MAX_CONTACTS_FREE (int): Maximum contacts allowed for free users.
        RESTRICTED_WORDS (set): Words restricted in contact names.
        REQUIRED_FIELDS (set): Fields that must be provided for contact creation.
    """

    MAX_CONTACTS_FREE = 10
    RESTRICTED_WORDS = {"admin", "system", "support", "test"}
    REQUIRED_FIELDS = {
        "contact_name",
        "primary_contact_first_name",
        "primary_contact_last_name",
        "email",
    }

    def __init__(self, db: Session):
        """Initialize the validation service.

        Args:
            db (Session): Database session for validation queries.
        """
        self.db = db

    async def validate_contact_creation(self, data):
        """Validates contact creation data.

        This method ensures all required fields are present, checks for restricted words,
        and prevents duplicate contact records based on email.

        Args:
            data: Contact creation data.

        Raises:
            ValidationError: If required fields are missing or restricted words are used.
            BusinessRuleViolationError: If business rules are violated.
            DuplicateResourceError: If a contact with the same email already exists.
        """
        missing_fields = self.REQUIRED_FIELDS - {
            k for k, v in data.__dict__.items() if v is not None
        }
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        if any(word in data.contact_name.lower() for word in self.RESTRICTED_WORDS):
            raise ValidationError("Contact name contains restricted words.")

        existing_contact = self.db.query(Contact).filter_by(email=data.email).first()
        if existing_contact:
            raise DuplicateResourceError("Contact with this email already exists.")
