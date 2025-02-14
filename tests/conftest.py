"""
Shared test fixtures for the Neighbour Approved application.

This module provides reusable fixtures for unit and integration tests.
Key fixtures include:
- test_client: Test client for the FastAPI app.
- dummy_db: Dummy asynchronous database session fixture using AsyncMock to simulate
  asynchronous database operations.
- sync_dummy_db: Dummy synchronous database session fixture (a MagicMock) for tests
  that require a synchronous Session.
- mock_user: Mock user object for testing user-related functionalities.
- mock_repository: Mock repository for simulating database interactions.
- base_user_service: Instance of BaseUserService with mocked dependencies.
- dummy_community: A dummy community model for testing.
- dummy_model: A dummy SQLAlchemy model class for testing retrieval mixin operations.

Usage:
    In tests, simply import the fixture by its name.
"""

import os
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import pytest
from fastapi.testclient import TestClient

from app.db.models.category_model import Category
from app.db.models.contact_model import Contact
from app.db.models.service_model import Service
from app.db.repositories.community_repository import CommunityRepository
from app.main import app
from app.services.community_service.community_service_base import CommunityService
from app.services.community_service.community_service_membership import (
    CommunityMembershipService,
)
from app.services.contact_service.contact_service_base import ContactService
from app.services.contact_service.contact_service_category import ContactServiceCategory
from app.services.contact_service.contact_service_endorsement import (
    ContactServiceEndorsement,
)
from app.services.contact_service.contact_service_service import ContactServiceService
from app.services.contact_service.contact_service_validation import (
    ContactServiceValidation,
)
from app.services.contact_service.contact_service_verification import (
    ContactServiceVerification,
)
from app.services.user_service.user_service_base_user import BaseUserService
from app.db.models.user_model import User
from app.db.repositories.user_repository import UserRepository

# Load test environment variables
load_dotenv(".env.test")


@pytest.fixture(scope="module")
def test_client():
    """
    Create and return a test client for the FastAPI application.

    Yields:
        TestClient: A test client for the FastAPI app.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    Provide test configuration values from environment variables.

    Returns:
        Dict[str, Any]: Dictionary containing all test configuration values.
    """
    return {
        "max_services": int(os.getenv("MAX_SERVICES", 20)),
        "max_categories": int(os.getenv("MAX_CATEGORIES", 5)),
        "max_contacts_free": int(os.getenv("MAX_CONTACTS_FREE", 10)),
        "max_communities_free": int(os.getenv("MAX_COMMUNITIES_FREE", 5)),
        "max_members_free": int(os.getenv("MAX_MEMBERS_FREE", 50)),
        "max_members_premium": int(os.getenv("MAX_MEMBERS_PREMIUM", 500)),
        "max_relationships": int(os.getenv("MAX_RELATIONSHIPS", 10)),
        "max_pending_invites": int(os.getenv("MAX_PENDING_INVITES", 100)),
        "max_pending_verifications": int(os.getenv("MAX_PENDING_VERIFICATIONS", 5)),
        "test_user_email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
        "test_user_id": int(os.getenv("TEST_USER_ID", 1)),
        "test_verifier_id": int(os.getenv("TEST_VERIFIER_ID", 99)),
        "test_community_name": os.getenv("TEST_COMMUNITY_NAME", "Test Community"),
        "test_community_id": int(os.getenv("TEST_COMMUNITY_ID", 1)),
        "test_contact_name": os.getenv("TEST_CONTACT_NAME", "Test Contact"),
        "test_contact_id": int(os.getenv("TEST_CONTACT_ID", 1)),
        "test_endorsement_id": int(os.getenv("TEST_ENDORSEMENT_ID", 123)),
        "test_endorsement_rating": float(os.getenv("TEST_ENDORSEMENT_RATING", 4.0)),
        "test_origin": os.getenv("TEST_ORIGIN", "http://example.com"),
    }


