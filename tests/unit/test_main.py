# pylint: disable=unused-argument
"""
Unit tests for the main application module.

This module contains tests that verify the core application configuration
and initialization is correct, including application metadata and settings.
"""

from tests.conftest import health_url


def test_app_metadata(client, health_settings, mock_env_vars):
    """
    Test that the application metadata is correctly configured.

    This test verifies that the FastAPI application has the correct title,
    description, and version as specified in the requirements.

    Args:
        client: FastAPI test client fixture
        test_settings: Test configuration settings fixture
        mock_env_vars: Fixture that sets up environment variables
    """
    openapi_schema = client.app.openapi()

    assert openapi_schema["info"]["title"] == "Neighbour Approved API"
    assert (
        "API for Neighbour Approved platform" in openapi_schema["info"]["description"]
    )
    assert openapi_schema["info"]["version"] == health_settings["version"]


def test_api_router_inclusion(client, health_settings):
    """
    Test that all necessary API routers have been correctly included in the application.

    This test ensures that the expected API routes are available in the application,
    indicating that the routers have been properly configured and included.

    Args:
        client: FastAPI test client fixture
        test_settings: Test configuration settings fixture
    """
    routes = [route.path for route in client.app.routes]

    # Verify that the health check endpoint is correctly registered
    # Use the health_url helper to construct the expected path
    expected_health_check_path = health_url("/health_check", health_settings)
    assert expected_health_check_path in routes


def test_environment_configuration_applied(client, mock_env_vars):
    """
    Test that environment configuration is correctly applied to the application.

    This test ensures that the application properly loads and applies environment
    configuration, which is important for correct operation across different
    deployment environments.

    Args:
        client: FastAPI test client fixture
        mock_env_vars: Fixture that sets up environment variables
    """
    # The mock_env_vars fixture ensures environment variables are set correctly
    # Make a request to an endpoint that would reflect environment configuration
    response = client.get("/api/v1/system/health/health_check")

    # Verify the response contains the expected version from environment
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"
