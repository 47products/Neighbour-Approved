"""
Shared test fixtures for the Neighbour Approved application.

This module provides reusable fixtures for unit and integration tests.
Key fixtures include:
- test_client: Test client for the FastAPI app.
- dummy_db: Dummy database session fixture using AsyncMock to simulate asynchronous 
  database operations.
- mock_user: Mock user object for testing user-related functionalities.
- mock_repository: Mock repository for simulating database interactions.
- base_user_service: Instance of BaseUserService with mocked dependencies.

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
from dotenv import load_dotenv
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.user_service.base_user import BaseUserService
from app.db.models.user_model import User
from app.db.repositories.user_repository import UserRepository

# Load test environment variables
load_dotenv(".env.test")


@pytest.fixture(scope="module")
def test_client():
    """
    Create and return a test client for the FastAPI application.

    This fixture instantiates a TestClient for the app and yields it for use in tests.

    Yields:
        TestClient: A test client for the FastAPI app.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def dummy_db():
    """
    Create a dummy asynchronous database session using AsyncMock.

    Returns:
        AsyncMock: A mocked AsyncSession with async methods.
    """
    db = AsyncMock(spec=AsyncSession)

    # Configure the async context manager
    context = AsyncMock()
    context.__aenter__ = AsyncMock(return_value=db)
    context.__aexit__ = AsyncMock(return_value=None)

    # Configure session methods:
    # Use MagicMock for begin_nested so that it returns the context immediately.
    from unittest.mock import MagicMock

    db.begin_nested = MagicMock(return_value=context)

    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()

    return db


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
        dummy_db: The mocked database session.

    Returns:
        MagicMock: A mocked UserRepository instance.
    """
    repository = MagicMock(spec=UserRepository)
    repository.get_by_email = AsyncMock(
        return_value=None
    )  # Default: no duplicate emails
    repository.get = AsyncMock()
    repository.update = AsyncMock()
    return repository


@pytest.fixture
def base_user_service(dummy_db, mock_repository):
    """
    Create an instance of BaseUserService with mocked dependencies.

    This fixture initializes BaseUserService with a mock database session and repository.

    Args:
        dummy_db: The mocked database session.
        mock_repository: The mocked UserRepository instance.

    Returns:
        BaseUserService: An instance with mocked database and repository.
    """
    service = BaseUserService(db=dummy_db)
    service._repository = mock_repository
    mock_repository.db = dummy_db
    return service