@pytest.fixture
def dummy_db(mock_user, mock_contact, mock_category, mock_service):
    """
    Create a dummy asynchronous database session using AsyncMock.

    Ensures db.get(User, user_id), db.get(Contact, contact_id), etc. return the correct instances.
    """
    db = AsyncMock(spec=AsyncSession)

    async def get_mock(model, obj_id):
        if model == User and obj_id == mock_user.id:
            return mock_user
        if model == Contact and obj_id == mock_contact.id:
            return mock_contact
        if model == Category and obj_id == mock_category.id:
            return mock_category
        if model == Service and obj_id == mock_service.id:
            return mock_service
        return None

    db.get = AsyncMock(side_effect=get_mock)
    db.query = MagicMock()
    db.query.return_value.filter_by.return_value.first = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    return db


@pytest.fixture
def sync_dummy_db():
    """
    Create a dummy synchronous database session.
    """
    return MagicMock(spec=Session)


@pytest.fixture
def mock_user():
    """
    Create a mock user object for testing.
    """
    return User(id=1, email="test@example.com", is_active=True)


@pytest.fixture
def mock_repository(dummy_db):
    """
    Create a mock repository instance simulating database operations.
    """
    repository = MagicMock(spec=UserRepository)
    repository.get_by_email = AsyncMock(return_value=None)
    repository.get = AsyncMock()
    repository.update = AsyncMock()
    return repository


@pytest.fixture
def base_user_service(dummy_db, mock_repository):
    """
    Create an instance of BaseUserService with mocked dependencies.
    """
    service = BaseUserService(db=dummy_db)
    service._repository = mock_repository
    mock_repository.db = dummy_db
    return service


@pytest.fixture
def dummy_community():
    """
    Create a dummy community instance for testing.
    """

    class DummyCommunity:
        def __init__(self, active=True):
            self.is_active = active
            self._sa_instance_state = object()

    return DummyCommunity


@pytest.fixture
def mock_community_repository(dummy_db):
    """
    Create a mock CommunityRepository for simulating database operations.
    """
    return MagicMock(spec=CommunityRepository)


@pytest.fixture
def community_service(dummy_db, mock_community_repository):
    """
    Create an instance of CommunityService with mocked dependencies.
    """
    return CommunityService(db=dummy_db, repository=mock_community_repository)


@pytest.fixture
def community_service_membership(dummy_db, mock_community_repository):
    """
    Create an instance of CommunityMembershipService with mocked dependencies.
    """
    service = CommunityMembershipService(db=dummy_db)
    service.repository = mock_community_repository
    return service


@pytest.fixture
def mock_db():
    """
    Provide a mocked database session.
    """
    return MagicMock()


@pytest.fixture
def mock_contact():
    """Create a dummy contact instance for testing."""
    return Contact(id=1, contact_name="Test Contact", is_active=True, categories=[])


@pytest.fixture
def mock_contact_data():
    """
    Create a mock contact data object for validation tests.
    """

    class MockContactData:
        def __init__(self):
            self.contact_name = "Valid Contact"
            self.primary_contact_first_name = "John"
            self.primary_contact_last_name = "Doe"
            self.email = "test@example.com"

    return MockContactData()


@pytest.fixture
def mock_contact_repository(dummy_db):
    """
    Create a mock ContactRepository for simulating database operations.
    """
    repository = MagicMock()
    repository.get = AsyncMock()
    repository.delete = AsyncMock(return_value=True)
    return repository


@pytest.fixture
def contact_service(dummy_db, mock_contact_repository):
    """
    Create an instance of ContactService with mocked dependencies.
    """
    from app.services.contact_service.contact_service_base import ContactService

    service = ContactService(db=dummy_db)
    service._repository = mock_contact_repository
    return service


@pytest.fixture
def contact_service_category(dummy_db, mock_contact_repository):
    """
    Create an instance of ContactServiceCategory with mocked dependencies.
    """
    from app.services.contact_service.contact_service_category import (
        ContactServiceCategory,
    )

    service = ContactServiceCategory(db=dummy_db)
    service.repository = mock_contact_repository
    return service


