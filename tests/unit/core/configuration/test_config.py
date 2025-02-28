# pylint: disable=unused-argument, duplicate-code, function-redefined
"""
Unit tests for the core configuration service.

This module contains tests for the centralised configuration service,
verifying that it correctly loads and provides access to core application
settings from environment variables and .env files.
"""

import os
from unittest.mock import patch
import pytest

from app.core.configuration.config import (
    _check_missing_environment_variables,
    get_settings,
    Settings,
    _load_env_files,
)


class TestConfigService:
    """Tests for the core configuration service."""

    def test_environment_variables_loaded(self, mock_env_vars):
        """Test that environment variables are correctly loaded into settings."""
        settings = get_settings()

        assert settings.app_name == "Test App"
        assert settings.version == "0.1.0"
        assert settings.database_url == "sqlite:///:memory:"
        assert settings.api_base_url == "/api/v1"
        assert settings.secret_key == "test-secret"
        assert settings.log_level == "INFO"
        assert settings.log_format == "standard"
        assert settings.environment == "testing"
        assert settings.debug is False

    def test_environment_override(self, monkeypatch, mock_env_vars):
        """Test that environment variables override existing settings."""
        # Override some environment variables
        monkeypatch.setenv("APP_NAME", "Custom App Name")
        monkeypatch.setenv("VERSION", "1.2.3")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DEBUG", "true")

        # Clear the cache to ensure settings are reloaded
        get_settings.cache_clear()

        # Get settings and verify overrides
        settings = get_settings()
        assert settings.app_name == "Custom App Name"
        assert settings.version == "1.2.3"
        assert settings.log_level == "DEBUG"
        assert settings.debug is True

    def test_load_env_files(self):
        """Test that environment variables are loaded from .env files."""
        with patch(
            "app.core.configuration.config.Path.exists", return_value=True
        ), patch("app.core.configuration.config.load_dotenv") as mock_load_dotenv:

            _load_env_files()

            # Check that load_dotenv was called twice (for env-specific and default files)
            assert mock_load_dotenv.call_count == 2

    def test_environment_validation(self, monkeypatch, mock_env_vars):
        """Test validation of environment setting."""
        # Override the fixture-set environment variable
        monkeypatch.setenv("ENVIRONMENT", "invalid")

        # Create a settings instance directly to test validation
        with pytest.raises(ValueError) as exc_info:
            # We need to create the Settings instance directly to trigger validation
            Settings(
                app_name="Test App",
                version="0.1.0",
                database_url="sqlite:///:memory:",
                api_base_url="/api/v1",
                secret_key="test-secret",
                log_level="INFO",
                log_format="standard",
                environment="invalid",
                debug=False,
            )

        assert "Environment must be one of" in str(exc_info.value)

    def test_log_level_validation(self, monkeypatch, mock_env_vars):
        """Test validation of log level setting."""
        # Override the fixture-set log level
        monkeypatch.setenv("LOG_LEVEL", "invalid")

        # Create a settings instance directly to test validation
        with pytest.raises(ValueError) as exc_info:
            Settings(
                app_name="Test App",
                version="0.1.0",
                database_url="sqlite:///:memory:",
                api_base_url="/api/v1",
                secret_key="test-secret",
                log_level="invalid",
                log_format="standard",
                environment="testing",
                debug=False,
            )

        assert "Log level must be one of" in str(exc_info.value)

    def test_log_format_validation(self, monkeypatch, mock_env_vars):
        """Test validation of log format setting."""
        # Override the fixture-set log format
        monkeypatch.setenv("LOG_FORMAT", "invalid")

        # Create a settings instance directly to test validation
        with pytest.raises(ValueError) as exc_info:
            Settings(
                app_name="Test App",
                version="0.1.0",
                database_url="sqlite:///:memory:",
                api_base_url="/api/v1",
                secret_key="test-secret",
                log_level="INFO",
                log_format="invalid",
                environment="testing",
                debug=False,
            )

        assert "Log format must be one of" in str(exc_info.value)

    def test_empty_secret_key(self, monkeypatch, mock_env_vars):
        """Test error handling when secret key is empty."""
        # Set an empty secret key
        monkeypatch.setenv("SECRET_KEY", "")

        # This should work but we'll catch the error in get_settings
        with patch("app.core.configuration.config.Settings") as mock_settings:
            mock_settings.side_effect = Exception("Validation error")

            with pytest.raises(ValueError) as exc_info:
                get_settings()

            assert "SECRET_KEY environment variable cannot be empty" in str(
                exc_info.value
            )

        # Test loading .env files when the environment-specific file doesn't exist.
        with patch(
            "app.core.configuration.config.Path.exists",
            side_effect=[
                False,
                True,
            ],  # Env-specific file doesn't exist, default file does
        ), patch("app.core.configuration.config.load_dotenv") as mock_load_dotenv:

            _load_env_files()

            # Should only load the default .env file, not the missing environment-specific one
            assert mock_load_dotenv.call_count == 1

    def test_check_missing_environment_variables_none_missing_direct(self, monkeypatch):
        """Test checking for missing environment variables when none are missing."""
        # Set all required variables
        required_fields = [
            "app_name",
            "version",
            "database_url",
            "api_base_url",
            "secret_key",
            "log_level",
            "log_format",
            "environment",
            "debug",
        ]

        for field in required_fields:
            monkeypatch.setenv(field, "test_value")

        # Call the function and verify results
        missing_vars = _check_missing_environment_variables()
        assert not missing_vars

    def test_check_missing_environment_variables_with_patched_environ(
        self, monkeypatch
    ):
        """Test checking for missing environment variables when some are missing."""
        # Clear all environment variables first
        for var in os.environ:
            monkeypatch.delenv(var, raising=False)

        # Set only some of the required variables
        monkeypatch.setenv("APP_NAME", "test_app")
        monkeypatch.setenv("VERSION", "0.1.0")

        # Call the function
        missing_vars = _check_missing_environment_variables()

        # Verify that missing variables are correctly identified
        assert "database_url" in missing_vars
        assert "api_base_url" in missing_vars
        assert "secret_key" in missing_vars
        assert "app_name" not in missing_vars
        assert "version" not in missing_vars

    def test_check_missing_environment_variables_none_missing_direct(self, monkeypatch):
        """Test checking for missing environment variables when none are missing."""
        # Set all required variables
        required_fields = [
            "app_name",
            "version",
            "database_url",
            "api_base_url",
            "secret_key",
            "log_level",
            "log_format",
            "environment",
            "debug",
        ]

        for field in required_fields:
            monkeypatch.setenv(field, "test_value")

        # Call the function and verify results
        missing_vars = _check_missing_environment_variables()
        assert not missing_vars

    def test_check_missing_environment_variables_with_patched_environ(
        self, monkeypatch
    ):
        """Test checking for missing environment variables when some are missing."""
        # The issue is with environment variable clearing. We need to be more specific
        # because the function checks for both upper and lowercase versions.

        # First, clear the LRU cache to ensure we get a fresh settings object
        get_settings.cache_clear()

        # Patch the _check_missing_environment_variables function directly
        with patch(
            "app.core.configuration.config.os.environ",
            {"APP_NAME": "test_app", "VERSION": "0.1.0"},
        ):
            # Call the function with our controlled environment
            missing_vars = _check_missing_environment_variables()

            # Now verify the results
            assert "database_url" in missing_vars
            assert "api_base_url" in missing_vars
            assert "secret_key" in missing_vars
            assert "app_name" not in missing_vars
            assert "version" not in missing_vars

    def test_get_settings_with_empty_secret_key(self, monkeypatch):
        """Test that get_settings raises an appropriate error with empty SECRET_KEY."""
        # Clear the lru_cache
        get_settings.cache_clear()

        # Set empty SECRET_KEY
        monkeypatch.setenv("SECRET_KEY", "")

        # Mock _load_env_files to avoid trying to load files
        with patch("app.core.configuration.config._load_env_files"):
            with pytest.raises(ValueError) as exc_info:
                get_settings()

            # Verify the error message is about the empty SECRET_KEY
            assert "SECRET_KEY environment variable cannot be empty" in str(
                exc_info.value
            )

    def test_get_settings_with_validation_error(self, monkeypatch):
        """Test that get_settings handles ValidationError properly."""
        # Clear the lru_cache
        get_settings.cache_clear()

        # Set up environment to make validation fail
        monkeypatch.setenv("SECRET_KEY", "not_empty")
        monkeypatch.setenv("LOG_LEVEL", "INVALID")  # This should fail validation

        # We expect a ValidationError due to invalid LOG_LEVEL
        with patch("app.core.configuration.config._load_env_files"):
            with pytest.raises(ValueError) as exc_info:
                get_settings()

            # Verify the error mentions log level
            assert "Log level must be one of" in str(exc_info.value)

    def test_get_settings_with_exception(self):
        """Test that get_settings converts a generic exception to ValueError."""
        # Clear the lru_cache
        get_settings.cache_clear()

        # Mock to cause a general exception in the settings creation
        with patch("app.core.configuration.config._load_env_files"), patch(
            "app.core.configuration.config.Settings",
            side_effect=Exception("General error"),
        ):

            with pytest.raises(ValueError) as exc_info:
                get_settings()

            # Verify the error message format
            assert "Configuration error: General error" in str(exc_info.value)

    def test_get_settings_general_exception(self, monkeypatch):
        """Test error handling in get_settings for generic exceptions."""
        # Clear the lru_cache
        get_settings.cache_clear()

        # Set up environment
        monkeypatch.setenv("SECRET_KEY", "not_empty")

        # Mock Settings to raise a generic exception
        with patch("app.core.configuration.config._load_env_files"), patch(
            "app.core.configuration.config.Settings",
            side_effect=Exception("General error"),
        ):

            with pytest.raises(ValueError) as exc_info:
                get_settings()

            # Verify the error message format
            assert "Configuration error: General error" in str(exc_info.value)
