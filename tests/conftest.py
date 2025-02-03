"""
Shared test fixtures for the Neighbour Approved application.

This module provides reusable fixtures for unit and integration tests.
Key fixtures include:
- test_client: Test client for the FastAPI app.
- dummy_db: Dummy database session fixture using AsyncMock to simulate asynchronous 
database operations.

Usage:
    In tests, simply import the fixture by its name.

Dependencies:
    - pytest
    - fastapi.testclient
    - dotenv
    - app.main: The FastAPI application instance.
"""

from unittest.mock import AsyncMock
from dotenv import load_dotenv
import pytest
from fastapi.testclient import TestClient
from app.main import app

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

    This fixture provides asynchronous methods such as commit() and rollback()
    to allow testing of service methods without a real database.

    Returns:
        AsyncMock: A mocked database session with asynchronous methods.
    """
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.get = AsyncMock()  # For methods like assign_role that use db.get(...)
    db.query = AsyncMock()  # For queries when needed.
    return db
