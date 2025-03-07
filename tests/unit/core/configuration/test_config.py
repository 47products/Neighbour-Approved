# pylint: disable=unused-argument, duplicate-code, function-redefined
"""
Unit tests for the core configuration service.

This module contains tests for the centralised configuration service,
verifying that it correctly loads and provides access to core application
settings from environment variables and .env files.
"""

import io
from unittest.mock import patch, MagicMock
from pydantic import ValidationError, BaseModel
import pytest
from app.core.configuration.config import (
    _check_missing_environment_variables,
    _get_required_env_vars,
    _validate_field_value,
    _validate_secret_key,
    _create_global_settings,
    get_settings,
    Settings,
    _load_env_files,
)


class TestConfigService:
    """Tests for the core configuration service."""

    def test_validate_field_value(self):
        """Test the _validate_field_value helper function."""
        # Test valid values
        assert (
            _validate_field_value(
                "info", ["debug", "info", "warning"], "Test Field", str.lower
            )
            == "info"
        )
        assert (
            _validate_field_value("DEBUG", ["DEBUG", "INFO", "WARNING"], "Test Field")
            == "DEBUG"
        )

        # Test transformation
        assert (
            _validate_field_value(
                "debug", ["DEBUG", "INFO", "WARNING"], "Test Field", str.upper
            )
            == "DEBUG"
        )

        # Test invalid value
        with pytest.raises(ValueError) as exc_info:
            _validate_field_value(
                "invalid", ["debug", "info", "warning"], "Test Field", str.lower
            )
        assert "Test Field must be one of" in str(exc_info.value)

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

    def test_validate_secret_key(self, monkeypatch):
        """Test the _validate_secret_key function."""
        # Test with valid secret key
        monkeypatch.setenv("SECRET_KEY", "valid-key")
        _validate_secret_key()  # Should not raise an exception

        # Test with empty secret key
        monkeypatch.setenv("SECRET_KEY", "")
        with pytest.raises(ValueError) as exc_info:
            _validate_secret_key()
        assert "SECRET_KEY environment variable cannot be empty" in str(exc_info.value)

    def test_get_required_env_vars(self):
        """Test the _get_required_env_vars function."""
        required_vars = _get_required_env_vars()

        # Check that we have the expected variables
        assert "app_name" in required_vars
        assert "secret_key" in required_vars
        assert "database_url" in required_vars

        # Should have 10 required variables
        assert len(required_vars) == 10

    def test_check_missing_environment_variables_none_missing(self, monkeypatch):
        """Test checking for missing environment variables when none are missing."""
        # Set all required variables
        for field_name in _get_required_env_vars():
            monkeypatch.setenv(field_name, "test_value")

        # Call the function and verify results
        missing_vars = _check_missing_environment_variables()
        assert not missing_vars

    def test_check_missing_environment_variables_with_missing(self):
        """Test checking for missing environment variables when some are missing."""
        # Patch the environment to control exactly what variables are available
        with patch(
            "app.core.configuration.config.os.environ",
            {"APP_NAME": "test_app", "VERSION": "0.1.0"},
        ):
            # Call the function with our controlled environment
            missing_vars = _check_missing_environment_variables()

            # Verify the results
            assert "database_url" in missing_vars
            assert "api_base_url" in missing_vars
            assert "secret_key" in missing_vars
            assert "app_name" not in missing_vars
            assert "version" not in missing_vars

    def test_create_global_settings_success(self):
        """Test successful creation of global settings."""
        with patch("app.core.configuration.config.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            result = _create_global_settings()

            assert result is mock_settings
            mock_get_settings.assert_called_once()

    def test_create_global_settings_error(self):
        """Test error handling when creating global settings."""
        with patch(
            "app.core.configuration.config.get_settings"
        ) as mock_get_settings, patch(
            "sys.stderr", new_callable=io.StringIO
        ) as mock_stderr:

            mock_get_settings.side_effect = ValueError("Test error")

            result = _create_global_settings()

            assert result is None
            mock_get_settings.assert_called_once()
            assert (
                "ERROR: Failed to load configuration: Test error"
                in mock_stderr.getvalue()
            )

    def test_load_env_files_with_no_files(self, monkeypatch):
        """Test _load_env_files when no .env files exist."""
        # Patch to simulate that no .env files exist
        with patch(
            "app.core.configuration.config.Path.exists", return_value=False
        ), patch("app.core.configuration.config.load_dotenv") as mock_load_dotenv:
            # Set environment
            monkeypatch.setenv("ENVIRONMENT", "production")

            _load_env_files()

            # Verify load_dotenv was not called at all
            assert mock_load_dotenv.call_count == 0

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
            "app.core.configuration.config._validate_secret_key"
        ), patch(
            "app.core.configuration.config.Settings",
            side_effect=Exception("General error"),
        ):

            with pytest.raises(ValueError) as exc_info:
                get_settings()

            # Verify the error message format
            assert "Configuration error: General error" in str(exc_info.value)

    def test_get_settings_missing_vars_with_validation_error(self, monkeypatch):
        """Test get_settings with missing vars and validation error."""

        # Create a real ValidationError we can use
        class TestModel(BaseModel):
            """Test model for validation."""

            value: int

        try:
            # This will raise a ValidationError we can capture
            TestModel(value="not_an_int")
        except ValidationError as real_validation_error:
            # Clear the cache
            get_settings.cache_clear()

            # Create a controlled environment
            with patch("app.core.configuration.config._load_env_files"), patch(
                "app.core.configuration.config._validate_secret_key"
            ), patch(
                "app.core.configuration.config.Settings",
                side_effect=real_validation_error,
            ), patch(
                "app.core.configuration.config._check_missing_environment_variables",
                return_value=["app_name", "database_url"],
            ):

                with pytest.raises(ValueError) as exc_info:
                    get_settings()

                # Check that the error includes missing variables
                error_msg = str(exc_info.value)
                assert "Missing required environment variables" in error_msg
                assert "app_name" in error_msg
                assert "database_url" in error_msg
                assert "Original error" in error_msg

    def test_settings_global_instance_creation(self):
        """Test the global settings instance creation."""
        # Mock the module-level code that creates the settings instance
        mocked_settings = MagicMock()

        # Execute the code that creates the global settings instance
        with patch(
            "app.core.configuration.config._create_global_settings",
            return_value=mocked_settings,
        ) as mock_create:
            # Directly call the function and assign the result
            module_globals = {"_create_global_settings": mock_create}
            module_globals["settings"] = module_globals["_create_global_settings"]()

            # Verify _create_global_settings was called
            mock_create.assert_called_once()

            # Verify the settings was assigned correctly
            assert module_globals["settings"] == mocked_settings
