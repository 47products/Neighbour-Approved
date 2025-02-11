"""
Application configuration module for Neighbour Approved.

This module implements the core application configuration using Pydantic V2's
settings management. It provides secure and validated configuration handling
for application-wide settings.

Key components:
    - Settings: Core application configuration class
    - get_settings: Cached settings provider function

Typical usage example:
    settings = get_settings()
    log_level = settings.LOG_LEVEL
    app_name = settings.APPLICATION_NAME

Dependencies:
    - pydantic >=2.0.0
    - python-dotenv
"""

from functools import lru_cache
from typing import List
from pydantic import Field, PostgresDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Core application configuration settings.

    This class manages application-wide configuration parameters, providing
    validation and secure handling of environment variables and settings.

    Attributes:
        APPLICATION_NAME: Name of the application
        ENVIRONMENT: Deployment environment (development, staging, production)
        DEBUG: Debug mode flag
        API_PREFIX: Prefix for all API endpoints
        CORS_ORIGINS: Allowed CORS origins
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        LOG_FORMAT: Log format (json or standard)
        LOG_PATH: Path to log files directory
        ENABLE_REQUEST_LOGGING: Whether to log HTTP requests
        ENABLE_SQL_LOGGING: Whether to log SQL queries
        POSTGRES_USER: Database username
        POSTGRES_PASSWORD: Database password (stored securely)
        POSTGRES_HOST: Database host address
        POSTGRES_PORT: Database port number
        POSTGRES_DB: Database name
    """

    APPLICATION_NAME: str = Field(
        "Neighbour Approved",
        description="Application name",
    )
    ENVIRONMENT: str = Field(
        "development",
        description="Deployment environment",
    )
    DEBUG: bool = Field(
        False,
        description="Debug mode flag",
    )
    API_PREFIX: str = Field(
        "/api",
        description="API endpoint prefix",
    )
    CORS_ORIGINS: List[str] = Field(
        default_factory=list,
        description="Allowed CORS origins",
    )
    LOG_LEVEL: str = Field(
        "INFO",
        description="Logging level",
    )
    LOG_FORMAT: str = Field(
        "json",
        description="Log format (json or standard)",
    )
    LOG_PATH: str = Field(
        "logs",
        description="Path to log files directory",
    )
    ENABLE_REQUEST_LOGGING: bool = Field(
        True,
        description="Enable HTTP request logging",
    )
    ENABLE_SQL_LOGGING: bool = Field(
        False,
        description="Enable SQL query logging",
    )
    ENABLE_SQL_ECHO: bool = Field(
        default=False, description="Enable SQL query logging for debugging purposes"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    # Database settings
    POSTGRES_USER: str = Field(..., description="Database username")
    POSTGRES_PASSWORD: SecretStr = Field(..., description="Database password")
    POSTGRES_HOST: str = Field(..., description="Database host address")
    POSTGRES_PORT: int = Field(default=5432, description="Database port number")
    POSTGRES_DB: str = Field(..., description="Database name")

    @property
    def database_url(self) -> PostgresDsn:
        """
        Construct the database URL from individual settings.

        Returns:
            PostgresDsn: Validated database URL for SQLAlchemy
        """
        return PostgresDsn(
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        """
        Validate environment-specific configuration.

        This method ensures that configuration values are appropriate for the
        specified environment.

        Returns:
            Settings: The validated settings instance

        Raises:
            ValueError: If environment validation fails
        """
        allowed_environments = {"development", "staging", "production"}
        if self.ENVIRONMENT.lower() not in allowed_environments:
            raise ValueError(
                f"Environment must be one of: {', '.join(allowed_environments)}"
            )
        return self

    @model_validator(mode="after")
    def validate_log_settings(self) -> "Settings":
        """
        Validate logging-related settings.

        Ensures that logging configuration values are valid and compatible.

        Returns:
            Settings: The validated settings instance

        Raises:
            ValueError: If logging settings are invalid
        """
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.LOG_LEVEL.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {', '.join(allowed_levels)}")

        allowed_formats = {"json", "standard"}
        if self.LOG_FORMAT.lower() not in allowed_formats:
            raise ValueError(f"Log format must be one of: {', '.join(allowed_formats)}")

        return self


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache application settings.

    This function provides a cached instance of the settings class to avoid
    repeated environment variable lookups and validation. The cache is
    particularly useful in web applications where configuration is frequently
    accessed.

    Returns:
        Settings: Cached settings instance

    Example:
        settings = get_settings()
        debug_mode = settings.DEBUG
    """
    return Settings()
