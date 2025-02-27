"""
Test configuration and fixtures for the Neighbour Approved API.

This module provides shared fixtures and configuration for unit tests.
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient for the application.

    This fixture provides a test client for making requests to the API
    during tests. It's configured with scope="function" to ensure a fresh
    client for each test, preventing state from leaking between tests.

    Yields:
        TestClient: A test client for the FastAPI application
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def test_settings() -> dict:
    """
    Provide test configuration settings.

    This fixture contains environment-specific settings for tests,
    allowing for consistent configuration across test modules.

    Returns:
        dict: A dictionary of test configuration settings
    """
    return {
        "version": "0.1.0",
        "api_base_url": "/api/v1",
        "system_base_url": "/api/v1/system",
        "health_base_url": "/api/v1/system/health",
    }
