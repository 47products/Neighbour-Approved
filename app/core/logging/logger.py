"""
Logging module for the Neighbour Approved application.

This module provides a centralised logging configuration for the application.
It initialises loggers that output to both console and files, with files
rolling over at midnight. The module sets up both general application logging
and a separate error log.
"""

import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.core.configuration.config import settings


class LoggerFactory:
    """
    Factory for creating and configuring loggers.

    This class handles the creation and configuration of loggers for the application,
    setting up appropriate handlers and formatters based on application settings.
    It ensures consistent logging across the application.
    """

    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def _ensure_log_directory():
        """Ensure the logs directory exists."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        return log_dir

    @classmethod
    def _create_console_handler(cls):
        """Create and configure a console handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(cls.DEFAULT_FORMAT, cls.DATE_FORMAT)
        )
        return console_handler

    @classmethod
    def _create_file_handler(cls, filename, level=logging.INFO):
        """
        Create and configure a file handler with midnight rotation.

        Args:
            filename: Name of the log file
            level: Logging level to use

        Returns:
            TimedRotatingFileHandler: Configured file handler
        """
        log_dir = cls._ensure_log_directory()
        file_path = log_dir / filename

        file_handler = TimedRotatingFileHandler(
            filename=file_path,
            when="midnight",
            backupCount=30,  # Keep 30 days of backups
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter(cls.DEFAULT_FORMAT, cls.DATE_FORMAT)
        )
        file_handler.setLevel(level)
        return file_handler

    @classmethod
    def create_logger(cls, name):
        """
        Create and configure a logger with the given name.

        This creates a logger that logs to both console and appropriate files,
        with configuration based on application settings.

        Args:
            name: Name of the logger (typically the module name)

        Returns:
            Logger: Configured logger instance
        """
        logger = logging.getLogger(name)

        # Clear any existing handlers (to prevent duplicates)
        if logger.hasHandlers():
            logger.handlers.clear()

        # Set the logger level based on settings
        log_level = getattr(logging, settings.log_level, logging.INFO)
        logger.setLevel(log_level)

        # Add console handler
        logger.addHandler(cls._create_console_handler())

        # Add file handlers
        logger.addHandler(cls._create_file_handler("app.log"))

        # Add error file handler (only captures ERROR and above)
        error_handler = cls._create_file_handler("error.log", logging.ERROR)
        logger.addHandler(error_handler)

        # Propagate to the root logger
        logger.propagate = False

        return logger


# Default application logger
app_logger = LoggerFactory.create_logger("neighbour_approved")


def get_logger(module_name):
    """
    Get a logger configured for the given module name.

    This is the main function to be used by application code to obtain
    a properly configured logger. It ensures consistent logging configuration
    across the application.

    Args:
        module_name: Name of the module (typically __name__)

    Returns:
        Logger: Configured logger instance
    """
    return LoggerFactory.create_logger(f"neighbour_approved.{module_name}")
