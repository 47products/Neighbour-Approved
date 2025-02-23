"""
Unit tests for the config module in the Neighbour Approved application.

This module tests:
- DatabaseSettings: Database-specific pydantic settings for 
  credentials, ports, pool sizes, etc.
- Ensures that the database_url property is correct
- Validates that pool settings throw a ValueError if invalid

Typical usage example:
    pytest tests/unit/test_database_config.py

Dependencies:
    - pytest
    - pydantic
    - The config module under test
"""

import pytest
from pydantic import ValidationError
from app.db.config import DatabaseSettings, SecretStr


def test_database_settings_valid():
    """
    Test that DatabaseSettings can be constructed with valid parameters
    and that database_url is computed correctly.
    """
    settings = DatabaseSettings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD=SecretStr("secret"),
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="testdb",
        MIN_POOL_SIZE=5,
        MAX_POOL_SIZE=10,
        POOL_RECYCLE_SECONDS=900,
    )

    assert settings.POSTGRES_USER == "testuser"
    assert settings.POSTGRES_PASSWORD.get_secret_value() == "secret"
    assert settings.POSTGRES_HOST == "localhost"
    assert settings.POSTGRES_PORT == 5432
    assert settings.POSTGRES_DB == "testdb"
    assert settings.MIN_POOL_SIZE == 5
    assert settings.MAX_POOL_SIZE == 10
    assert settings.POOL_RECYCLE_SECONDS == 900

    # Check database_url property
    url = settings.database_url
    # pydantic's PostgresDsn normalizes the URL, but let's check the essential bits
    assert str(url) == "postgresql://testuser:secret@localhost:5432/testdb"


def test_database_settings_min_pool_greater_than_max_raises():
    """
    Test that a ValueError is raised when MIN_POOL_SIZE > MAX_POOL_SIZE.
    """
    with pytest.raises(ValueError, match="Minimum pool size cannot be greater"):
        DatabaseSettings(
            POSTGRES_USER="testuser",
            POSTGRES_PASSWORD=SecretStr("secret"),
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5432,
            POSTGRES_DB="testdb",
            MIN_POOL_SIZE=20,
            MAX_POOL_SIZE=10,
        )


def test_database_settings_defaults():
    """
    Test that DatabaseSettings assigns default port and pool sizes if not specified.
    """
    settings = DatabaseSettings(
        POSTGRES_USER="defaultuser",
        POSTGRES_PASSWORD=SecretStr("defaultpass"),
        POSTGRES_HOST="127.0.0.1",
        POSTGRES_DB="defaults_testdb",
    )

    # Defaults
    assert settings.POSTGRES_PORT == 5432
    assert settings.MIN_POOL_SIZE == 5
    assert settings.MAX_POOL_SIZE == 20
    assert settings.POOL_RECYCLE_SECONDS == 1800
    # Confirm the URL builds
    assert "127.0.0.1:5432" in str(settings.database_url)
