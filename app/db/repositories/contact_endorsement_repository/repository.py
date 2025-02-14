"""
Contact Endorsement Repository Module.

This module composes the various mixins to implement the full repository for
contact endorsement data access operations. Business logic resides in the service layer.

Usage Example:
    from app.db.repositories.contact_endorsement_repository import ContactEndorsementRepository

    repo = ContactEndorsementRepository(db_session)

Dependencies:
    - app.db.repositories.repository_implementation.BaseRepository (Base repository class)
    - app.db.models.contact_endorsement_model.ContactEndorsement (Contact endorsement model)
    - app.api.v1.schemas.contact_endorsement_schema.ContactEndorsementCreate, ContactEndorsementUpdate (Schema definitions)
    - Mixins: ContactEndorsementQueriesMixin, ContactEndorsementStatsMixin, ContactEndorsementDeletionMixin
"""

from sqlalchemy.orm import Session
from app.db.repositories.repository_implementation import BaseRepository
from app.db.models.contact_endorsement_model import ContactEndorsement
from app.api.v1.schemas.contact_endorsement_schema import (
    ContactEndorsementCreate,
    ContactEndorsementUpdate,
)
from .queries import ContactEndorsementQueriesMixin
from .stats import ContactEndorsementStatsMixin
from .deletion import ContactEndorsementDeletionMixin


class ContactEndorsementRepository(
    ContactEndorsementQueriesMixin,
    ContactEndorsementStatsMixin,
    ContactEndorsementDeletionMixin,
    BaseRepository[
        ContactEndorsement, ContactEndorsementCreate, ContactEndorsementUpdate
    ],
):
    """
    Repository for contact endorsement data access operations.

    Combines functionality for querying, statistics, and deletion.
    """

    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.

        Args:
            db (Session): Database session for operations.
        """
        super().__init__(ContactEndorsement, db)
