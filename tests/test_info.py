# File: tests/test_info.py

"""
Test Module for the `/api/v1/info` Endpoint of Neighbour Approved Backend.

This module contains test cases to verify the functionality and correctness of the
`/api/v1/info` endpoint. The tests ensure that the endpoint returns the expected
status codes and response data, adhering to the defined Pydantic schemas.

The tests utilize FastAPI's `TestClient` for making HTTP requests to the FastAPI
application instance defined in `app.main`. This allows for end-to-end testing of
the API endpoints without requiring the application to be running on a live server.
"""

from fastapi.testclient import TestClient
from app.main import app

# Initialize the TestClient with the FastAPI app instance
client = TestClient(app)


def test_get_info():
    """
    Test the `/api/v1/info` Endpoint.

    This test case verifies that the `/api/v1/info` endpoint responds correctly.
    It checks the following:

    1. **Status Code:** Ensures that the endpoint returns an HTTP 200 OK status.
    2. **Response Structure:** Validates that the JSON response matches the
       expected structure defined by the `InfoResponse` Pydantic schema.
    3. **Response Data:** Confirms that the response data contains the correct
       application name and version.

    **Steps:**
    1. Send a GET request to the `/api/v1/info` endpoint using the TestClient.
    2. Assert that the response status code is 200.
    3. Parse the JSON response.
    4. Assert that the `name` field in the response matches "Neighbour Approved".
    5. Assert that the `version` field in the response matches "0.1.0".

    **Expected Outcome:**
    The `/api/v1/info` endpoint should return a JSON response with the following structure:
    ```json
    {
        "name": "Neighbour Approved",
        "version": "0.1.0"
    }
    ```
    and an HTTP status code of 200.

    **Example:**
    ```
    GET /api/v1/info
    Response:
    {
        "name": "Neighbour Approved",
        "version": "0.1.0"
    }
    ```
    """
    # Send a GET request to the `/api/v1/info` endpoint
    response = client.get("/api/v1/info")

    # Assert that the response status code is 200 OK
    assert response.status_code == 200, "Info endpoint should return HTTP 200"

    # Parse the JSON response body
    data = response.json()

    # Assert that the `name` field is correct
    assert data["name"] == "Neighbour Approved", "App name should match expected value"

    # Assert that the `version` field is correct
    assert data["version"] == "0.1.0", "App version should match expected value"
