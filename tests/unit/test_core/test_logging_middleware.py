"""
Unit tests for logging_middleware.py in the Neighbour Approved application.

Tests cover:
- RequestLoggingMiddleware: verifying skip_paths, request/response logs, error handling,
  and request ID insertion.
- setup_logging_middleware: verifying registration with the MiddlewareRegistry based on settings.

Typical usage example:
    pytest tests/unit/test_logging_middleware.py

Dependencies:
    - pytest, pytest-asyncio
    - fastapi, starlette
    - app.core.logging_middleware
    - app.core.middleware_management
    - app.core.config
    - structlog
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch
from starlette.responses import Response
from starlette.requests import Request
from fastapi import FastAPI
from app.core.config import Settings
from app.core.logging_middleware import (
    RequestLoggingMiddleware,
    RequestLoggingConfig,
    setup_logging_middleware,
)
from app.core.middleware_management import MiddlewareRegistry, MiddlewarePriority
from app.core.logging_configuration import setup_logging  # if you have one


@pytest.fixture
def call_next_mock():
    """Simulate the 'call_next' function that the middleware will call."""

    async def _dummy_call_next(request: Request) -> Response:
        return Response(content=b"OK", status_code=200)

    return _dummy_call_next


@pytest.fixture
def request_mock():
    """Create a mock Starlette/FastAPI Request object."""
    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.headers = {"user-agent": "test-agent"}
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.url.path = "/some/path"
    mock_request.query_params = "test=query"
    return mock_request


@pytest.mark.asyncio
async def test_request_logging_middleware_skip_paths(
    request_mock, call_next_mock, caplog
):
    """
    If the request path is in skip_paths, the middleware calls next without logging.
    """
    caplog.set_level("DEBUG", logger="app.core.logging_middleware")

    config = {
        "skip_paths": ["/health"],
        "enabled": True,
    }
    # Make the request.path one of the skip paths
    request_mock.url.path = "/health"

    mw = RequestLoggingMiddleware(app=None, config=config)

    response = await mw.dispatch(request_mock, call_next_mock)
    assert response.status_code == 200

    # No 'http_request_started' or 'http_request_completed' logs should exist
    started_logs = [r for r in caplog.records if "http_request_started" in r.message]
    completed_logs = [
        r for r in caplog.records if "http_request_completed" in r.message
    ]
    assert not started_logs
    assert not completed_logs


@pytest.mark.asyncio
async def test_request_logging_middleware_success(request_mock, call_next_mock, caplog):
    """
    Test that a normal request logs start and completion, sets X-Request-ID, etc.
    """
    caplog.set_level("DEBUG", logger="app.core.logging_middleware")

    # No skip paths
    config = {"skip_paths": []}
    mw = RequestLoggingMiddleware(app=None, config=config)

    response = await mw.dispatch(request_mock, call_next_mock)
    assert response.status_code == 200
    # Confirm we got logs: 'http_request_started' and 'http_request_completed'
    started_logs = [r for r in caplog.records if "http_request_started" in r.message]
    completed_logs = [
        r for r in caplog.records if "http_request_completed" in r.message
    ]
    assert len(started_logs) == 1
    assert len(completed_logs) == 1

    # Check that 'X-Request-ID' is in the response
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_request_logging_middleware_exception(request_mock, caplog):
    """
    If call_next raises an exception, the middleware logs http_request_failed and re-raises.
    """
    caplog.set_level("DEBUG", logger="app.core.logging_middleware")

    async def failing_call_next(req: Request) -> Response:
        raise RuntimeError("Simulated error")

    mw = RequestLoggingMiddleware(app=None, config={})

    with pytest.raises(RuntimeError, match="Simulated error"):
        await mw.dispatch(request_mock, failing_call_next)

    # We expect 'http_request_started' and 'http_request_failed'
    started_logs = [r for r in caplog.records if "http_request_started" in r.message]
    failed_logs = [r for r in caplog.records if "http_request_failed" in r.message]
    assert len(started_logs) == 1
    assert len(failed_logs) == 1


@pytest.mark.asyncio
async def test_request_logging_middleware_json_log_format(
    request_mock, call_next_mock, caplog, mocker
):
    """
    If LOG_FORMAT == 'json', the code re-binds a new logger with json=True.
    We can confirm that scenario by mocking get_settings() to return LOG_FORMAT=json.
    """
    caplog.set_level("DEBUG", logger="app.core.logging_middleware")

    # Patch get_settings to force LOG_FORMAT=json
    mock_settings = mocker.MagicMock()
    mock_settings.LOG_FORMAT = "json"
    mock_settings.ENABLE_REQUEST_LOGGING = True

    mocker.patch("app.core.logging_middleware.get_settings", return_value=mock_settings)

    mw = RequestLoggingMiddleware(app=None, config={})

    response = await mw.dispatch(request_mock, call_next_mock)
    assert response.status_code == 200

    # Because we used 'json=True', the logs might differ,
    # but we can still confirm the normal messages were triggered
    started_logs = [r for r in caplog.records if "http_request_started" in r.message]
    assert len(started_logs) == 1


def test_setup_logging_middleware_enable(mocker):
    """
    If ENABLE_REQUEST_LOGGING is True, setup_logging_middleware registers
    RequestLoggingMiddleware on the registry at priority FIRST.
    """
    # Mock get_settings to say logging is enabled
    mock_settings = mocker.MagicMock()
    mock_settings.ENABLE_REQUEST_LOGGING = True
    mocker.patch("app.core.logging_middleware.get_settings", return_value=mock_settings)

    # We'll also mock the registry so we see if 'register' is called
    registry_mock = mocker.patch(
        "app.core.logging_middleware.MiddlewareRegistry", autospec=True
    )
    registry_instance = registry_mock.return_value

    app = FastAPI()
    from app.core.logging_middleware import setup_logging_middleware

    setup_logging_middleware(app)

    # We expect a single register call for RequestLoggingMiddleware
    registry_instance.register.assert_called_once()
    args, kwargs = registry_instance.register.call_args
    assert args[0].__name__ == "RequestLoggingMiddleware"
    assert kwargs["priority"] == 1  # MiddlewarePriority.FIRST
    assert kwargs["config"] == {"enable_request_logging": True}

    # Then apply_middlewares
    registry_instance.apply_middlewares.assert_called_once_with(app)


def test_setup_logging_middleware_disable(mocker):
    """
    If ENABLE_REQUEST_LOGGING is False, no middleware is registered.
    """
    mock_settings = mocker.MagicMock()
    mock_settings.ENABLE_REQUEST_LOGGING = False
    mocker.patch("app.core.logging_middleware.get_settings", return_value=mock_settings)

    registry_mock = mocker.patch(
        "app.core.logging_middleware.MiddlewareRegistry", autospec=True
    )
    registry_instance = registry_mock.return_value

    app = FastAPI()
    from app.core.logging_middleware import setup_logging_middleware

    setup_logging_middleware(app)

    registry_instance.register.assert_not_called()
    registry_instance.apply_middlewares.assert_called_once_with(app)
