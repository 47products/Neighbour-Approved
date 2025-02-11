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

Usage:
    In tests, simply import the fixture by its name.

Dependencies:
    - pytest
    - fastapi.testclient
    - dotenv
    - app.main: The FastAPI application instance.
"""

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


@pytest.fixture
def dummy_db(mock_user, mock_contact, mock_category, mock_service):
    """
    Create a dummy asynchronous database session using AsyncMock.

    Ensures db.get(User, user_id), db.get(Contact, contact_id), db.get(Category, category_id),
    and db.get(Service, service_id) return the correct instances.

    Returns:
        AsyncMock: A mocked AsyncSession with async methods.
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
        return None  # Simulate entity not found

    db.get = AsyncMock(side_effect=get_mock)  # Mock db.get() properly

    # Mock .query() to support .filter_by().first()
    db.query = MagicMock()
    db.query.return_value.filter_by.return_value.first = MagicMock()

    db.commit = AsyncMock()
    db.rollback = AsyncMock()

    return db


@pytest.fixture
def sync_dummy_db():
    """
    Create a dummy synchronous database session.

    Returns:
        MagicMock: A mocked synchronous Session.
    """
    return MagicMock(spec=Session)


@pytest.fixture
def mock_user():
    """
    Create a mock user object for testing.

    Returns:
        User: A mocked user instance with predefined attributes.
    """
    return User(id=1, email="test@example.com", is_active=True)


@pytest.fixture
def mock_repository(dummy_db):
    """
    Create a mock UserRepository for simulating database operations.

    This fixture replaces actual repository calls with AsyncMock instances.

    Args:
        dummy_db: The mocked asynchronous database session.

    Returns:
        MagicMock: A mocked UserRepository instance.
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

    Args:
        dummy_db: The mocked asynchronous database session.
        mock_repository: The mocked UserRepository instance.

    Returns:
        BaseUserService: An instance with mocked database and repository.
    """
    service = BaseUserService(db=dummy_db)
    service._repository = mock_repository
    mock_repository.db = dummy_db
    return service


@pytest.fixture
def dummy_community():
    """
    Create a dummy community instance for testing.

    Returns:
        DummyCommunity: A class that can be instantiated to simulate a community.
    """

    class DummyCommunity:
        def __init__(self, active=True):
            self.is_active = active
            # Provide a dummy _sa_instance_state to satisfy SQLAlchemy instrumentation.
            self._sa_instance_state = object()

    return DummyCommunity


@pytest.fixture
def mock_community_repository(dummy_db):
    """
    Create a mock CommunityRepository for simulating database operations.

    Args:
        dummy_db: The mocked asynchronous database session.

    Returns:
        MagicMock: A mocked CommunityRepository instance.
    """
    return MagicMock(spec=CommunityRepository)


@pytest.fixture
def community_service(dummy_db, mock_community_repository):
    """
    Create an instance of CommunityService with mocked dependencies.

    Args:
        dummy_db: The mocked asynchronous database session.
        mock_community_repository: The mocked CommunityRepository instance.

    Returns:
        CommunityService: An instance with mocked dependencies.
    """
    return CommunityService(db=dummy_db, repository=mock_community_repository)


@pytest.fixture
def community_service_membership(dummy_db, mock_community_repository):
    """
    Create an instance of CommunityMembershipService with mocked dependencies.

    Args:
        dummy_db: The mocked asynchronous database session.
        mock_community_repository: The mocked CommunityRepository instance.

    Returns:
        CommunityMembershipService: An instance with mocked dependencies.
    """
    service = CommunityMembershipService(db=dummy_db)
    service.repository = mock_community_repository
    return service


@pytest.fixture
def mock_db():
    """
    Provide a mocked database session.

    Returns:
        MagicMock: A mock of the database session.
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

    Returns:
        A class mimicking an actual contact data object with necessary attributes.
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

    Args:
        dummy_db: The mocked asynchronous database session.

    Returns:
        MagicMock: A mocked ContactRepository instance.
    """
    repository = MagicMock()
    repository.get = AsyncMock()
    repository.delete = AsyncMock(return_value=True)
    return repository


