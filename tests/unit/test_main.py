"""
Unit tests for the main application of the Neighbour Approved backend.

This module tests key aspects of the FastAPI application initialization,
including:
- Application startup behavior.
- OpenAPI schema generation.
- Application metadata (title, description, version).
- CORS middleware configuration.

The tests help ensure that the application is properly configured before
handling incoming requests.
"""

from app.main import app  # Import the FastAPI app created by the application factory


def test_application_startup(test_client):
    """
    Test that the application starts correctly and provides the default root response.

    This test sends a GET request to the "/" endpoint, which is not defined in the
    application. FastAPI should return a 404 response with the standard "Not Found" detail.

    Expected Outcome:
        - HTTP status code 404.
        - JSON response: {"detail": "Not Found"}.

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """
    response = test_client.get("/")
    assert response.status_code == 404  # Expected as no "/" route is defined
    assert response.json() == {"detail": "Not Found"}


def test_openapi_schema(test_client):
    """
    Test that the OpenAPI schema is correctly generated.

    This test verifies that the OpenAPI schema endpoint (/openapi.json) returns a valid
    JSON schema that includes the correct application information.

    Expected Outcome:
        - HTTP status code 200.
        - The JSON response contains an "info" field with the title "Neighbour Approved".

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "info" in schema
    assert schema["info"]["title"] == "Neighbour Approved"


def test_application_metadata():
    """
    Test that the application's metadata is correctly set.

    This test checks that the FastAPI application instance has the correct metadata
    as configured in the application factory, including title, description, and version.

    Expected Outcome:
        - app.title is "Neighbour Approved".
        - app.description is "A platform for community-driven endorsements of contractors.".
        - app.version is "0.1.0".

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """
    assert app.title == "Neighbour Approved"
    assert (
        app.description
        == "A platform for community-driven endorsements of contractors."
    )
    assert app.version == "0.1.0"


def test_cors_headers(test_client):
    """
    Test that CORS headers are properly set in responses based on allowed origins.

    This test sends a GET request with an Origin header to a known endpoint ("/openapi.json")
    and then checks whether the response includes the "access-control-allow-origin" header.
    The expected outcome depends on the application’s CORS settings:

    - If the provided Origin is allowed (or if "*" is configured), the response should include
      the "access-control-allow-origin" header with a value equal to the Origin or "*".
    - Otherwise, the header will not be present.

    Expected Outcome:
        - If the test origin is allowed, the header "access-control-allow-origin" is present and its
          value is either the test origin or "*".
        - If the test origin is not allowed, the header will be absent.

    Example:
        Run this test with pytest:
            pytest --maxfail=1 --disable-warnings -q
    """
    # Import the settings to determine allowed origins.
    from app.core.config import get_settings

    settings = get_settings()
    allowed_origins = settings.CORS_ORIGINS

    # Define the test origin.
    test_origin = "http://example.com"

    # Send a GET request to an endpoint that supports GET (e.g., /openapi.json).
    response = test_client.get("/openapi.json", headers={"Origin": test_origin})

    if test_origin in allowed_origins or "*" in allowed_origins:
        # If the test origin is allowed, then the CORS middleware should include the header.
        assert "access-control-allow-origin" in response.headers
        # The header value should either match the test origin or be set to "*".
        assert response.headers["access-control-allow-origin"] in [test_origin, "*"]
    else:
        # If the test origin is not allowed, then the header is not expected.
        assert "access-control-allow-origin" not in response.headers
