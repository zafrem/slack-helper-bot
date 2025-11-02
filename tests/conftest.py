"""Pytest configuration and shared fixtures."""

import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

from src.config.settings import Settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)

    # App settings
    settings.app_version = "0.1.0"
    settings.environment = "test"
    settings.debug = True
    settings.log_level = "DEBUG"

    # Slack settings
    settings.slack_bot_token = MagicMock()
    settings.slack_bot_token.get_secret_value.return_value = "xoxb-test-token"
    settings.slack_app_token = MagicMock()
    settings.slack_app_token.get_secret_value.return_value = "xapp-test-token"
    settings.slack_signing_secret = MagicMock()
    settings.slack_signing_secret.get_secret_value.return_value = "test-secret"

    # LLM settings
    settings.llm_provider = "openai"
    settings.llm_model = "gpt-4-turbo-preview"
    settings.openai_api_key = MagicMock()
    settings.openai_api_key.get_secret_value.return_value = "sk-test-key"

    # Database settings
    settings.database_url = "sqlite+aiosqlite:///:memory:"

    # Metrics settings
    settings.metrics_port = 9090

    return settings


@pytest.fixture
def sample_slack_message() -> dict:
    """Create sample Slack message event."""
    return {
        "type": "message",
        "channel": "C123456",
        "user": "U123456",
        "text": "Test message",
        "ts": "1234567890.123456",
        "thread_ts": "1234567890.123456",
    }


@pytest.fixture
def sample_slack_reaction() -> dict:
    """Create sample Slack reaction event."""
    return {
        "type": "reaction_added",
        "user": "U123456",
        "reaction": "+1",
        "item": {
            "type": "message",
            "channel": "C123456",
            "ts": "1234567890.123456",
        },
        "event_ts": "1234567890.123457",
    }


@pytest.fixture
def sample_slack_file() -> dict:
    """Create sample Slack file object."""
    return {
        "id": "F123456",
        "name": "test.png",
        "mimetype": "image/png",
        "url_private": "https://files.slack.com/files-pri/T123-F123/test.png",
        "size": 12345,
    }


# Mark all async tests
def pytest_collection_modifyitems(items):
    """Automatically mark async tests."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
