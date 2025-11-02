"""Tests for application settings."""

import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError

from src.config.settings import Settings, get_settings


def test_settings_defaults():
    """Test default settings values."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
    }, clear=True):
        settings = Settings()

        assert settings.app_version == "0.1.0"
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.llm_provider == "openai"
        assert settings.llm_temperature == 0.1
        assert settings.embeddings_dimension == 1536


def test_settings_from_env():
    """Test settings loaded from environment variables."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-custom",
        "SLACK_APP_TOKEN": "xapp-custom",
        "SLACK_SIGNING_SECRET": "custom-secret",
        "ENVIRONMENT": "production",
        "LOG_LEVEL": "DEBUG",
        "LLM_PROVIDER": "anthropic",
        "LLM_MODEL": "claude-3",
        "DATABASE_URL": "postgresql://test",
    }, clear=True):
        settings = Settings()

        assert settings.environment == "production"
        assert settings.log_level == "DEBUG"
        assert settings.llm_provider == "anthropic"
        assert settings.llm_model == "claude-3"
        assert settings.database_url == "postgresql://test"


def test_settings_required_fields():
    """Test that required fields raise validation errors."""
    with pytest.raises(ValidationError):
        Settings()


def test_settings_validation_llm_temperature():
    """Test LLM temperature validation."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
        "LLM_TEMPERATURE": "3.0",  # Invalid, should be <= 2.0
    }, clear=True):
        with pytest.raises(ValidationError):
            Settings()


def test_settings_validation_rate_limit():
    """Test rate limit validation."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
        "RATE_LIMIT_PER_USER": "0",  # Invalid, should be >= 1
    }, clear=True):
        with pytest.raises(ValidationError):
            Settings()


def test_is_development():
    """Test is_development property."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
        "ENVIRONMENT": "development",
    }, clear=True):
        settings = Settings()
        assert settings.is_development is True
        assert settings.is_production is False


def test_is_production():
    """Test is_production property."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
        "ENVIRONMENT": "production",
    }, clear=True):
        settings = Settings()
        assert settings.is_production is True
        assert settings.is_development is False


def test_get_settings_cached():
    """Test that get_settings returns cached instance."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
    }, clear=True):
        settings1 = get_settings()
        settings2 = get_settings()

        # Should return same instance
        assert settings1 is settings2


def test_secret_fields():
    """Test that secret fields are properly handled."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
        "OPENAI_API_KEY": "sk-test-key",
    }, clear=True):
        settings = Settings()

        # Should have SecretStr type
        assert hasattr(settings.slack_bot_token, "get_secret_value")
        assert settings.slack_bot_token.get_secret_value() == "xoxb-test"
        assert settings.openai_api_key.get_secret_value() == "sk-test-key"


def test_optional_integrations():
    """Test optional integration settings."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_USERNAME": "test@example.com",
        "SMTP_HOST": "smtp.test.com",
    }, clear=True):
        settings = Settings()

        assert settings.jira_url == "https://test.atlassian.net"
        assert settings.jira_username == "test@example.com"
        assert settings.smtp_host == "smtp.test.com"


def test_default_sla_values():
    """Test default SLA values."""
    with patch.dict("os.environ", {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "SLACK_SIGNING_SECRET": "secret",
    }, clear=True):
        settings = Settings()

        assert settings.default_sla_minutes == 120
        assert settings.default_first_response_minutes == 15
        assert settings.enable_pii_redaction is True
        assert settings.enable_action_approval is True