@pytest.fixture
def contact_service(dummy_db, mock_contact_repository):
    """
    Create an instance of ContactService with mocked dependencies.

    Args:
        dummy_db: The mocked asynchronous database session.
        mock_contact_repository: The mocked ContactRepository instance.

    Returns:
        ContactService: An instance with mocked dependencies.
    """
    service = ContactService(db=dummy_db)
    service._repository = mock_contact_repository
    return service


@pytest.fixture
def contact_service_category(dummy_db, mock_contact_repository):
    """Create an instance of ContactServiceCategory with mocked dependencies."""
    service = ContactServiceCategory(db=dummy_db)
    service.repository = mock_contact_repository  # Ensure repository is used
    return service


@pytest.fixture
def mock_category():
    """Create a dummy category instance for testing."""
    return Category(id=5, name="Plumbing")


@pytest.fixture
def contact_service_endorsement(mock_db):
    """
    Create an instance of ContactServiceEndorsement with a mocked database session.

    Args:
        mock_db (MagicMock): Mocked database session.

    Returns:
        ContactServiceEndorsement: Instance of the endorsement service.
    """
    return ContactServiceEndorsement(db=mock_db)


@pytest.fixture
def mock_service():
    """Create a dummy service instance for testing."""
    return Service(id=10, name="Test Service")


@pytest.fixture
def mock_service_repository(dummy_db):
    """
    Create a mock ServiceRepository for simulating database operations.

    Args:
        dummy_db: The mocked asynchronous database session.

    Returns:
        MagicMock: A mocked ServiceRepository instance.
    """
    repository = MagicMock()
    repository.get = AsyncMock()
    repository.delete = AsyncMock(return_value=True)
    return repository


@pytest.fixture
def contact_service_service(dummy_db, mock_contact_repository, mock_service_repository):
    """
    Create an instance of ContactServiceService with mocked dependencies.

    Args:
        dummy_db (AsyncMock): The mocked asynchronous database session.
        mock_contact_repository (MagicMock): The mocked ContactRepository instance.
        mock_service_repository (MagicMock): The mocked ServiceRepository instance.

    Returns:
        ContactServiceService: An instance with mocked dependencies.
    """
    service = ContactServiceService(db=dummy_db)
    service.contact_repository = mock_contact_repository
    service.service_repository = mock_service_repository
    return service


@pytest.fixture
def contact_service_validation(dummy_db):
    """
    Create an instance of ContactServiceValidation with a mocked database session.

    Args:
        dummy_db (AsyncMock): The mocked asynchronous database session.

    Returns:
        ContactServiceValidation: An instance with mocked dependencies.
    """
    return ContactServiceValidation(db=dummy_db)


@pytest.fixture
def contact_service_verification(dummy_db):
    """
    Create an instance of ContactServiceVerification with a mocked database session.

    Args:
        dummy_db (AsyncMock): The mocked asynchronous database session.

    Returns:
        ContactServiceVerification: An instance with mocked dependencies.
    """
    return ContactServiceVerification(db=dummy_db)


@pytest.fixture
def mock_verifiable_contact():
    """
    Create a mock contact that meets verification criteria.

    Returns:
        MagicMock: A mock Contact instance with verification attributes.
    """
    contact = MagicMock(spec=Contact)
    contact.id = 1
    contact.is_active = True
    contact.email = "verified@example.com"
    contact.contact_number = "123456789"
    contact.primary_contact_contact_number = "987654321"
    contact.endorsements_count = 3
    contact.communities = [MagicMock()]  # Simulating active community links
    contact.is_verified = False
    contact.verification_date = None
    contact.verification_notes = None
    return contact


@pytest.fixture
def mock_unverifiable_contact():
    """
    Create a mock contact that does not meet verification criteria.

    Returns:
        MagicMock: A mock Contact instance missing required attributes.
    """
    contact = MagicMock(spec=Contact)
    contact.id = 2
    contact.is_active = False  # Inactive contact should not be verified
    contact.email = "unverified@example.com"
    contact.contact_number = None  # Missing phone number
    contact.primary_contact_contact_number = None
    contact.endorsements_count = 1  # Not enough endorsements
    contact.communities = []  # No linked communities
    return contact
