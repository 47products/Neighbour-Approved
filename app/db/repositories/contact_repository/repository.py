"""
Contact Repository Module.

This module implements the ContactRepository class which combines multiple mixins
to provide a comprehensive repository for managing contact data. It integrates
query, service, category, and endorsement functionalities along with the base
repository implementation.

Usage Example:
    from app.db.repositories.contact_repository import ContactRepository

    repo = ContactRepository(db_session)
    contact = await repo.get_by_email("user@example.com")

Dependencies:
    - SQLAlchemy ORM (for database session management)
    - app.db.models.contact_model.Contact (Contact model)
    - app.api.v1.schemas.contact_schema.ContactCreate, ContactUpdate (Schema definitions)
    - Various mixins for queries, services, categories, and endorsements.
"""

from sqlalchemy.orm import Session
from app.db.repositories.repository_implementation import BaseRepository
from app.db.models.contact_model import Contact
from app.api.v1.schemas.contact_schema import ContactCreate, ContactUpdate
from .queries import ContactQueriesMixin
from .services import ContactServicesMixin
from .categories import ContactCategoriesMixin
from .endorsements import ContactEndorsementsMixin


class ContactRepository(
    ContactQueriesMixin,
    ContactServicesMixin,
    ContactCategoriesMixin,
    ContactEndorsementsMixin,
    BaseRepository[Contact, ContactCreate, ContactUpdate],
):
    """
    Repository for managing contact data access operations.

    Combines functionality from multiple mixins to provide a comprehensive
    interface for performing CRUD operations and complex queries on contact records.

    Attributes:
        db (Session): The SQLAlchemy database session.
        _model: The Contact model.
        _logger: Logger instance for structured logging.
    """

    def __init__(self, db: Session):
        """
        Initialize the ContactRepository with a database session.

        Args:
            db (Session): The SQLAlchemy database session to be used for operations.
        """
        super().__init__(Contact, db)
