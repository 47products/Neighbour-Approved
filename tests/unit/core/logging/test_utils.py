"""
Unit tests for the logging utilities module.

This module contains comprehensive tests for the logging utilities defined
in the utils.py module, including context adapters, logging decorators,
and the operation logger context manager.
"""

import logging
from unittest.mock import MagicMock, patch
import pytest

from app.core.logging.utils import (
    LoggingContextAdapter,
    get_context_logger,
    log_function_call,
    log_exception,
    OperationLogger,
)


class TestLoggingContextAdapter:
    """Tests for the LoggingContextAdapter class."""

    def test_process_with_context(self):
        """
        Test that the process method correctly adds context to log messages.

        This test verifies that when context is provided, it is correctly
        formatted and appended to the log message.
        """
        # Arrange
        logger = MagicMock()
        extra = {"user_id": "123", "request_id": "abc456"}
        adapter = LoggingContextAdapter(logger, extra)

        # Act
        message, kwargs = adapter.process("Test message", {})

        # Assert
        assert message == "Test message [user_id=123] [request_id=abc456]"
        assert kwargs == {}

    def test_process_without_context(self):
        """
        Test that the process method works correctly with empty context.

        This test verifies that when no context is provided, the message
        remains unchanged.
        """
        # Arrange
        logger = MagicMock()
        adapter = LoggingContextAdapter(logger, {})

        # Act
        message, kwargs = adapter.process("Test message", {"extra": "value"})

        # Assert
        assert message == "Test message"
        assert kwargs == {"extra": "value"}


class TestGetContextLogger:
    """Tests for the get_context_logger function."""

    @patch("app.core.logging.utils.get_logger")
    def test_get_context_logger_returns_adapter(self, mock_get_logger):
        """
        Test that get_context_logger returns a LoggingContextAdapter instance.

        This test verifies that the function correctly creates and returns
        a logging adapter with the provided context.
        """
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Act
        result = get_context_logger("test_module", user_id="123")

        # Assert
        assert isinstance(result, LoggingContextAdapter)
        assert result.extra == {"user_id": "123"}
        mock_get_logger.assert_called_once_with("test_module")


class TestLogFunctionCall:
    """Tests for the log_function_call decorator."""

    @patch("app.core.logging.utils.get_logger")
    def test_decorator_logs_function_call_and_return(self, mock_get_logger):
        """
        Test that the decorator logs function entry and exit with parameters and result.

        This test verifies that the decorator correctly logs when a function
        is called, including its parameters, and when it returns with its result.
        """
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Define a function with the decorator
        @log_function_call()
        def test_function(a, b):
            return a + b

        # Act
        result = test_function(1, 2)

        # Assert
        assert result == 3
        assert mock_logger.log.call_count == 2

        # Check first call (function entry) - now using % formatting
        call_info = mock_logger.log.call_args_list[0]
        args = call_info[0]  # Get the positional arguments tuple
        assert args[0] == logging.DEBUG
        assert args[1] == "Calling %s(%s)"
        assert args[2] == "test_function"
        assert "1, 2" in args[3]  # Correct assertion for the actual call

        # Check second call (function exit) - now using % formatting
        call_info = mock_logger.log.call_args_list[1]  # Use consistent approach
        args = call_info[0]  # Get the positional arguments tuple
        assert args[0] == logging.DEBUG
        assert args[1] == "%s returned %s"
        assert args[2] == "test_function"
        assert args[3] == "3"

    @patch("app.core.logging.utils.get_logger")
    def test_decorator_logs_function_exception(self, mock_get_logger):
        """
        Test that the decorator logs exceptions raised by the function.

        This test verifies that when a decorated function raises an exception,
        the decorator properly logs the exception information.
        """
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Define a function with the decorator that raises an exception
        @log_function_call()
        def test_function():
            raise ValueError("Test error")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            test_function()

        assert str(exc_info.value) == "Test error"
        assert mock_logger.log.call_count == 1  # Only function entry is logged
        mock_logger.error.assert_called_once()  # Exception is logged at error level

        # Check error log - now using % formatting
        args, kwargs = mock_logger.error.call_args
        assert args[0] == "%s raised %s: %s"
        assert args[1] == "test_function"
        assert args[2] == "ValueError"
        assert args[3] == "Test error"
        assert kwargs["exc_info"] is True

    @patch("app.core.logging.utils.get_logger")
    def test_decorator_with_custom_level(self, mock_get_logger):
        """
        Test that the decorator uses the specified logging level.

        This test verifies that the decorator respects the custom logging
        level passed as a parameter.
        """
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Define a function with the decorator using INFO level
        @log_function_call(level=logging.INFO)
        def test_function():
            return "result"

        # Act
        test_function()

        # Assert
        assert mock_logger.log.call_count == 2

        # Check both calls use INFO level
        args1, _ = mock_logger.log.call_args_list[0]
        args2, _ = mock_logger.log.call_args_list[1]
        assert args1[0] == logging.INFO
        assert args2[0] == logging.INFO


