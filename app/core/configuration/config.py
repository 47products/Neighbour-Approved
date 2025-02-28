"""
Core configuration service for the Neighbour Approved application.

This module provides a centralised way to access application configuration
from environment variables and .env files. It focuses solely on core
application settings without any business logic or domain-specific configuration.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class Settings(BaseSettings):
    """
    Core application settings loaded from environment variables.

    This class contains only the essential configuration needed for the
    application framework to function, without any business logic or
    domain-specific settings. All values are loaded from environment
    variables or .env files with no defaults hardcoded in the application.

    Attributes:
        app_name: Name of the application
        version: Application version string
        database_url: Database connection URL
        api_base_url: Base URL for the API
        secret_key: Secret key for security features
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format for log messages (standard, json)
        environment: Deployment environment (development, testing, production)
        debug: Whether debug mode is enabled
    """

    app_name: str = Field(default="Neighbour Approved")
    app_description: str = Field(default="API for Neighbour Approved platform")
    version: str = Field(default="0.1.0")
    database_url: str = Field(default="sqlite:///:memory:")
    api_base_url: str = Field(default="/api/v1")
    secret_key: str = Field(default="")
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="standard")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate the log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate the log format."""
        allowed_formats = ["standard", "json"]
        if v.lower() not in allowed_formats:
            raise ValueError(f"Log format must be one of {allowed_formats}")
        return v.lower()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate the environment."""
        allowed_environments = ["development", "testing", "staging", "production"]
        if v.lower() not in allowed_environments:
            raise ValueError(f"Environment must be one of {allowed_environments}")
        return v.lower()

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


def _check_missing_environment_variables() -> Dict[str, Any]:
    """
    Check for missing required environment variables.

    Returns:
        Dict[str, Any]: Dictionary of missing variables

    Note:
        This is a helper function for get_settings()
    """
    # Define the required fields to check
    required_fields = [
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

    missing_vars = []
    for field_name in required_fields:
        if field_name not in os.environ and field_name.upper() not in os.environ:
            missing_vars.append(field_name)

    return missing_vars


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
        ValidationError: If Pydantic validation fails
    """
    # Load environment variables from .env files
    _load_env_files()

    # Check for empty secret key before attempting to create Settings
    if os.getenv("SECRET_KEY") == "":
        raise ValueError("SECRET_KEY environment variable cannot be empty")

    try:
        return Settings()
    except ValidationError as e:
        # Provide more helpful error message for validation errors
        missing_vars = _check_missing_environment_variables()

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Original error: {str(e)}"
            ) from e
        raise
    except Exception as e:
        # More specific handling of other potential errors
        raise ValueError(f"Configuration error: {str(e)}") from e


# Create a global instance for easy import
try:
    settings = get_settings()
except (ValueError, ValidationError) as e:
    import sys

    print(f"ERROR: Failed to load configuration: {str(e)}", file=sys.stderr)
    # Create a placeholder settings object for import safety
    settings = None
