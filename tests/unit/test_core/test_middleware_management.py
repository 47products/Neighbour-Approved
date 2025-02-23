"""
Unit tests for the middleware_management module in the Neighbour Approved application.

This module tests:
- BaseMiddleware: including initialization, startup/shutdown, process, and execute_pipeline
- MiddlewareRegistry: registration, ordering, startup/shutdown, middleware chain execution,
  and integration with FastAPI

Typical usage example:
    pytest tests/unit/test_middleware_management.py

Dependencies:
    - pytest
    - pytest-mock or unittest.mock
    - fastapi, starlette, or relevant mocking for Request, Response
    - The middleware_management module under test
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request, Response
from starlette.responses import Response as StarletteResponse
from starlette.middleware.base import RequestResponseEndpoint
from typing import Any, Dict

from app.core.middleware_management import (
    MiddlewarePriority,
    MiddlewareConfig,
    BaseMiddleware,
    MiddlewareRegistry,
)


# A concrete subclass of BaseMiddleware for testing
class TestMiddleware(BaseMiddleware[MiddlewareConfig]):
    async def process(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        A trivial process method that calls the next step and returns the response.
        """
        return await call_next(request)


@pytest.fixture
def request_mock() -> Request:
    """
    Returns a mock of FastAPI Request.
    Could also use Request(scope=...) if needed, but we keep it simple here.
    """
    return MagicMock(spec=Request)


@pytest.fixture
def call_next_mock() -> RequestResponseEndpoint:
    """Returns a mock for the 'call_next' function in starlette BaseHTTPMiddleware."""

    async def _dummy_call_next(request: Request) -> Response:
        return StarletteResponse("next called", status_code=200)

    return _dummy_call_next


# ---------------------------------------------------------------------------
# BaseMiddleware tests
# ---------------------------------------------------------------------------


async def test_base_middleware_init():
    """
    Test that BaseMiddleware __init__ sets config, dependencies, and logs a bound logger.
    """
    config = {"enabled": True, "log_level": "DEBUG", "skip_paths": ["/health"]}
    middleware = TestMiddleware(app=None, config=config, dependencies=[])
    assert middleware.config.enabled is True
    assert middleware.config.log_level == "DEBUG"
    assert middleware.config.skip_paths == ["/health"]
    assert middleware.dependencies == []
    # The logger is private, but we can check it's not None
    assert middleware._logger is not None


async def test_base_middleware_startup_shutdown(caplog):
    """
    Test startup() and shutdown() log messages.
    """
    caplog.set_level("DEBUG", logger="app.core.middleware_management")
    middleware = TestMiddleware(app=None)
    await middleware.startup()
    await middleware.shutdown()

    # Check logs in caplog
    startup_logs = [
        r.message for r in caplog.records if "middleware_startup" in r.message
    ]
    shutdown_logs = [
        r.message for r in caplog.records if "middleware_shutdown" in r.message
    ]
    assert len(startup_logs) == 1
    assert len(shutdown_logs) == 1


async def test_base_middleware_process_not_implemented():
    """
    If we use BaseMiddleware directly, process() should raise NotImplementedError,
    but in the derived class we override it. Let's test the base class itself.
    """
    from app.core.middleware_management import BaseMiddleware

    class RawBaseMiddleware(BaseMiddleware[MiddlewareConfig]):
        pass  # no override

    middleware = RawBaseMiddleware(app=None)
    with pytest.raises(NotImplementedError):
        await middleware.process(MagicMock(), MagicMock())


async def test_base_middleware_execute_pipeline_no_more_middlewares(
    request_mock, call_next_mock
):
    """
    Test execute_pipeline scenario where pipeline_position == len(middleware_chain).
    We expect it to just call call_next(request).
    """
    middleware = TestMiddleware(app=None)
    # pipeline_position = 0, but middleware_chain is empty => 0 == 0 => call call_next
    response = await middleware.execute_pipeline(request_mock, call_next_mock, 0, [])
    assert response.status_code == 200
    assert response.body == b"next called"