class TestLogException:
    """Tests for the log_exception function."""

    def test_log_exception_uses_correct_level(self):
        """
        Test that log_exception logs at the specified level.

        This test verifies that the function correctly logs the exception
        information at the specified logging level.
        """
        # Arrange
        mock_logger = MagicMock()
        exception = ValueError("Test error")

        # Act
        log_exception(
            mock_logger, "An error occurred", exception, level=logging.WARNING
        )

        # Assert
        mock_logger.log.assert_called_once()
        args, _ = mock_logger.log.call_args
        assert args[0] == logging.WARNING
        # Check format string and arguments for % formatting
        assert args[1] == "%s: %s: %s\n%s"
        assert args[2] == "An error occurred"
        assert args[3] == "ValueError"
        assert args[4] == "Test error"

    def test_log_exception_default_level(self):
        """
        Test that log_exception uses ERROR level by default.

        This test verifies that when no level is specified, the function
        logs at the ERROR level.
        """
        # Arrange
        mock_logger = MagicMock()
        exception = RuntimeError("Runtime error")

        # Act
        log_exception(mock_logger, "Something failed", exception)

        # Assert
        mock_logger.log.assert_called_once()
        args, _ = mock_logger.log.call_args
        assert args[0] == logging.ERROR
        # Check format string and arguments for % formatting
        assert args[1] == "%s: %s: %s\n%s"
        assert args[2] == "Something failed"
        assert args[3] == "RuntimeError"
        assert args[4] == "Runtime error"

    def test_log_exception_includes_traceback(self):
        """
        Test that log_exception includes traceback information.

        This test verifies that the function includes the exception traceback
        in the log message.
        """
        # Arrange
        mock_logger = MagicMock()
        exception = KeyError("Missing key")

        # Act
        with patch("traceback.format_exc", return_value="Mock traceback"):
            log_exception(mock_logger, "Key error", exception)

        # Assert
        mock_logger.log.assert_called_once()
        args, _ = mock_logger.log.call_args
        # Check that traceback is included in the arguments
        assert args[1] == "%s: %s: %s\n%s"
        assert args[5] == "Mock traceback"


class TestOperationLogger:
    """Tests for the OperationLogger context manager."""

    def test_successful_operation_logging(self):
        """
        Test logging of a successful operation.

        This test verifies that the context manager correctly logs the start
        and successful completion of an operation, including timing information.
        """
        # Arrange
        mock_logger = MagicMock()

        # Patch time.time to return controlled values for duration calculation
        time_values = [1000.0, 1002.5]  # Start time, end time (2.5 second difference)

        with patch("time.time", side_effect=time_values):
            # Act - note: using with no log_options is valid
            with OperationLogger(mock_logger, "Test operation"):
                pass  # Successful operation with no exceptions

        # Assert
        assert mock_logger.log.call_count == 2

        # Check start log
        start_call = mock_logger.log.call_args_list[0]
        assert start_call[0][0] == logging.INFO
        assert "Starting operation: Test operation" in start_call[0][1]

        # Check completion log
        end_call = mock_logger.log.call_args_list[1]
        assert end_call[0][0] == logging.INFO
        assert "Completed operation: Test operation in 2.5000s" in end_call[0][1]

    def test_failed_operation_logging(self):
        """
        Test logging of a failed operation.

        This test verifies that the context manager correctly logs the start
        and failure of an operation that raises an exception.
        """
        # Arrange
        mock_logger = MagicMock()

        # Patch time.time to return controlled values
        time_values = [1000.0, 1001.0]  # 1 second difference

        with patch("time.time", side_effect=time_values):
            # Act
            try:
                with OperationLogger(mock_logger, "Failed operation"):
                    raise ValueError("Operation failed")
            except ValueError:
                pass  # We expect the exception to be raised

        # Assert
        assert mock_logger.log.call_count == 2

        # Check start log
        start_call = mock_logger.log.call_args_list[0]
        assert start_call[0][0] == logging.INFO
        assert "Starting operation: Failed operation" in start_call[0][1]

        # Check failure log
        end_call = mock_logger.log.call_args_list[1]
        assert end_call[0][0] == logging.ERROR
        assert "Failed operation: Failed operation after 1.0000s" in end_call[0][1]
        assert "ValueError: Operation failed" in end_call[0][1]
        assert end_call[1]["exc_info"] is True

    def test_operation_logger_with_context(self):
        """
        Test operation logging with additional context information.

        This test verifies that the context manager correctly includes
        provided context information in the log messages.
        """
        # Arrange
        mock_logger = MagicMock()
        context = {"user_id": "123", "request_id": "abc789"}

        # Act - updated to use log_options
        with patch("time.time", side_effect=[1000.0, 1003.0]):
            with OperationLogger(
                mock_logger, "Context operation", log_options={"context": context}
            ):
                pass

        # Assert
        assert mock_logger.log.call_count == 2

        # Check both logs include context information
        for call_args in mock_logger.log.call_args_list:
            log_message = call_args[0][1]
            assert "[user_id=123]" in log_message
            assert "[request_id=abc789]" in log_message

    def test_operation_logger_custom_log_levels(self):
        """
        Test operation logging with custom log levels.

        This test verifies that the context manager correctly uses the
        specified custom log levels for normal and error messages.
        """
        # Arrange
        mock_logger = MagicMock()

        # Act - successful operation with custom level - updated to use log_options
        with patch("time.time", side_effect=[1000.0, 1001.0]):
            with OperationLogger(
                mock_logger, "Debug operation", log_options={"log_level": logging.DEBUG}
            ):
                pass

        # Assert
        assert mock_logger.log.call_count == 2
        assert mock_logger.log.call_args_list[0][0][0] == logging.DEBUG
        assert mock_logger.log.call_args_list[1][0][0] == logging.DEBUG

        # Reset mock
        mock_logger.reset_mock()

        # Act - failed operation with custom error level - updated to use log_options
        with patch("time.time", side_effect=[1000.0, 1001.0]):
            try:
                with OperationLogger(
                    mock_logger,
                    "Warning error operation",
                    log_options={
                        "log_level": logging.DEBUG,
                        "error_level": logging.WARNING,
                    },
                ):
                    raise ValueError("Test error")
            except ValueError:
                pass

        # Assert
        assert mock_logger.log.call_count == 2
        assert mock_logger.log.call_args_list[0][0][0] == logging.DEBUG  # Start log
        assert mock_logger.log.call_args_list[1][0][0] == logging.WARNING  # Error log
