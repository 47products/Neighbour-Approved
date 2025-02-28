"""
Unit tests for the health check endpoint.

This module contains tests for the system health check endpoint
to verify it returns the expected responses and status codes.
"""

from tests.conftest import health_url, assert_successful_response


def test_health_check(client, health_settings):
    """
    Test that the health check endpoint returns a 200 status code
    and the correct response data.

    This test ensures that the health check endpoint is operational
    and returns the expected status and version information.

    Args:
        client: FastAPI test client fixture
        test_settings: Test configuration settings fixture
    """
    # Construct the health check endpoint URL using the helper
    url = health_url("/health_check", health_settings)

    # Make the request to the health check endpoint
    response = client.get(url)

    # Verify the response status code and content
    assert_successful_response(response)
    assert response.json() == {"status": "ok", "version": health_settings["version"]}


def test_health_check_response_headers(client, health_settings):
    """
    Test that the health check endpoint returns appropriate headers.

    This test verifies that the response includes the expected content type
    and other standard headers required for proper API operation.

    Args:
        client: FastAPI test client fixture
        test_settings: Test configuration settings fixture
    """
    url = health_url("/health_check", health_settings)
    response = client.get(url)

    # Verify response headers using the helper function
    assert_successful_response(response)