async def test_base_middleware_execute_pipeline_with_next_middleware(
    request_mock, call_next_mock, caplog
):
    """
    Test that execute_pipeline calls the next middleware's process() method
    and logs the execution time. We'll use 'TestMiddleware' for the next link too.
    """
    caplog.set_level("DEBUG", logger="app.core.middleware_management")
    first_mw = TestMiddleware(app=None)
    second_mw = TestMiddleware(app=None)
    mw_chain = [
        second_mw
    ]  # We'll run first_mw's execute_pipeline => next_mw = second_mw

    # Spy on second_mw.process
    with patch.object(second_mw, "process", autospec=True) as mock_process:

        async def _fake_process(request, chain_next):
            return await chain_next(request)

        mock_process.side_effect = _fake_process

        response = await first_mw.execute_pipeline(
            request_mock, call_next_mock, 0, mw_chain
        )
        assert response.status_code == 200

    # The second middleware's process method should have been called exactly once
    mock_process.assert_called_once()
    # We also expect logs about "middleware_execution"
    exec_logs = [r for r in caplog.records if "middleware_execution" in r.message]
    assert len(exec_logs) == 1


async def test_base_middleware_execute_pipeline_error_in_process(
    request_mock, call_next_mock, caplog
):
    """
    Test that if the next middleware process raises an exception,
    it's logged as 'middleware_execution_failed' and re-raised.
    """
    first_mw = TestMiddleware(app=None)

    class FailingMiddleware(BaseMiddleware[MiddlewareConfig]):
        async def process(self, req, next_):
            raise RuntimeError("simulated process error")

    mw_chain = [FailingMiddleware(app=None)]
    with pytest.raises(RuntimeError, match="simulated process error"):
        await first_mw.execute_pipeline(request_mock, call_next_mock, 0, mw_chain)

    error_logs = [
        r for r in caplog.records if "middleware_execution_failed" in r.message
    ]
    assert len(error_logs) == 1


async def test_base_middleware_execute_pipeline_error_caught_outside(
    request_mock, call_next_mock, caplog
):
    """
    Test that if an error occurs outside the next_middleware.process() call,
    it logs 'pipeline_execution_failed'.
    We'll force an error after the 'if pipeline_position == len(middleware_chain)' line.
    """
    mw = TestMiddleware(app=None)
    # We'll create a scenario: pipeline_position is 0, but we pass negative len(...), forcing an error?
    # Or we can directly patch the code to raise an exception in the outer try block.
    # We'll do a simpler approach: monkeypatch the 'process' method to raise at the outer level.

    with patch.object(mw, "process", side_effect=Exception("outer pipeline failure")):
        with pytest.raises(Exception, match="outer pipeline failure"):
            # Passing a chain with just 'mw' itself => might be cyclical, but it's enough
            await mw.execute_pipeline(request_mock, call_next_mock, 0, [mw])

    pipeline_failed_logs = [
        r for r in caplog.records if "pipeline_execution_failed" in r.message
    ]
    assert len(pipeline_failed_logs) == 1


# ---------------------------------------------------------------------------
# MiddlewareRegistry tests
# ---------------------------------------------------------------------------


def test_middleware_registry_register():
    """
    Test that register() stores the middleware class with config and priority,
    logs the registration, and raises ValueError if re-registered.
    """
    registry = MiddlewareRegistry()
    config = {"enabled": False}
    registry.register(TestMiddleware, priority=MiddlewarePriority.FIRST, config=config)

    # Register again => ValueError
    with pytest.raises(ValueError, match="already registered"):
        registry.register(TestMiddleware, priority=MiddlewarePriority.NORMAL)


def test_middleware_registry_get_ordered_middlewares(caplog):
    """
    Test that get_ordered_middlewares sorts by priority, then by class name.
    """
    registry = MiddlewareRegistry()

    class AMiddleware(TestMiddleware):
        pass

    class BMiddleware(TestMiddleware):
        pass

    registry.register(BMiddleware, priority=MiddlewarePriority.NORMAL)
    registry.register(AMiddleware, priority=MiddlewarePriority.EARLY)

    # The result should have AMiddleware first (priority=2 => EARLY) before BMiddleware
    ordered = registry.get_ordered_middlewares()
    assert ordered == [AMiddleware, BMiddleware]


