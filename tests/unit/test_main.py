def test_application_startup(test_client):
    """Test that the application starts correctly and provides the default root response."""
    response = test_client.get("/")
    assert response.status_code == 404  # Expected as no "/" route is defined
    assert response.json() == {
        "detail": "Not Found"
    }  # FastAPI default for undefined routes
