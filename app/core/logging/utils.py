"""
Logging utilities for the Neighbour Approved application.

This module provides utility functions and classes to support
the application's logging needs, such as context management
and specialized logging adapters.
"""

import time
import logging
import functools
import traceback
from typing import Any, Dict, Callable, TypeVar, Optional, cast

from app.core.logging.logger import get_logger

# Type variable for function return types
T = TypeVar("T")


class LoggingContextAdapter(logging.LoggerAdapter):
    """
    Adapter that adds context information to log messages.

    This adapter allows adding custom context information to all
    log messages without modifying the underlying logger.
    """

    def process(self, msg, kwargs):
        """
        Process the log message to add context information.

        Args:
            msg: The log message
            kwargs: Additional keyword arguments

        Returns:
            Tuple: Modified message and kwargs
        """
        context_str = " ".join(f"[{k}={v}]" for k, v in self.extra.items())
        if context_str:
            return f"{msg} {context_str}", kwargs
        return msg, kwargs


def get_context_logger(module_name: str, **context) -> logging.LoggerAdapter:
    """
    Get a logger with additional context information.

    This function creates a logger that automatically includes
    the provided context information in all log messages.

    Args:
        module_name: The module name for the logger
        **context: Additional context key-value pairs

    Returns:
        LoggerAdapter: A logger adapter with context
    """
    logger = get_logger(module_name)
    return LoggingContextAdapter(logger, context)


def log_function_call(level: int = logging.DEBUG):
    """
    Decorator to log function entry and exit with parameters and result.

    This decorator logs when a function is called and when it returns,
    including the parameters passed and the result returned.

    Args:
        level: The logging level to use

    Returns:
        Callable: Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)

            # Log function entry
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)

            logger.log(level, "Calling %s(%s)", func.__name__, signature)

            try:
                # Call the function
                result = func(*args, **kwargs)

                # Log function exit
                logger.log(level, "%s returned %s", func.__name__, repr(result))

                return result
            except Exception as e:
                # Log exception
                logger.error(
                    "%s raised %s: %s",
                    func.__name__,
                    type(e).__name__,
                    str(e),
                    exc_info=True,
                )
                raise

        return cast(Callable[..., T], wrapper)

    return decorator


def log_exception(
    logger: logging.Logger, message: str, exc: Exception, level: int = logging.ERROR
):
    """
    Log an exception with a structured format.

    This utility function standardizes how exceptions are logged,
    including traceback information and exception details.

    Args:
        logger: The logger to use
        message: The message to log
        exc: The exception to log
        level: The logging level to use
    """
    exc_type = type(exc).__name__
    exc_message = str(exc)
    tb = traceback.format_exc()

    logger.log(level, "%s: %s: %s\n%s", message, exc_type, exc_message, tb)


class OperationLogger:
    """
    Context manager for logging operations with timing information.

    This context manager logs when an operation starts and completes,
    including how long it took. It also logs any exceptions raised
    during the operation.
    """

    # Class-level defaults
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_ERROR_LEVEL = logging.ERROR

    def __init__(
        self,
        logger: logging.Logger,
        operation_name: str,
        log_options: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the context manager.

        Args:
            logger: The logger to use
            operation_name: Name of the operation being performed
            log_options: Dictionary containing logging options:
                - log_level: Level to log normal messages (default: INFO)
                - error_level: Level to log error messages (default: ERROR)
                - context: Additional context information to include in logs
        """
        self.logger = logger
        self.operation_name = operation_name
        # Extract options from the dictionary with defaults
        options = log_options or {}
        self.log_level = options.get("log_level", self.DEFAULT_LOG_LEVEL)
        self.error_level = options.get("error_level", self.DEFAULT_ERROR_LEVEL)
        self.context = options.get("context", {})
        self.start_time = None

    def __enter__(self):
        """
        Enter the context manager, logging the start of the operation.

        Returns:
            OperationLogger: The context manager instance
        """
        self.start_time = time.time()

        context_str = ""
        if self.context:
            context_str = " " + " ".join(f"[{k}={v}]" for k, v in self.context.items())

        self.logger.log(
            self.log_level, f"Starting operation: {self.operation_name}{context_str}"
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager, logging the completion or failure.

        Args:
            exc_type: Type of any exception raised
            exc_val: The exception instance raised
            exc_tb: The exception traceback

        Returns:
            bool: False to propagate exceptions
        """
        duration = time.time() - self.start_time
        formatted_duration = f"{duration:.4f}s"

        context_str = ""
        if self.context:
            context_str = " " + " ".join(f"[{k}={v}]" for k, v in self.context.items())

        if exc_type is None:
            # Operation completed successfully
            self.logger.log(
                self.log_level,
                f"Completed operation: {self.operation_name} in {formatted_duration}{context_str}",
            )
        else:
            # Operation failed
            self.logger.log(
                self.error_level,
                f"Failed operation: {self.operation_name} after {formatted_duration}: "
                f"{exc_type.__name__}: {str(exc_val)}{context_str}",
                exc_info=True,
            )

        # Don't suppress exceptions
        return False
