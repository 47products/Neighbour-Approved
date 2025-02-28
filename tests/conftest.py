# pylint: disable=unused-argument
"""
Test configuration and fixtures for the Neighbour Approved API.

This module provides shared fixtures and configuration for unit tests.
It centralises common test components to improve maintainability and
consistency across the test suite.
"""

import asyncio
from typing import Generator, Dict, Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.configuration.config import get_settings


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
def health_settings() -> Dict[str, Any]:
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


@pytest.fixture(scope="function")
def mock_env_vars(monkeypatch):
    """
    Set up environment variables for testing.

    This fixture sets common environment variables needed for many tests.
    It helps standardise the test environment across different test modules.

    Args:
        monkeypatch: Pytest fixture for modifying the environment

    Yields:
        None: The fixture makes environment changes and cleans up after tests
    """
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("VERSION", "0.1.0")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("API_BASE_URL", "/api/v1")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_FORMAT", "standard")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "false")

    # Clear any cached settings
    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()

    yield

    # Clear cache again after tests
    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for tests.

    This fixture provides a consistent event loop for async tests,
    ensuring proper cleanup after test execution.

    Yields:
        asyncio.AbstractEventLoop: The event loop for async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_user():
    """
    Provide a test user for authentication tests.

    Returns:
        dict: A dictionary containing test user information
    """
    return {
        "id": 1,
        "email": "test@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def auth_headers(user_data):
    """
    Provide authentication headers for authenticated requests.

    Args:
        user_data: The test user fixture

    Returns:
        dict: A dictionary containing authorization headers
    """
    # This is a simplified example - in a real implementation, you'd use
    # your actual JWT creation logic to generate a valid token
    mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.mock_token"

    return {"Authorization": f"Bearer {mock_token}"}


# URL helper functions
def api_url(path: str, test_settings: dict) -> str:
    """
    Construct an API URL for testing.

    Args:
        path: The endpoint path
        test_settings: Test settings fixture

    Returns:
        str: The full API URL
    """
    return f"{test_settings['api_base_url']}{path}"


def system_url(path: str, test_settings: dict) -> str:
    """
    Construct a system URL for testing.

    Args:
        path: The endpoint path
        test_settings: Test settings fixture

    Returns:
        str: The full system URL
    """
    return f"{test_settings['system_base_url']}{path}"


def health_url(path: str, test_settings: dict) -> str:
    """
    Construct a health endpoint URL for testing.

    Args:
        path: The endpoint path
        test_settings: Test settings fixture

    Returns:
        str: The full health URL
    """
    return f"{test_settings['health_base_url']}{path}"


# Response assertion helpers
def assert_successful_response(response, expected_status_code=200):
    """
    Assert that an API response is successful.

    Args:
        response: The HTTP response object
        expected_status_code: The expected HTTP status code

    Raises:
        AssertionError: If any assertions fail
    """
    assert response.status_code == expected_status_code
    assert response.headers["content-type"] == "application/json"
    assert "content-length" in response.headers


def assert_error_response(response, expected_status_code=400):
    """
    Assert that an API response is an error.

    Args:
        response: The HTTP response object
        expected_status_code: The expected HTTP status code

    Raises:
        AssertionError: If any assertions fail
    """
    assert response.status_code == expected_status_code
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    assert "error_code" in data
    assert "message" in data


class MockFactory:
    """Factory for creating minimal mocks when needed."""

    @staticmethod
    def external_service():
        """
        Create a mock for an external service that can't be used in tests.

        Returns:
            MagicMock: A mock with essential behaviour configured
        """
        mock = MagicMock()
        # Configure only the essential behaviours
        mock.get_data.return_value = {"key": "value"}
        return mock
