"""
Database configuration module for Neighbour Approved.

This module implements database-specific configuration settings, providing
secure handling of database credentials and connection parameters. It extends
the core application configuration with database-specific settings.

Key components:
    - DatabaseSettings: Database configuration class
    - get_database_url: Database URL constructor function

Typical usage example:
    settings = DatabaseSettings()
    db_url = settings.database_url
    pool_size = settings.MAX_POOL_SIZE

Dependencies:
    - pydantic >=2.0.0
    - SQLAlchemy
"""

from pydantic import Field, PostgresDsn, SecretStr, model_validator
from app.core.config import Settings as CoreSettings


class DatabaseSettings(CoreSettings):
    """
    Database configuration settings.

    This class manages database connection parameters and credentials,
    ensuring proper validation and secure handling of sensitive information.

    Attributes:
        POSTGRES_USER: Database username
        POSTGRES_PASSWORD: Database password (stored securely)
        POSTGRES_HOST: Database host address
        POSTGRES_PORT: Database port number
        POSTGRES_DB: Database name
        MIN_POOL_SIZE: Minimum database connection pool size
        MAX_POOL_SIZE: Maximum database connection pool size
        POOL_RECYCLE_SECONDS: Connection recycle interval in seconds

    Typical usage example:
        settings = DatabaseSettings()
        db_url = settings.database_url
        max_connections = settings.MAX_POOL_SIZE
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

    @property
    def database_url(self) -> PostgresDsn:
        """
        Construct the database URL from individual settings.

        Returns:
            PostgresDsn: Validated database URL for SQLAlchemy

        Example:
            url = settings.database_url
            engine = create_engine(str(url))
        """
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @model_validator(mode="after")
    def validate_pool_settings(self) -> "DatabaseSettings":
        """
        Validate database pool configuration.

        Ensures that pool sizes are valid and compatible with each other.

        Returns:
            DatabaseSettings: The validated settings instance

        Raises:
            ValueError: If pool settings are invalid
        """
        if self.MIN_POOL_SIZE > self.MAX_POOL_SIZE:
            raise ValueError(
                "Minimum pool size cannot be greater than maximum pool size"
            )
        return self