@pytest.fixture
def mock_category():
    """Create a dummy category instance for testing."""
    return Category(id=5, name="Plumbing")


@pytest.fixture
def contact_service_endorsement(mock_db):
    """
    Create an instance of ContactServiceEndorsement with a mocked database session.
    """
    from app.services.contact_service.contact_service_endorsement import (
        ContactServiceEndorsement,
    )

    return ContactServiceEndorsement(db=mock_db)


@pytest.fixture
def mock_service():
    """Create a dummy service instance for testing."""
    return Service(id=10, name="Test Service")


@pytest.fixture
def mock_service_repository(dummy_db):
    """
    Create a mock ServiceRepository for simulating database operations.
    """
    repository = MagicMock()
    repository.get = AsyncMock()
    repository.delete = AsyncMock(return_value=True)
    return repository


@pytest.fixture
def contact_service_service(dummy_db, mock_contact_repository, mock_service_repository):
    """
    Create an instance of ContactServiceService with mocked dependencies.
    """
    from app.services.contact_service.contact_service_service import (
        ContactServiceService,
    )

    service = ContactServiceService(db=dummy_db)
    service.contact_repository = mock_contact_repository
    service.service_repository = mock_service_repository
    return service


@pytest.fixture
def contact_service_validation(dummy_db):
    """
    Create an instance of ContactServiceValidation with a mocked database session.
    """
    from app.services.contact_service.contact_service_validation import (
        ContactServiceValidation,
    )

    return ContactServiceValidation(db=dummy_db)


@pytest.fixture
def contact_service_verification(dummy_db):
    """
    Create an instance of ContactServiceVerification with a mocked database session.
    """
    from app.services.contact_service.contact_service_verification import (
        ContactServiceVerification,
    )

    return ContactServiceVerification(db=dummy_db)


@pytest.fixture
def mock_verifiable_contact():
    """
    Create a mock contact that meets verification criteria.
    """
    from app.db.models.contact_model import Contact

    contact = MagicMock(spec=Contact)
    contact.id = 1
    contact.is_active = True
    contact.email = "verified@example.com"
    contact.contact_number = "123456789"
    contact.primary_contact_contact_number = "987654321"
    contact.endorsements_count = 3
    contact.communities = [MagicMock()]
    contact.is_verified = False
    contact.verification_date = None
    contact.verification_notes = None
    return contact


@pytest.fixture
def mock_unverifiable_contact():
    """
    Create a mock contact that does not meet verification criteria.
    """
    from app.db.models.contact_model import Contact

    contact = MagicMock(spec=Contact)
    contact.id = 2
    contact.is_active = False
    contact.email = "unverified@example.com"
    contact.contact_number = None
    contact.primary_contact_contact_number = None
    contact.endorsements_count = 1
    contact.communities = []
    return contact


@pytest.fixture
def mock_model():
    """
    Create a mock SQLAlchemy model class with a valid __name__ attribute.
    """
    mock = MagicMock(spec=User)
    mock.__name__ = "User"
    return mock


@pytest.fixture
def mock_repository(dummy_db):
    """
    Create a mock repository instance that simulates database operations.
    """
    repo = MagicMock()
    repo.db = dummy_db
    repo.create = AsyncMock()
    repo.get = AsyncMock()
    repo.get_multi = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def dummy_model():
    """
    Fixture for a dummy User model with necessary attributes.

    This model is built on a SQLAlchemy Table to simulate real column expressions.
    Returns a mapped model class using declarative_base.
    """
    from sqlalchemy import Column, Integer, String, Boolean
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

    class DummyUserModel(Base):
        __tablename__ = "dummy"
        id = Column(Integer, primary_key=True)
        email = Column(String)
        first_name = Column(String)
        last_name = Column(String)
        is_active = Column(Boolean)
        email_verified = Column(Boolean)

    # Simulate a roles attribute with an 'any' method.
    from sqlalchemy.sql import literal

    class DummyRoles:
        def any(self, **kwargs):
            return literal(True)

    DummyUserModel.roles = DummyRoles()
    return DummyUserModel
