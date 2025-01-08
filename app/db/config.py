"""
Configuration management module.

This module implements the application's configuration management system using
Pydantic V2's settings management. It provides a secure and validated approach to
handling environment variables and sensitive configuration data while maintaining
flexibility for different deployment environments.

The module enforces proper validation of configuration values and provides clear
error messages when required settings are missing or invalid. It integrates with
environment variables and supports multiple configuration profiles for different
deployment scenarios.
"""

from functools import lru_cache
from pydantic import (
    Field,
    PostgresDsn,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """
    Database-specific configuration settings.

    This class manages database connection parameters and credentials,
    ensuring proper validation and secure handling of sensitive information.

    Attributes:
        POSTGRES_USER: Database username
        POSTGRES_PASSWORD: Database password (stored securely)
        POSTGRES_HOST: Database host address
        POSTGRES_PORT: Database port number
        POSTGRES_DB: Database name
        ENABLE_SQL_ECHO: Flag to enable SQL query logging
        MIN_POOL_SIZE: Minimum database connection pool size
        MAX_POOL_SIZE: Maximum database connection pool size
        POOL_RECYCLE_SECONDS: Connection recycle interval
    """

    POSTGRES_USER: str = Field(
        ...,
        description="Database username",
    )
    POSTGRES_PASSWORD: SecretStr = Field(
        ...,
        description="Database password",
    )
    POSTGRES_HOST: str = Field(
        ...,
        description="Database host address",
    )
    POSTGRES_PORT: int = Field(
        default=5432,
        description="Database port number",
    )
    POSTGRES_DB: str = Field(
        ...,
        description="Database name",
    )
    ENABLE_SQL_ECHO: bool = Field(
        default=False,
        description="Enable SQL query logging",
    )
    MIN_POOL_SIZE: int = Field(
        default=5,
        description="Minimum database connection pool size",
    )
    MAX_POOL_SIZE: int = Field(
        default=20,
        description="Maximum database connection pool size",
    )
    POOL_RECYCLE_SECONDS: int = Field(
        default=1800,
        description="Connection recycle interval in seconds",
    )

    @field_validator("POSTGRES_PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """
        Validate that the port number is within a valid range.

        Args:
            v: Port number to validate

        Returns:
            int: Validated port number

        Raises:
            ValueError: If port number is invalid
        """
        if not 1 <= v <= 65535:
            raise ValueError("Port number must be between 1 and 65535")
        return v

    @field_validator("MIN_POOL_SIZE", "MAX_POOL_SIZE")
    @classmethod
    def validate_pool_size(cls, v: int) -> int:
        """
        Validate that pool sizes are positive integers.

        Args:
            v: Pool size to validate

        Returns:
            int: Validated pool size

        Raises:
            ValueError: If pool size is invalid
        """
        if v < 1:
            raise ValueError("Pool size must be positive")
        return v

    @model_validator(mode="after")
    def validate_pool_sizes(self) -> "DatabaseSettings":
        """
        Validate that minimum pool size is less than maximum.

        Returns:
            DatabaseSettings: The validated settings instance

        Raises:
            ValueError: If pool size configuration is invalid
        """
        if self.MIN_POOL_SIZE > self.MAX_POOL_SIZE:
            raise ValueError(
                "Minimum pool size cannot be greater than maximum pool size"
            )
        return self


class Settings(DatabaseSettings):
    """
    Main application configuration settings.

    This class extends database settings with additional application-wide
    configuration parameters. It provides a centralized location for all
    configuration management while ensuring proper validation and security.

    Attributes:
        APPLICATION_NAME: Name of the application
        ENVIRONMENT: Deployment environment (development, staging, production)
        DEBUG: Debug mode flag
        API_PREFIX: Prefix for all API endpoints
        CORS_ORIGINS: Allowed CORS origins
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
    CORS_ORIGINS: list[str] = Field(
        default_factory=list,
        description="Allowed CORS origins",
    )

    # Logging Configuration
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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @property
    def database_url(self) -> PostgresDsn:
        """
        Construct the database URL from individual settings.

        Returns:
            PostgresDsn: Validated database URL
        """
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate the deployment environment setting.

        Args:
            v: Environment name to validate

        Returns:
            str: Validated environment name

        Raises:
            ValueError: If environment name is invalid
        """
        allowed_environments = {"development", "staging", "production"}
        if v.lower() not in allowed_environments:
            raise ValueError(
                f"Environment must be one of: {', '.join(allowed_environments)}"
            )
        return v.lower()

    @field_validator("API_PREFIX")
    @classmethod
    def validate_api_prefix(cls, v: str) -> str:
        """
        Validate the API prefix format.

        Args:
            v: API prefix to validate

        Returns:
            str: Validated API prefix

        Raises:
            ValueError: If API prefix format is invalid
        """
        if not v.startswith("/"):
            v = f"/{v}"
        return v.rstrip("/")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {', '.join(allowed_levels)}")
        return v.upper()

    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        allowed_formats = {"json", "standard"}
        if v.lower() not in allowed_formats:
            raise ValueError(f"Log format must be one of: {', '.join(allowed_formats)}")
        return v.lower()


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
    """
    return Settings()
