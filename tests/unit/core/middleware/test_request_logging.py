# pylint: disable=unused-argument, too-many-arguments, too-many-positional-arguments
"""
Unit tests for the request logging middleware.

This module contains tests for the RequestLoggingMiddleware and the
add_request_logging_middleware function, verifying that HTTP requests 
and responses are properly logged with timing information, status codes, 
and request IDs.
"""

from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi import FastAPI, Request, Response

from app.core.middleware.request_logging import (
    RequestLoggingMiddleware,
    add_request_logging_middleware,
)


class TestRequestLoggingMiddleware:
    """Tests for the RequestLoggingMiddleware class."""

    @pytest.fixture
    def mock_logger(self):
        """
        Create a mock logger for testing.

        Returns:
            MagicMock: A mock logger object with common methods
        """
        with patch("app.core.middleware.request_logging.logger") as mock_logger:
            yield mock_logger

    @pytest.fixture
    def mock_uuid(self):
        """
        Create a mock UUID generator for testing.

        Returns:
            MagicMock: A mock uuid4 function that returns a predictable value
        """
        with patch("app.core.middleware.request_logging.uuid.uuid4") as mock_uuid4:
            mock_uuid4.return_value = "test-request-id"
            yield mock_uuid4

    @pytest.fixture
    def mock_time(self):
        """
        Create a mock time function for testing.

        Returns:
            MagicMock: A mock time.time function that returns predictable values
        """
        with patch("app.core.middleware.request_logging.time.time") as mock_time:
            # Return start time, then end time (1.5 seconds later)
            mock_time.side_effect = [100.0, 101.5]
            yield mock_time

    @pytest.fixture
    def middleware(self):
        """
        Create a RequestLoggingMiddleware instance for testing.

        Returns:
            RequestLoggingMiddleware: A middleware instance
        """
        return RequestLoggingMiddleware(MagicMock())

    @pytest.fixture
    def mock_request(self):
        """
        Create a mock Request object for testing.

        Returns:
            MagicMock: A mock Request object with the necessary attributes
        """
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/test"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.client.port = 8000
        mock_request.state = MagicMock()
        return mock_request

    @pytest.fixture
    def mock_response(self):
        """
        Create a mock Response object for testing.

        Returns:
            MagicMock: A mock Response object with the necessary attributes
        """
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        return mock_response

    @pytest.fixture
    def test_setup(
        self, mock_request, mock_response, mock_logger, mock_uuid, mock_time
    ):
        """
        Combine multiple fixtures to reduce argument count in test methods.

        Returns:
            dict: A dictionary containing all the fixtures
        """
        return {
            "request": mock_request,
            "response": mock_response,
            "logger": mock_logger,
        }

    @pytest.mark.asyncio(scope="session")
    async def test_dispatch_successful_request(self, middleware, test_setup):
        """
        Test that the middleware correctly logs successful requests.

        This test verifies that the middleware logs the start and completion
        of requests, adds request IDs to headers, and includes timing information.

        Args:
            middleware: RequestLoggingMiddleware instance
            test_setup: Combined test fixtures
        """
        mock_request = test_setup["request"]
        mock_response = test_setup["response"]
        mock_logger = test_setup["logger"]

        # Mock the call_next function to return our mock response
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response

        # Call the dispatch method
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Verify the request ID was set on the request state
        assert mock_request.state.request_id == "test-request-id"

        # Verify the response has the request ID header
        assert response.headers["X-Request-ID"] == "test-request-id"

        # Verify the logger was called with the expected messages
        assert mock_logger.info.call_count == 2

        # Check first log call (request start)
        mock_logger.info.assert_any_call(
            "Request started: %s %s from %s [request_id=%s]",
            "GET",
            "http://test.com/api/test",
            "127.0.0.1:8000",
            "test-request-id",
        )

        # Check second log call (request completion)
        mock_logger.info.assert_any_call(
            "Request completed: %s %s [status=%s] [time=%ss] [request_id=%s]",
            "GET",
            "http://test.com/api/test",
            200,
            "1.5000",
            "test-request-id",
        )

    @pytest.mark.asyncio
    async def test_dispatch_failed_request(self, middleware, test_setup):
        """
        Test that the middleware correctly logs failed requests.

        This test verifies that the middleware logs exceptions that occur
        during request processing, including timing information.

        Args:
            middleware: RequestLoggingMiddleware instance
            test_setup: Combined test fixtures
        """
        mock_request = test_setup["request"]
        mock_logger = test_setup["logger"]

        # Mock the call_next function to raise an exception
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = ValueError("Test error")

        # Call the dispatch method, expecting an exception
        with pytest.raises(ValueError) as excinfo:
            await middleware.dispatch(mock_request, mock_call_next)

        # Verify the exception is the one we raised
        assert str(excinfo.value) == "Test error"

        # Verify the request ID was set on the request state
        assert mock_request.state.request_id == "test-request-id"

        # Verify the logger was called with the expected messages
        assert mock_logger.info.call_count == 1
        assert mock_logger.error.call_count == 1

        # Check info log call (request start)
        mock_logger.info.assert_called_once_with(
            "Request started: %s %s from %s [request_id=%s]",
            "GET",
            "http://test.com/api/test",
            "127.0.0.1:8000",
            "test-request-id",
        )

        # Check error log call (request failure)
        mock_logger.error.assert_called_once_with(
            "Request failed: %s %s [error=%s] [time=%ss] [request_id=%s]",
            "GET",
            "http://test.com/api/test",
            "Test error",
            "1.5000",
            "test-request-id",
            exc_info=True,
        )

    @pytest.mark.asyncio
    async def test_dispatch_with_no_client(self, middleware, test_setup):
        """
        Test that the middleware handles requests with no client information.

        This test verifies that the middleware correctly handles cases where
        the request has no client information, using "unknown" as a fallback.

        Args:
            middleware: RequestLoggingMiddleware instance
            test_setup: Combined test fixtures
        """
        mock_request = test_setup["request"]
        mock_response = test_setup["response"]
        mock_logger = test_setup["logger"]

        # Set client to None to test the fallback
        mock_request.client = None

        # Mock the call_next function to return our mock response
        mock_call_next = AsyncMock()
        mock_call_next.return_value = mock_response

        # Call the dispatch method
        await middleware.dispatch(mock_request, mock_call_next)

        # Verify the first log call uses "unknown" for client
        mock_logger.info.assert_any_call(
            "Request started: %s %s from %s [request_id=%s]",
            "GET",
            "http://test.com/api/test",
            "unknown",
            "test-request-id",
        )


