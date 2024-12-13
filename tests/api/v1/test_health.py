"""
Test Module for the `/health` Endpoint of Neighbour Approved Backend.

This module contains test cases to verify the functionality and correctness of the
`/health` endpoint. The tests ensure that the endpoint is accessible, returns the
expected JSON payload, and responds with the correct HTTP status code.
"""

from fastapi.testclient import TestClient
from app.main import app

# Initialize the TestClient with the FastAPI app instance
client = TestClient(app)


def test_health_status_code():
    """
    Test that the /health endpoint returns an HTTP 200 status code.

    Steps:
    1. Send a GET request to the /health endpoint.
    2. Assert that the response status code is 200.

    Expected Outcome:
    The /health endpoint should respond with HTTP 200 OK.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200, "Expected status code 200 for /health endpoint"


def test_health_response_content():
    """
    Test that the /health endpoint returns the expected JSON response.

    Steps:
    1. Send a GET request to the /health endpoint.
    2. Assert that the response status code is 200.
    3. Assert that the JSON response matches {"status": "ok"}.

    Expected Outcome:
    The /health endpoint should return a JSON response with {"status": "ok"}.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200, "Expected status code 200 for /health endpoint"
    assert response.json() == {
        "status": "ok"
    }, "Expected JSON response {'status': 'ok'}"
