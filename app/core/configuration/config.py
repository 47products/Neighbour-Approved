"""
Core configuration service for the Neighbour Approved application.

This module provides a centralised way to access application configuration
from environment variables and .env files. It focuses solely on core
application settings without any business logic or domain-specific configuration.
"""

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Callable, Optional

from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


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
        transform: Function to transform the value before checking (e.g., upper, lower)

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
    """
    Logging-specific configuration settings.

    Attributes:
        level: The logging level to use
        format: The format for log messages
        log_to_file: Whether to log to files
        log_to_console: Whether to log to the console
        log_dir: Directory to store log files
        app_log_filename: Filename for the application log
        error_log_filename: Filename for the error log
        backup_count: Number of backup log files to keep
    """

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
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        return _validate_field_value(v, allowed_levels, "Log level", str.upper)

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate the log format."""
        allowed_formats = ["standard", "json"]
        return _validate_field_value(v, allowed_formats, "Log format", str.lower)


class Settings(BaseSettings):
    """
    Core application settings loaded from environment variables.

    This class contains only the essential configuration needed for the
    application framework to function, without any business logic or
    domain-specific settings. All values are loaded from environment
    variables or .env files with no defaults hardcoded in the application.

    Attributes:
        app_name: Name of the application
        app_description: Description of the application
        version: Application version string
        database_url: Database connection URL
        api_base_url: Base URL for the API
        secret_key: Secret key for security features
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format for log messages (standard, json)
        environment: Deployment environment (development, testing, production)
        debug: Whether debug mode is enabled
    """

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
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        return _validate_field_value(v, allowed_levels, "Log level", str.upper)

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate the log format."""
        allowed_formats = ["standard", "json"]
        return _validate_field_value(v, allowed_formats, "Log format", str.lower)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate the environment."""
        allowed_environments = ["development", "testing", "staging", "production"]
        return _validate_field_value(v, allowed_environments, "Environment", str.lower)

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


def _load_env_files() -> None:
    """
    Load environment variables from .env files.

    This function loads variables from environment-specific .env files
    first, then from the default .env file. Environment-specific files
    take precedence over the default file.
    """
    # Determine the base directory (project root)
    base_dir = Path(__file__).parents[3]

    # Load environment-specific .env file if it exists
    env = os.getenv("ENVIRONMENT", "development")
    env_specific_file = base_dir / f".env.{env}"

    if env_specific_file.exists():
        load_dotenv(str(env_specific_file), override=True)

    # Load default .env file
    default_env_file = base_dir / ".env"
    if default_env_file.exists():
        load_dotenv(str(default_env_file))


def _get_required_env_vars() -> List[str]:
    """
    Get list of required environment variables.

    Returns:
        List[str]: List of required environment variable names
    """
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
    """
    Check for missing required environment variables.

    Returns:
        List[str]: List of missing variable names
    """
    # Start with the list of required fields
    missing_vars = []

    # Check each required field
    for field_name in _get_required_env_vars():
        # Check both uppercase and lowercase versions
        if (field_name not in os.environ) and (field_name.upper() not in os.environ):
            missing_vars.append(field_name)

    return missing_vars


def _validate_secret_key() -> None:
    """
    Validate that the SECRET_KEY environment variable is not empty.

    Raises:
        ValueError: If SECRET_KEY is empty
    """
    if os.getenv("SECRET_KEY") == "":
        raise ValueError("SECRET_KEY environment variable cannot be empty")


@lru_cache()
def get_settings() -> Settings:
    """
    Load and return core application settings with caching.

    This function loads environment variables from .env files and returns
    a validated Settings object. Results are cached to avoid repeated loading.

    Returns:
        Settings: Core application configuration settings

    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    # Load environment variables from .env files
    _load_env_files()

    # Check for empty secret key before attempting to create Settings
    _validate_secret_key()

    try:
        return Settings()
    except ValidationError as e:
        # Check for missing environment variables for better error messages
        missing_vars = _check_missing_environment_variables()
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Original error: {str(e)}"
            ) from e
        # Re-raise the original ValidationError
        raise
    except Exception as e:
        # Handle other potential errors
        raise ValueError(f"Configuration error: {str(e)}") from e


def _create_global_settings() -> Optional[Settings]:
    """
    Create and return the global settings instance.

    This function handles the creation of the global settings instance,
    including error handling.

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
