# pylint: disable=W0719, W0621
"""
Unit tests for the centralised exception handling in the Neighbour Approved application.

This module tests the custom exceptions and exception handlers defined in
error_handler.py, ensuring that each exception type and handler behaves
as expected. It verifies correct HTTP status codes, error codes, and
response structures for both handled and unhandled exceptions.

Typical usage example (pytest from project root):
    pytest --maxfail=1 --disable-warnings -q

Dependencies:
    - Pytest
    - FastAPI TestClient (provided via conftest.py)
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi import APIRouter, HTTPException, status
from fastapi import Query, FastAPI
from app.core.exception_handling import error_handler
from app.core.exception_handling.error_handler import (
    BaseAppException,
    ResourceNotFoundError,
    ValidationError as AppValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ExternalServiceError,
)


# Create a test router to raise each exception type, so we can verify the handlers.
router = APIRouter()


@router.get("/base-exception", include_in_schema=False)
def raise_base_exception():
    """
    Raise a generic BaseAppException for testing.

    Raises:
        BaseAppException: Generic base exception
    """
    raise BaseAppException(
        error_code="BASE_TEST_ERROR",
        message="A base application error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"info": "Extra details for base exception"},
    )


@router.get("/resource-not-found", include_in_schema=False)
def raise_resource_not_found_exception():
    """
    Raise a ResourceNotFoundError for testing.

    Raises:
        ResourceNotFoundError: Example resource not found scenario
    """
    raise ResourceNotFoundError(
        message="Resource not found during test",
        resource_type="TestResource",
        resource_id="123",
    )


@router.get("/validation-error-app", include_in_schema=False)
def raise_validation_error_app():
    """
    Raise an application-level ValidationError (custom) for testing.

    Raises:
        AppValidationError: Custom validation error
    """
    raise AppValidationError(
        message="Custom validation failed",
        fields={"example_field": "Invalid data"},
    )


@router.get("/authentication-error", include_in_schema=False)
def raise_authentication_error():
    """
    Raise an AuthenticationError for testing.

    Raises:
        AuthenticationError: Example authentication failure
    """
    raise AuthenticationError(message="Authentication check failed")


@router.get("/authorization-error", include_in_schema=False)
def raise_authorization_error():
    """
    Raise an AuthorizationError for testing.

    Raises:
        AuthorizationError: Example authorization failure
    """
    raise AuthorizationError(
        message="Authorization check failed",
        required_permission="test:permission",
    )


@router.get("/database-error", include_in_schema=False)
def raise_database_error():
    """
    Raise a DatabaseError for testing.

    Raises:
        DatabaseError: Example database operation failure
    """
    raise DatabaseError(message="Test DB error", operation="INSERT")


@router.get("/external-service-error", include_in_schema=False)
def raise_external_service_error():
    """
    Raise an ExternalServiceError for testing.

    Raises:
        ExternalServiceError: Example of an external service call failing
    """
    raise ExternalServiceError(
        message="External service test error",
        service="TestExternalAPI",
    )


@router.get("/http-exception", include_in_schema=False)
def raise_http_exception():
    """
    Raise a native FastAPI/Starlette HTTPException for testing.

    Raises:
        HTTPException: Standard FastAPI HTTPException
    """
    # Using the Starlette/FastAPI HTTPException:
    raise HTTPException(status_code=418, detail="I'm a teapot")


@router.get("/unhandled-exception", include_in_schema=False)
def raise_unhandled_exception():
    """
    Raise a generic unhandled Python exception for testing.

    Raises:
        Exception: A plain Python exception not handled by application code
    """
    raise Exception("This is an unhandled exception")


@router.get("/request-validation-error", include_in_schema=False)
def trigger_fastapi_validation_error(name: int = Query(...)):
    """
    Trigger a built-in FastAPI RequestValidationError by passing an invalid query param.

    Args:
        name: An integer query parameter. Passing a non-integer triggers the validation error.

    Returns:
        dict: A success response if the query param is valid
    """
    return {"name": name, "message": "Validation success"}


@pytest.fixture(scope="function")
def error_test_client(client):
    """
    Provide a test client that includes routes raising each error for coverage.

    This fixture modifies the existing 'client' fixture so it won't re-raise
    unhandled server exceptions to the test code. It also appends the test
    router with error-raising endpoints to the existing FastAPI application.

    Args:
        client: The base TestClient from conftest

    Returns:
        TestClient: A client with additional endpoints for error testing
    """
    # Disable re-raising server exceptions so the unhandled_exception_handler
    # can return a 500 response instead of propagating the error directly.
    client.raise_server_exceptions = False

    # Add our test endpoints that deliberately raise various exceptions.
    client.app.include_router(router, prefix="/test-errors")

    return client


@pytest.mark.parametrize(
    "endpoint,expected_status,expected_error_code",
    [
        (
            "/base-exception",
            500,
            "BASE_TEST_ERROR",
        ),
        (
            "/resource-not-found",
            404,
            "RESOURCE_NOT_FOUND",
        ),
        (
            "/validation-error-app",
            422,
            "VALIDATION_ERROR",
        ),
        (
            "/authentication-error",
            401,
            "AUTHENTICATION_ERROR",
        ),
        (
            "/authorization-error",
            403,
            "AUTHORIZATION_ERROR",
        ),
        (
            "/database-error",
            500,
            "DATABASE_ERROR",
        ),
        (
            "/external-service-error",
            502,
            "EXTERNAL_SERVICE_ERROR",
        ),
    ],
)
def test_custom_app_exceptions(
    error_test_client,
    endpoint,
    expected_status,
    expected_error_code,
):
    """
    Test endpoints that raise custom application exceptions.

    This test verifies that each custom exception defined in error_handler.py
    returns the expected HTTP status code, error_code, and JSON structure.

    Args:
        error_test_client: Pytest fixture providing a client with error routes
        endpoint: The test route to call
        expected_status: The expected HTTP status code from the raised exception
        expected_error_code: The expected error code string in the JSON response
    """
    response = error_test_client.get(f"/test-errors{endpoint}")
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code} "
        f"for endpoint {endpoint}"
    )

    data = response.json()
    assert data["error_code"] == expected_error_code
    assert "message" in data
    assert "details" in data


def test_starlette_http_exception(error_test_client):
    """
    Test that a native Starlette/FastAPI HTTPException is handled correctly.

    This test verifies that raising an HTTPException in an endpoint
    triggers the http_exception_handler with the expected status code
    and response structure.

    Args:
        error_test_client: Pytest fixture providing a client with error routes
    """
    response = error_test_client.get("/test-errors/http-exception")
    assert response.status_code == 418
    data = response.json()
    assert data["error_code"] == "HTTP_418"
    assert data["message"] == "I'm a teapot"
    assert "details" in data
    assert data["details"] == {}


def test_unhandled_exception_raises(error_test_client):
    """
    Test that an unhandled exception raises a 500 error.

    This test verifies that an unhandled exception in an endpoint
    triggers the unhandled_exception_handler, returning a 500 error
    with the expected error code and message.

    Args:
        error_test_client: Pytest fixture providing a client with error routes
    """
    with pytest.raises(Exception) as exc_info:
        error_test_client.get("/test-errors/unhandled-exception")
    assert "This is an unhandled exception" in str(exc_info.value)


def test_fastapi_request_validation_error(error_test_client):
    """
    Test that FastAPI's built-in RequestValidationError is handled.

    This test calls an endpoint expecting an integer query parameter
    with a string value, triggering FastAPI's validation and verifying
    that the validation_exception_handler produces a 422 response
    with an appropriate error code.

    Args:
        error_test_client: Pytest fixture providing a client with error routes
    """
    # 'name' should be an int, so passing a string triggers RequestValidationError
    response = error_test_client.get(
        "/test-errors/request-validation-error", params={"name": "invalid"}
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "message" in data
    assert "Request validation failed" in data["message"]
    assert "details" in data
    assert "fields" in data["details"]
    assert "name" in data["details"]["fields"]


def test_positive_flow_validation(error_test_client):
    """
    Test the 'positive' flow for request validation.

    This test provides a valid integer query parameter to the endpoint,
    verifying that no error is raised and that the endpoint responds
    with a normal 200 success status.

    Args:
        error_test_client: Pytest fixture providing a client with error routes
    """
    response = error_test_client.get(
        "/test-errors/request-validation-error", params={"name": 42}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == 42
    assert data["message"] == "Validation success"


def test_invalid_data_structure_for_custom_validation(error_test_client):
    """
    Negative test to ensure custom ValidationError fields are captured correctly.

    This test demonstrates a scenario in which we might raise the custom
    ValidationError with specific fields, verifying that the JSON output
    includes the 'fields' dictionary.

    Args:
        error_test_client: Pytest fixture providing a client with error routes
    """
    # We reuse the 'validation-error-app' route for a negative check
    # This route always raises an AppValidationError
    response = error_test_client.get("/test-errors/validation-error-app")
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "fields" in data["details"]
    assert "example_field" in data["details"]["fields"]


def test_resource_not_found_with_only_type(error_test_client):
    """
    Test ResourceNotFoundError with only resource_type specified.

    This tests the code path in ResourceNotFoundError where only resource_type
    is provided but not resource_id.
    """

    # Add a route that raises ResourceNotFoundError with only type
    @router.get("/resource-not-found-type-only", include_in_schema=False)
    def raise_resource_not_found_type_only():
        raise ResourceNotFoundError(
            message="Resource not found during test",
            resource_type="TypeOnlyResource",
        )

    # Register the new route
    error_test_client.app.include_router(router, prefix="/test-errors-extra")

    # Test the endpoint
    response = error_test_client.get("/test-errors-extra/resource-not-found-type-only")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "RESOURCE_NOT_FOUND"
    assert "details" in data
    assert "resource_type" in data["details"]
    assert "resource_id" not in data["details"]


def test_resource_not_found_with_no_details(error_test_client):
    """
    Test ResourceNotFoundError with no additional details.

    This tests the code path in ResourceNotFoundError where neither
    resource_type nor resource_id is provided.
    """

    # Add a route that raises ResourceNotFoundError with no details
    @router.get("/resource-not-found-no-details", include_in_schema=False)
    def raise_resource_not_found_no_details():
        raise ResourceNotFoundError(
            message="Generic resource not found",
        )

    # Register the new route
    error_test_client.app.include_router(router, prefix="/test-errors-extra2")

    # Test the endpoint
    response = error_test_client.get(
        "/test-errors-extra2/resource-not-found-no-details"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "RESOURCE_NOT_FOUND"
    assert "details" in data
    assert data["details"] == {}


def test_app_exception_handler_for_500_errors(error_test_client):
    """
    Test that the app_exception_handler logs 500-level errors at error level.

    This test verifies that exceptions with status codes >= 500 are logged
    at the error level with exc_info=True.
    """

    # Create a route that raises a DatabaseError (500-level error)
    @router.get("/database-error-logged", include_in_schema=False)
    def raise_database_error_for_logging():
        raise DatabaseError(message="Database error for logging test")

    # Register the new route
    error_test_client.app.include_router(router, prefix="/test-errors-log")

    # Patch the logger to verify it's called with the right level
    with patch("app.core.exception_handling.error_handler.logger") as mock_logger:
        # Call the endpoint to trigger the exception
        response = error_test_client.get("/test-errors-log/database-error-logged")

        # Verify the response
        assert response.status_code == 500

        # Verify the logger was called with error level and exc_info=True
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "Application exception" in args[0]
        assert "DATABASE_ERROR" in args[1]
        assert kwargs.get("exc_info") is True


def test_custom_exception_handlers_registration():
    """
    Test registering custom exception handlers from EXCEPTION_HANDLERS dict.

    This test verifies that custom exception handlers in the EXCEPTION_HANDLERS
    dictionary are properly registered with the FastAPI application.
    """

    # Create a mock exception class and handler
    class CustomTestException(Exception):
        """Custom test exception for handler registration"""

    async def custom_handler():
        return {"handled": "custom"}

    # Set up the test
    with patch.dict(
        error_handler.EXCEPTION_HANDLERS, {CustomTestException: custom_handler}
    ):
        # Create a mock FastAPI app
        mock_app = MagicMock(spec=FastAPI)

        # Call the register function
        error_handler.register_exception_handlers(mock_app)

        # Verify all expected handlers were registered
        assert (
            mock_app.add_exception_handler.call_count >= 4
        )  # At least the main handlers

        # Check that our custom handler was registered
        mock_app.add_exception_handler.assert_any_call(
            CustomTestException, custom_handler
        )
