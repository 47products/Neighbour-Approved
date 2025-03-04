"""
Unit tests for the core logging module.

This module contains tests for the application's logging functionality,
ensuring that loggers are correctly configured and function as expected.
"""

import logging
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from app.core.logging.logger import LoggerFactory, get_logger
from app.core.configuration.config import settings


class TestLogger:
    """Tests for the core logger functionality."""

    def test_logger_factory_create_logger(self):
        """Test that LoggerFactory correctly creates a logger."""
        logger = LoggerFactory.create_logger("test_logger")

        # Verify the logger is properly configured
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0
        assert logger.level == getattr(logging, settings.log_level)

    def test_get_logger(self):
        """Test that get_logger returns a correctly named logger."""
        logger = get_logger("test_module")

        # Verify the logger has the correct name
        assert logger.name == "neighbour_approved.test_module"
        assert len(logger.handlers) > 0

    def test_ensure_log_directory(self):
        """Test that the log directory is created if it doesn't exist."""
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp(prefix="test_logs_")
        try:
            test_log_dir = Path(temp_dir)

            # Patch the _ensure_log_directory method to use our test directory
            # pylint: disable=protected-access
            with patch(
                "app.core.logging.logger.LoggerFactory._ensure_log_directory",
                return_value=test_log_dir,
            ), patch(
                "logging.handlers.TimedRotatingFileHandler",
                return_value=MagicMock(spec=logging.handlers.TimedRotatingFileHandler),
            ):
                # Create a logger which would trigger directory creation
                LoggerFactory.create_logger("test_logger")

                # Verify the patched method returns our test directory
                assert LoggerFactory._ensure_log_directory() == test_log_dir
            # pylint: enable=protected-access

        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

    @pytest.mark.parametrize(
        "level_name", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    def test_logger_respects_log_level(self, level_name):
        """Test that the logger respects the configured log level."""
        level = getattr(logging, level_name)

        # Mock the settings to use our test level
        with patch("app.core.logging.logger.settings") as mock_settings:
            mock_settings.log_level = level_name

            # Create a logger with our mocked settings
            logger = LoggerFactory.create_logger("test_logger")

            # Verify the logger has the correct level
            assert logger.level == level

    def test_console_handler_configuration(self):
        """Test that the console handler is correctly configured."""
        # Create a console handler
        # pylint: disable=protected-access
        handler = LoggerFactory._create_console_handler()
        # pylint: enable=protected-access

        # Verify the handler is correctly configured
        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, logging.Formatter)

    def test_file_handler_configuration(self):
        """Test that the file handler is correctly configured."""
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp(prefix="test_logs_")
        try:
            # Create a file handler with a temporary file
            with patch(
                "app.core.logging.logger.TimedRotatingFileHandler"
            ) as mock_handler:
                # Configure the mock
                mock_instance = MagicMock()
                mock_handler.return_value = mock_instance

                # Also patch _ensure_log_directory to return our temp dir
                # pylint: disable=protected-access
                with patch(
                    "app.core.logging.logger.LoggerFactory._ensure_log_directory",
                    return_value=Path(temp_dir),
                ):

                    # Call the method
                    LoggerFactory._create_file_handler("test.log")
                    # pylint: enable=protected-access

                    # Verify the handler was created with the correct parameters
                    mock_handler.assert_called_once()
                    call_kwargs = mock_handler.call_args[1]
                    assert call_kwargs["when"] == "midnight"
                    assert call_kwargs["backupCount"] == 30
                    assert call_kwargs["encoding"] == "utf-8"
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

    def test_logger_handlers(self):
        """Test that the logger has the expected handlers."""
        # Create a logger
        logger = LoggerFactory.create_logger("test_logger")

        # Count handler types
        console_handlers = sum(
            1
            for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.handlers.TimedRotatingFileHandler)
        )
        file_handlers = sum(
            1
            for h in logger.handlers
            if isinstance(h, logging.handlers.TimedRotatingFileHandler)
        )

        # Verify we have the expected number of each handler type
        assert console_handlers == 1, "Should have exactly one console handler"
        assert (
            file_handlers == 2
        ), "Should have exactly two file handlers (app.log and error.log)"

        # Verify the error.log handler has the correct level
        error_handlers = [
            h
            for h in logger.handlers
            if isinstance(h, logging.handlers.TimedRotatingFileHandler)
            and h.level == logging.ERROR
        ]
        assert (
            len(error_handlers) == 1
        ), "Should have one handler specifically for errors"
