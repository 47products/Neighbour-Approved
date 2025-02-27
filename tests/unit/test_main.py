"""
Unit tests for the main application module.

This module contains tests for the core API endpoints including the
health check endpoint. It verifies that the API returns the expected
responses and status codes.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """
    Test that the health check endpoint returns a 200 status code
    and the correct response data.
    """
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
