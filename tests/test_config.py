"""Tests for the configuration module."""

import os
from unittest.mock import patch

from app.config import ResearchSettings, get_settings


class TestResearchSettings:
    """Test the ResearchSettings configuration class."""

    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        settings = ResearchSettings()

        assert settings.app_name == "plasma-engine-research"
        assert settings.cors_origins == ["http://localhost:3000"]
        assert settings.openai_api_key is None

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            "APP_NAME": "test-research-service",
            "CORS_ORIGINS": "http://localhost:8000,https://app.example.com",
            "OPENAI_API_KEY": "sk-test123"
        }):
            settings = ResearchSettings()

            assert settings.app_name == "test-research-service"
            assert settings.cors_origins == ["http://localhost:8000", "https://app.example.com"]
            assert settings.openai_api_key == "sk-test123"

    def test_cors_origins_single_value(self):
        """Test CORS origins with single value."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://single-origin.com"}):
            settings = ResearchSettings()
            assert settings.cors_origins == ["https://single-origin.com"]

    def test_cors_origins_multiple_values(self):
        """Test CORS origins with multiple comma-separated values."""
        origins = "http://localhost:3000,https://staging.app.com,https://app.com"
        with patch.dict(os.environ, {"CORS_ORIGINS": origins}):
            settings = ResearchSettings()
            assert settings.cors_origins == [
                "http://localhost:3000",
                "https://staging.app.com",
                "https://app.com"
            ]

    def test_extra_fields_ignored(self):
        """Test that extra environment variables are ignored."""
        with patch.dict(os.environ, {"UNKNOWN_SETTING": "should-be-ignored"}):
            # Should not raise an error due to extra="ignore" in model config
            settings = ResearchSettings()
            assert not hasattr(settings, "unknown_setting")


class TestGetSettings:
    """Test the get_settings function and caching behavior."""

    def test_returns_research_settings_instance(self):
        """Test that get_settings returns a ResearchSettings instance."""
        settings = get_settings()
        assert isinstance(settings, ResearchSettings)

    def test_caching_behavior(self):
        """Test that get_settings caches the settings instance."""
        # Clear the cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # Should return the same instance due to @lru_cache
        assert settings1 is settings2

    def test_cache_respects_environment_changes(self):
        """Test that settings cache needs to be cleared for env changes."""
        get_settings.cache_clear()

        with patch.dict(os.environ, {"APP_NAME": "first-name"}):
            settings1 = get_settings()
            assert settings1.app_name == "first-name"

        # Without clearing cache, should still return cached version
        with patch.dict(os.environ, {"APP_NAME": "second-name"}):
            settings2 = get_settings()
            assert settings2.app_name == "first-name"  # Still cached

        # After clearing cache, should pick up new environment
        get_settings.cache_clear()
        with patch.dict(os.environ, {"APP_NAME": "second-name"}):
            settings3 = get_settings()
            assert settings3.app_name == "second-name"

    def test_settings_validation(self):
        """Test that settings validation works correctly."""
        # This would test any Pydantic validators if they were added
        settings = ResearchSettings(
            app_name="valid-name",
            cors_origins=["http://localhost:3000"],
            openai_api_key="sk-valid-key"
        )
        assert settings.app_name == "valid-name"