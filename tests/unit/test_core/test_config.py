"""
Unit tests for the Settings configuration module.

This module tests all aspects of the `config.py` module, including:
- Default settings initialization
- Validation errors for incorrect settings
- Proper database URL generation
- Correct caching of settings instance

Typical usage example:
    pytest tests/unit/test_core/test_config.py
"""

import os
from unittest.mock import patch
import pytest
from pydantic import ValidationError
from app.core.config import Settings, get_settings


@patch.dict(os.environ, {"DEBUG": "False"})
def test_default_settings():
    """
    Test that default settings are correctly initialized.

    This test ensures that the default values of the settings are correctly set
    as per the `Settings` class definition.
    """
    settings = Settings()
    assert settings.APPLICATION_NAME == "Neighbour Approved"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is False
    assert settings.API_PREFIX == "/api"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.LOG_FORMAT == "standard"
    assert settings.LOG_PATH == "logs"
    assert settings.ENABLE_REQUEST_LOGGING is True
    assert settings.ENABLE_SQL_LOGGING is False
    assert settings.ENABLE_SQL_ECHO is False
    assert settings.POSTGRES_PORT == 5432


def test_invalid_environment():
    """
    Test that an invalid environment value raises a validation error.

    This test verifies that attempting to initialize `Settings` with an
    unsupported environment value results in a `ValidationError`.
    """
    with pytest.raises(ValidationError, match="Environment must be one of"):
        Settings(ENVIRONMENT="invalid_env")


def test_invalid_log_level():
    """
    Test that an invalid log level raises a validation error.

    This test ensures that only valid logging levels are allowed and any
    invalid value triggers a `ValidationError`.
    """
    with pytest.raises(ValidationError, match="Log level must be one of"):
        Settings(LOG_LEVEL="INVALID")


def test_invalid_log_format():
    """
    Test that an invalid log format raises a validation error.

    This test confirms that only `json` or `standard` log formats are allowed,
    and any other value raises a `ValidationError`.
    """
    with pytest.raises(ValidationError, match="Log format must be one of"):
        Settings(LOG_FORMAT="invalid_format")


def test_database_url():
    """
    Test that the database URL is correctly generated.

    This test verifies that the `database_url` property constructs the correct
    PostgreSQL connection string from the provided settings.
    """
    settings = Settings(
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_pass",
        POSTGRES_HOST="localhost",
        POSTGRES_DB="test_db",
    )
    expected_url = "postgresql://test_user:test_pass@localhost:5432/test_db"

    # Convert PostgresDsn object to string before asserting
    assert str(settings.database_url) == expected_url


def test_get_settings_caching():
    """
    Test that get_settings function returns a cached instance.

    This test ensures that `get_settings()` returns the same instance of `Settings`
    across multiple calls due to the `lru_cache` decorator.
    """
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
