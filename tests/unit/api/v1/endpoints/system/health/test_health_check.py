"""
Unit tests for the health check endpoint.

This module contains tests for the system health check endpoint
to verify it returns the expected responses and status codes.
"""


def test_health_check(client, test_settings):
    """
    Test that the health check endpoint returns a 200 status code
    and the correct response data.

    This test ensures that the health check endpoint is operational
    and returns the expected status and version information.

    Args:
        client: FastAPI test client fixture
        test_settings: Test configuration settings fixture
    """
    # Construct the health check endpoint URL using the test settings
    health_check_url = f"{test_settings['health_base_url']}/health_check"

    # Make the request to the health check endpoint
    response = client.get(health_check_url)

    # Verify the response status code and content
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": test_settings["version"]}


def test_health_check_response_headers(client, test_settings):
    """
    Test that the health check endpoint returns appropriate headers.

    This test verifies that the response includes the expected content type
    and other standard headers required for proper API operation.

    Args:
        client: FastAPI test client fixture
        test_settings: Test configuration settings fixture
    """
    health_check_url = f"{test_settings['health_base_url']}/health_check"
    response = client.get(health_check_url)

    # Verify response headers
    assert response.headers["content-type"] == "application/json"
    assert "content-length" in response.headers
