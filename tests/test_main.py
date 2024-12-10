"""
This module contains tests for verifying the functionality of the Neighbour Approved
application's main endpoints. It uses the FastAPI TestClient to make requests against
the application instance defined in `app.main`.

The test below checks the `/health` endpoint to ensure that the service responds
correctly and is operational.
"""

from fastapi.testclient import TestClient
from app.main import app


def test_health_check():
    """
    Test the /health endpoint of the application.

    Steps:
    1. Create a TestClient instance for the FastAPI `app`.
    2. Send a GET request to the `/health` endpoint.
    3. Assert that the response status code is 200 (OK).
    4. Assert that the JSON response body matches {"status": "ok"}.

    Expected Outcome:
    If the application is running and the health endpoint is implemented correctly,
    the test should pass, indicating the service is operational.
    """
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200, "Health endpoint should return HTTP 200"
    assert response.json() == {
        "status": "ok"
    }, "Health endpoint should return the expected JSON response"
