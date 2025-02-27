"""
Unit tests for the main application module.

This module contains tests for the core API endpoints including the
health check endpoint. It verifies that the API returns the expected
responses and status codes.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
