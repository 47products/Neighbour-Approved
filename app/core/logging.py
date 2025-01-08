"""
Logging configuration module for the Neighbour Approved application.

This module sets up structured logging using structlog and Rich for enhanced visualization,
with proper formatting, context management, and integration with standard library logging.
It provides consistent logging patterns across the application with support for different
environments and log levels.
"""

import logging
import logging.config
from pathlib import Path
import sys
from typing import Any, Dict, Optional
import structlog
from pythonjsonlogger import jsonlogger
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

from app.db.config import Settings

# Initialize settings and Rich console
settings = Settings()
console = Console(force_terminal=True)
install_rich_traceback(show_locals=True)


def configure_stdlib_logging() -> None:
    """Configure standard library logging to work with structlog and Rich."""
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d %(process)d %(thread)d %(threadName)s",
            },
            "rich": {
                "format": "%(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "formatter": "rich",
                "show_time": True,
                "show_level": True,
                "rich_tracebacks": True,
                "tracebacks_show_locals": True,
                "level": settings.LOG_LEVEL,
                "markup": True,
            },
            "json_console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout,
                "level": settings.LOG_LEVEL,
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "json",
                "filename": f"{settings.LOG_PATH}/app.log",
                "when": "midnight",
                "interval": 1,
                "backupCount": 30,
                "encoding": "utf-8",
                "level": settings.LOG_LEVEL,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": f"{settings.LOG_PATH}/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf-8",
                "level": "ERROR",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": [
                    (
                        "console"
                        if settings.ENVIRONMENT == "development"
                        else "json_console"
                    ),
                    "file",
                    "error_file",
                ],
                "level": settings.LOG_LEVEL,
            },
            "uvicorn": {
                "handlers": [
                    (
                        "console"
                        if settings.ENVIRONMENT == "development"
                        else "json_console"
                    )
                ],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": [
                    (
                        "console"
                        if settings.ENVIRONMENT == "development"
                        else "json_console"
                    ),
                    "file",
                ],
                "level": "INFO" if settings.ENABLE_SQL_LOGGING else "WARNING",
                "propagate": False,
            },
        },
    }

    # Ensure log directory exists
    Path(settings.LOG_PATH).mkdir(parents=True, exist_ok=True)

    # Apply configuration
    logging.config.dictConfig(log_config)


def setup_structlog() -> None:
    """Configure structlog with enhanced processors and Rich integration."""
    timestamper = structlog.processors.TimeStamper(fmt="iso")

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
        # Using simple string-based styles instead of functions
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            level_styles={
                "debug": "blue",
                "info": "green",
                "warning": "yellow",
                "error": "red",
                "critical": "red,bold",
            },
        )
        processors = shared_processors + [renderer]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class AppLogger:
    """
    Application logger with context management and standard methods.

    This class provides a consistent interface for logging across the application,
    with support for context management and standardized log fields.
    """

    def __init__(self, name: str):
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
    """Initialize all logging configurations for the application."""
    configure_stdlib_logging()
    setup_structlog()


def get_logger(name: str) -> AppLogger:
    """Get a configured logger instance."""
    return AppLogger(name)
