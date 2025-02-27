"""
Unit tests for the health check endpoint.

This module contains tests for the system health check endpoint
to verify it returns the expected responses and status codes.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """
    Test that the health check endpoint returns a 200 status code
    and the correct response data.
    """
    response = client.get("/api/v1/system/health/health_check")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
