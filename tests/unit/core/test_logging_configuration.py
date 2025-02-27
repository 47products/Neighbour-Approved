"""
Unit tests for logging_configuration.py in the Neighbour Approved application.

Tests cover:
- configure_stdlib_logging: verifying directory creation and dictConfig usage
- setup_structlog: verifying structlog.configure calls with dev vs. production settings
- AppLogger: verifying context binding, clearing, and log-level methods
- setup_logging: ensuring both stdlib and structlog are configured
- get_logger: returning a valid AppLogger

Typical usage example:
    pytest tests/unit/test_logging_configuration.py

Dependencies:
    - pytest
    - pytest-mock or unittest.mock
    - The logging_configuration module under test
"""

from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, call
from structlog.processors import JSONRenderer
from app.core.logging_configuration import (
    configure_stdlib_logging,
    setup_structlog,
    AppLogger,
    setup_logging,
    get_logger,
    settings,  # original Settings instance
)


def test_configure_stdlib_logging(mocker):
    """
    Test that configure_stdlib_logging() creates the log directory (if needed)
    and calls logging.config.dictConfig(...) with the correct structure.
    """
    # Patch out Path.mkdir to confirm it's called with the correct path.
    mkdir_mock = mocker.patch("pathlib.Path.mkdir")
    dict_config_mock = mocker.patch("logging.config.dictConfig")

    # Execute
    configure_stdlib_logging()

    # Check that we tried to create the log directory for settings.LOG_PATH
    mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)

    # Confirm dict_config_mock was called once with a dict that includes a "handlers" key, etc.
    assert dict_config_mock.call_count == 1
    args, kwargs = dict_config_mock.call_args
    log_config = args[0]
    assert "version" in log_config
    assert "handlers" in log_config
    assert "console" in log_config["handlers"]
    assert "file" in log_config["handlers"]
    # Optional: check the log level matches settings.LOG_LEVEL
    assert log_config["handlers"]["console"]["level"] == settings.LOG_LEVEL


@patch("app.core.logging_configuration.settings.ENVIRONMENT", new="development")
def test_setup_structlog_dev(mocker):
    """
    If ENVIRONMENT=development, we expect a dev ConsoleRenderer with colors=True.
    """
    configure_mock = mocker.patch("structlog.configure")

    setup_structlog()

    assert configure_mock.call_count == 1
    # Inspect the 'processors' argument from structlog.configure(...)
    _, kwargs = configure_mock.call_args
    processors = kwargs["processors"]
    # The last processor in dev mode is structlog.dev.ConsoleRenderer
    from structlog.dev import ConsoleRenderer

    assert isinstance(processors[-1], ConsoleRenderer)


@patch("app.core.logging_configuration.settings.ENVIRONMENT", new="production")
def test_setup_structlog_production(mocker):
    """
    With our plain text configuration, all environments now use ConsoleRenderer.
    """
    configure_mock = mocker.patch("structlog.configure")

    setup_structlog()

    _, kwargs = configure_mock.call_args
    processors = kwargs["processors"]
    from structlog.dev import ConsoleRenderer

    assert isinstance(processors[-1], ConsoleRenderer)


def test_AppLogger_basic_methods(mocker):
    # Create a mock structlog logger
    structlog_logger_mock = mocker.MagicMock()
    # Make the bind() method return the same mock so we stay on one logger
    structlog_logger_mock.bind.return_value = structlog_logger_mock

    # Patch get_logger(...) to return our mock
    get_logger_mock = mocker.patch(
        "structlog.get_logger", return_value=structlog_logger_mock
    )

    app_logger = AppLogger("testlogger")

    get_logger_mock.assert_called_once_with("testlogger")

    # Now calls to app_logger.bind_context won't replace structlog_logger_mock
    app_logger.bind_context(user_id=123, action="login")
    assert app_logger.context == {"user_id": 123, "action": "login"}

    # info
    app_logger.info("some_event", extra="stuff")
    # error
    app_logger.error("error_event", error=ValueError("test error"), code=500)
    # warning
    app_logger.warning("warn_event", detail="warning detail")
    # debug
    app_logger.debug("debug_event", debug_flag=True)
    # audit
    app_logger.audit("deleted_record", user_id=123, record_id="abc")

    # Now the calls all go to structlog_logger_mock
    assert structlog_logger_mock.info.call_count == 2  # some_event + audit
    assert structlog_logger_mock.error.call_count == 1
    assert structlog_logger_mock.warning.call_count == 1
    assert structlog_logger_mock.debug.call_count == 1


def test_setup_logging(mocker):
    """
    Test that setup_logging() calls configure_stdlib_logging() and setup_structlog().
    """
    conf_stdlib_mock = mocker.patch(
        "app.core.logging_configuration.configure_stdlib_logging"
    )
    conf_structlog_mock = mocker.patch("app.core.logging_configuration.setup_structlog")

    setup_logging()

    conf_stdlib_mock.assert_called_once()
    conf_structlog_mock.assert_called_once()


def test_get_logger(mocker):
    """
    Test that get_logger(name) returns an AppLogger with the given name.
    """
    # We'll patch AppLogger to confirm it's created
    app_logger_init = mocker.patch(
        "app.core.logging_configuration.AppLogger", autospec=True
    )

    logger_instance = get_logger("test_module")

    app_logger_init.assert_called_once_with("test_module")
    assert logger_instance == app_logger_init.return_value


def test_configure_stdlib_logging_oserror(mocker):
    """
    Covers lines 147-148 by forcing Path.mkdir to raise an OSError,
    simulating a directory creation failure.
    """
    mkdir_mock = mocker.patch.object(
        Path, "mkdir", side_effect=OSError("Permission denied")
    )
    dict_config_mock = mocker.patch("logging.config.dictConfig")

    with pytest.raises(OSError, match="Permission denied"):
        configure_stdlib_logging()

    mkdir_mock.assert_called_once()
    # If mkdir() fails, we never call dictConfig
    dict_config_mock.assert_not_called()


@patch("app.core.logging_configuration.settings.ENVIRONMENT", new="staging")
def test_setup_structlog_unknown_env(mocker):
    """
    Covers environments that aren't 'development' or 'production'.
    We now expect ConsoleRenderer for all environments.
    """
    configure_mock = mocker.patch("structlog.configure")

    setup_structlog()

    configure_mock.assert_called_once()
    _, kwargs = configure_mock.call_args
    processors = kwargs["processors"]
    from structlog.dev import ConsoleRenderer

    assert isinstance(processors[-1], ConsoleRenderer)