class TestAddRequestLoggingMiddleware:
    """Tests for the add_request_logging_middleware function."""

    def test_add_middleware_to_app(self):
        """
        Test that the function correctly adds the middleware to a FastAPI app.

        This test verifies that the add_request_logging_middleware function
        correctly adds the RequestLoggingMiddleware to a FastAPI application.
        """
        # Create a FastAPI app
        app = FastAPI()

        # Mock the add_middleware method
        app.add_middleware = MagicMock()

        # Call the function
        add_request_logging_middleware(app)

        # Verify add_middleware was called with RequestLoggingMiddleware
        app.add_middleware.assert_called_once_with(RequestLoggingMiddleware)


class TestIntegration:
    """Integration tests for request logging middleware."""

    def test_middleware_integration(self, client):
        """
        Test that the middleware is correctly integrated with the application.

        This test verifies that requests sent through the TestClient
        have the expected request ID header in the response.

        Args:
            client: TestClient fixture from conftest.py
        """
        with patch("app.core.middleware.request_logging.uuid.uuid4") as mock_uuid4:
            mock_uuid4.return_value = "test-integration-id"

            # Send a request to the application
            response = client.get("/api/v1/system/health/health_check")

            # Verify the response has the request ID header
            assert response.headers.get("X-Request-ID") == "test-integration-id"