@pytest.mark.asyncio
async def test_middleware_registry_startup_middlewares(caplog):
    """
    Test that startup_middlewares() instantiates each middleware with its config,
    calls .startup(), and logs 'middleware_started'.
    """
    caplog.set_level("DEBUG", logger="app.core.middleware_management")
    registry = MiddlewareRegistry()
    reg_config = {"log_level": "DEBUG"}

    class StartupMiddleware(TestMiddleware):
        pass

    registry.register(StartupMiddleware, config=reg_config)

    await registry.startup_middlewares()

    # We'll see logs for 'middleware_startup' and 'middleware_started'
    started_log = [r for r in caplog.records if "middleware_started" in r.message]
    assert len(started_log) == 1
    # Optionally, we can check 'middleware_startup' logs too:
    startup_debug_log = [r for r in caplog.records if "middleware_startup" in r.message]
    assert len(startup_debug_log) == 1


@pytest.mark.asyncio
async def test_middleware_registry_shutdown_middlewares(caplog):
    """
    Test that shutdown_middlewares() calls each middleware in reverse order,
    calling .shutdown() and logging 'middleware_shutdown'.
    """
    registry = MiddlewareRegistry()

    class M1(TestMiddleware):
        pass

    class M2(TestMiddleware):
        pass

    registry.register(M1, priority=MiddlewarePriority.FIRST)
    registry.register(M2, priority=MiddlewarePriority.NORMAL)

    # Start them first, for logs consistency
    await registry.startup_middlewares()
    caplog.clear()

    await registry.shutdown_middlewares()

    # We'll see logs for 'middleware_shutdown' and 'middleware_shutdown'
    shutdown_log = [r for r in caplog.records if "middleware_shutdown" in r.message]
    # We have 2 middlewares, M2 is last in order => shuts down first => so logs show M2, M1
    assert len(shutdown_log) == 2
    # Optionally check the ordering
    assert "M2" in shutdown_log[0].message
    assert "M1" in shutdown_log[1].message


@pytest.mark.asyncio
async def test_middleware_registry_execute_middleware_chain_empty(call_next_mock):
    """
    If no middlewares are registered, execute_middleware_chain() calls call_next directly.
    """
    registry = MiddlewareRegistry()
    # request mock not needed for verifying the response alone
    request_mock = MagicMock(spec=Request)

    response = await registry.execute_middleware_chain(request_mock, call_next_mock)
    assert response.status_code == 200
    assert response.body == b"next called"


@pytest.mark.asyncio
async def test_middleware_registry_execute_middleware_chain_single_mw(
    call_next_mock, caplog
):
    """
    If one middleware is registered, execute_middleware_chain() uses that middleware's
    execute_pipeline() to process the request.
    """
    caplog.set_level("DEBUG", logger="app.core.middleware_management")
    registry = MiddlewareRegistry()
    registry.register(TestMiddleware)

    request_mock = MagicMock(spec=Request)
    response = await registry.execute_middleware_chain(request_mock, call_next_mock)
    assert response.status_code == 200

    # We can look for logs about 'middleware_execution' from the base class
    exec_logs = [r for r in caplog.records if "middleware_execution" in r.message]
    assert len(exec_logs) == 1


def test_middleware_registry_apply_middlewares(mocker):
    """
    Test that apply_middlewares() attaches an HTTP-level middleware to the FastAPI app.
    """
    registry = MiddlewareRegistry()
    mock_app = MagicMock(spec=FastAPI)

    registry.apply_middlewares(mock_app)
    # Check if app.middleware("http") was invoked, or if we can confirm
    # the 'middleware_pipeline_configured' log. We can also confirm that
    # mock_app.middleware was called with "http" once.
    # But FastAPI mocking is a bit tricky. Let's see:
    # There's no direct call to app.middleware(...) returning anything,
    # but we can check that the function was indeed bound.
    # Alternatively, we can check caplog for "middleware_pipeline_configured".
    # We'll do that with the logger.

    # The actual decorator pattern means we can't easily check app.middleware calls
    # unless we do deeper mocking. We'll rely on the log message:
    # "middleware_pipeline_configured"
    # Let's do it with a caplog or a spy:

    # We can check the log using the registry's logger.
    # For that, we need caplog, or patch the registry's _logger

    # We'll patch the registry's logger to see if it logs "middleware_pipeline_configured".
    with patch.object(registry._logger, "info") as mock_log:
        registry.apply_middlewares(mock_app)
        # We expect an "middleware_pipeline_configured" info log
        mock_log.assert_called_with("middleware_pipeline_configured")
