"""
Unit tests for the core configuration service.

This module contains tests for the centralised configuration service,
verifying that it correctly loads and provides access to core application
settings from environment variables and .env files.
"""

from unittest.mock import patch
import pytest

from app.core.configuration.config import get_settings, Settings, _load_env_files


class TestConfigService:
    """Tests for the core configuration service."""

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """Set up environment variables for testing."""
        # Set required environment variables for tests
        monkeypatch.setenv("APP_NAME", "Test App")
        monkeypatch.setenv("VERSION", "0.1.0")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        monkeypatch.setenv("API_BASE_URL", "/api/v1")
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("LOG_LEVEL", "INFO")
        monkeypatch.setenv("LOG_FORMAT", "standard")
        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.setenv("DEBUG", "false")

        # Clear the lru_cache before each test
        get_settings.cache_clear()

        yield

        # Clear the lru_cache after each test
        get_settings.cache_clear()

    def test_environment_variables_loaded(self):
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

    def test_environment_override(self, monkeypatch):
        """Test that environment variables override existing settings."""
        # Override some environment variables
        monkeypatch.setenv("APP_NAME", "Custom App Name")
        monkeypatch.setenv("VERSION", "1.2.3")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DEBUG", "true")

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

    def test_environment_validation(self, monkeypatch):
        """Test validation of environment setting."""
        # First remove the fixture-set environment variable
        monkeypatch.delenv("ENVIRONMENT")
        # Then set an invalid one
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

    def test_log_level_validation(self, monkeypatch):
        """Test validation of log level setting."""
        # First remove the fixture-set environment variable
        monkeypatch.delenv("LOG_LEVEL")
        # Then set an invalid one
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

    def test_log_format_validation(self, monkeypatch):
        """Test validation of log format setting."""
        # First remove the fixture-set environment variable
        monkeypatch.delenv("LOG_FORMAT")
        # Then set an invalid one
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

    def test_empty_secret_key(self, monkeypatch):
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
