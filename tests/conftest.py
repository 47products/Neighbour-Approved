import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def test_client():
    """Fixture for creating a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client
