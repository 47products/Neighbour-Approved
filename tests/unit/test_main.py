"""
Unit tests for the main application module.

This module contains tests that verify the core application configuration
and initialization is correct, including application metadata and settings.
"""


def test_app_metadata(client):
    """
    Test that the application metadata is correctly configured.

    This test verifies that the FastAPI application has the correct title,
    description, and version as specified in the requirements.
    """
    openapi_schema = client.app.openapi()

    assert openapi_schema["info"]["title"] == "Neighbour Approved API"
    assert (
        "API for Neighbour Approved platform" in openapi_schema["info"]["description"]
    )
    assert openapi_schema["info"]["version"] == "0.1.0"


def test_api_router_inclusion(client):
    """
    Test that all necessary API routers have been correctly included in the application.

    This test ensures that the expected API routes are available in the application,
    indicating that the routers have been properly configured and included.
    """
    routes = [route.path for route in client.app.routes]

    # Verify that the health check endpoint is correctly registered
    assert "/api/v1/system/health/health_check" in routes
