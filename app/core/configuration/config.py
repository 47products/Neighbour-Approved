"""
Core configuration service for the Neighbour Approved application.

This module provides a centralised way to access application configuration
from environment variables and .env files.
"""

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Callable

from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Constants for validation
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMATS = ["standard", "json"]
ENVIRONMENTS = ["development", "testing", "staging", "production"]


def _validate_field_value(
    value: str,
    allowed_values: List[str],
    field_name: str,
    transform: Callable = lambda x: x,
) -> str:
    """
    Validate that a field value is in the list of allowed values.

    Args:
        value: The value to validate
        allowed_values: List of allowed values
        field_name: Name of the field for error messages
        transform: Function to transform the value before checking

    Returns:
        The transformed value if valid

    Raises:
        ValueError: If the value is not in the allowed values
    """
    transformed_value = transform(value)
    if transformed_value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return transformed_value


class LoggingSettings(BaseSettings):
    """Logging-specific configuration settings."""

    level: str = Field(default="INFO")
    format: str = Field(default="standard")
    log_to_file: bool = Field(default=True)
    log_to_console: bool = Field(default=True)
    log_dir: str = Field(default="logs")
    app_log_filename: str = Field(default="app.log")
    error_log_filename: str = Field(default="error.log")
    backup_count: int = Field(default=30)

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate the log level."""
        return _validate_field_value(v, LOG_LEVELS, "Log level", str.upper)

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate the log format."""
        return _validate_field_value(v, LOG_FORMATS, "Log format", str.lower)


class Settings(BaseSettings):
    """Core application settings loaded from environment variables."""

    app_name: str = Field(default="Neighbour Approved API")
    app_description: str = Field(default="API for Neighbour Approved platform")
    version: str = Field(default="0.1.0")
    database_url: str = Field(default="sqlite:///:memory:")
    api_base_url: str = Field(default="/api/v1")
    secret_key: str = Field(default="")
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="standard")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Add logging settings
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate the log level."""
        return _validate_field_value(v, LOG_LEVELS, "Log level", str.upper)

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate the log format."""
        return _validate_field_value(v, LOG_FORMATS, "Log format", str.lower)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate the environment."""
        return _validate_field_value(v, ENVIRONMENTS, "Environment", str.lower)

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


def _load_env_files() -> None:
    """
    Load environment variables from .env files.

    Loads from environment-specific .env file first, then from the default .env file.
    Environment-specific files take precedence over the default file.
    """
    # Get base directory (project root)
    base_dir = Path(__file__).parents[3]

    # Get environment
    env = os.getenv("ENVIRONMENT", "development")
    env_specific_file = base_dir / f".env.{env}"
    default_env_file = base_dir / ".env"

    # Load environment-specific file first (if exists)
    if env_specific_file.exists():
        load_dotenv(str(env_specific_file), override=True)

    # Then load default file (if exists)
    if default_env_file.exists():
        load_dotenv(str(default_env_file))


def _get_required_env_vars() -> List[str]:
    """Get list of required environment variables."""
    return [
        "app_name",
        "app_description",
        "version",
        "database_url",
        "api_base_url",
        "secret_key",
        "log_level",
        "log_format",
        "environment",
        "debug",
    ]


def _check_missing_environment_variables() -> List[str]:
    """Check for missing required environment variables."""
    missing = []

    for field_name in _get_required_env_vars():
        # Check both uppercase and lowercase versions
        if (field_name not in os.environ) and (field_name.upper() not in os.environ):
            missing.append(field_name)

    return missing


def _validate_secret_key() -> None:
    """
    Validate that SECRET_KEY environment variable is not empty.

    Raises:
        ValueError: If SECRET_KEY is empty
    """
    if os.getenv("SECRET_KEY") == "":
        raise ValueError("SECRET_KEY environment variable cannot be empty")


def _handle_validation_error(error: ValidationError) -> ValueError:
    """Handle validation errors with improved error messages."""
    missing_vars = _check_missing_environment_variables()

    if missing_vars:
        return ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Original error: {str(error)}"
        )

    return ValueError(str(error))


def _create_settings() -> Settings:
    """Create and validate settings object with simplified error handling."""
    try:
        return Settings()
    except ValidationError as e:
        raise _handle_validation_error(e) from e
    except Exception as e:
        raise ValueError(f"Configuration error: {str(e)}") from e


@lru_cache()
def get_settings() -> Settings:
    """
    Load and return core application settings with caching.

    Returns:
        Settings: Core application configuration settings

    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    # Step 1: Load environment variables
    _load_env_files()

    # Step 2: Validate secret key
    _validate_secret_key()

    # Step 3: Create settings
    return _create_settings()


def _create_global_settings() -> Optional[Settings]:
    """
    Create and return the global settings instance.

    Returns:
        Settings: The global settings instance, or None if an error occurs
    """
    try:
        return get_settings()
    except ValueError as e:
        print(f"ERROR: Failed to load configuration: {str(e)}", file=sys.stderr)
        return None


# Create a global instance for easy import
settings = _create_global_settings()
