"""
Logging configuration module for the Neighbour Approved application.

This module sets up structured logging using structlog and Rich for enhanced visualization,
with proper formatting, context management, and integration with standard library logging.
It provides consistent logging patterns across the application with support for different
environments and log levels.

Attributes:
    settings: Core application settings instance
    console: Rich console instance for enhanced terminal output
"""

import logging
import logging.config
from pathlib import Path
from typing import Any, Dict, Optional
import structlog
from rich.console import Console
from rich.traceback import install as install_rich_traceback

from app.core.config import Settings

# Initialize settings and Rich console
settings = Settings()
console = Console(force_terminal=True)
install_rich_traceback(show_locals=True)


def configure_stdlib_logging() -> None:
    """Configure standard library logging to work with structlog and Rich.

    Sets up the standard library logging configuration with structured formatting,
    file rotation, and separate handlers for console and file output.

    The configuration includes:
        - Console output using Rich for enhanced visualization
        - Daily rotating file logs
        - Separate error log file
        - SQL query logging based on settings

    Raises:
        OSError: If log directory creation fails
    """
    log_path = Path(settings.LOG_PATH)
    log_path.mkdir(parents=True, exist_ok=True)  # Ensure log directory exists

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(message)s (%(name)s:%(lineno)d)",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(message)s %(name)s %(lineno)d",
            },
        },
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "formatter": "standard",
                "show_time": True,
                "show_level": True,
                "rich_tracebacks": True,
                "tracebacks_show_locals": True,
                "markup": False,  # Prevent ANSI escape codes in logs
                "level": settings.LOG_LEVEL,
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "json" if settings.LOG_FORMAT == "json" else "standard",
                "filename": log_path / "app.log",
                "encoding": "utf-8",
                "level": settings.LOG_LEVEL,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": settings.LOG_LEVEL,
            },
        },
    }

    # Apply configuration
    logging.config.dictConfig(log_config)


def setup_structlog() -> None:
    """Configure structlog with enhanced processors and Rich integration."""
    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")

    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.ENVIRONMENT == "development":
        # Enable colors only for console
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=True)]
    else:
        # Remove ANSI colors in production logs
        processors = shared_processors + [
            structlog.processors.JSONRenderer()  # Logs as clean JSON
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class AppLogger:
    """Application logger with context management and standard methods.

    This class provides a consistent interface for logging across the application,
    with support for context management and standardized log fields.

    Attributes:
        logger: Structured logger instance
        context (dict): Current logging context
    """

    def __init__(self, name: str):
        """Initialize the logger with a given name."""
        self.logger = structlog.get_logger(name)
        self.context: Dict[str, Any] = {}

    def bind_context(self, **kwargs: Any) -> None:
        """Add context to all subsequent log calls."""
        self.context.update(kwargs)
        self.logger = self.logger.bind(**kwargs)

    def clear_context(self) -> None:
        """Clear the current logging context."""
        self.context = {}
        self.logger = structlog.get_logger(self.logger.name)

    def info(self, event: str, **kwargs: Any) -> None:
        """Log an info level message."""
        self.logger.info(event, **kwargs)

    def error(
        self, event: str, error: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """Log an error level message with optional exception details."""
        log_kwargs = kwargs.copy()
        if error:
            log_kwargs["error_type"] = type(error).__name__
            log_kwargs["error_message"] = str(error)
        self.logger.error(event, **log_kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log a warning level message."""
        self.logger.warning(event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log a debug level message."""
        self.logger.debug(event, **kwargs)

    def audit(self, event: str, user_id: Optional[int] = None, **kwargs: Any) -> None:
        """Log an audit event with user information."""
        audit_kwargs = {"audit_event": event, "user_id": user_id, **kwargs}
        self.logger.info("audit_log", **audit_kwargs)


def setup_logging() -> None:
    """Initialize all logging configurations for the application.

    Sets up both standard library logging and structlog configurations
    for comprehensive logging support across the application.
    """
    configure_stdlib_logging()
    setup_structlog()


def get_logger(name: str) -> AppLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name for identification

    Returns:
        AppLogger: Configured logger instance with the specified name
    """
    return AppLogger(name)
