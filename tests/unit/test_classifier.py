"""Tests for question classifier."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.classifier.question_classifier import QuestionClassifier
from src.config.settings import Settings
from src.models.conversation import QuestionType


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.llm_provider = "openai"
    settings.llm_model = "gpt-4-turbo-preview"
    settings.openai_api_key = MagicMock()
    settings.openai_api_key.get_secret_value.return_value = "test-key"
    return settings


@pytest.mark.asyncio
async def test_classifier_bug_detection(mock_settings, monkeypatch):
    """Test bug detection."""
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "bug"
    mock_client.chat.completions.create.return_value = mock_response

    classifier = QuestionClassifier(mock_settings)
    classifier.client = mock_client

    result = await classifier.classify("The app crashes when I click the button")

    assert result == QuestionType.BUG
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_classifier_how_to_detection(mock_settings, monkeypatch):
    """Test how-to question detection."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "how_to"
    mock_client.chat.completions.create.return_value = mock_response

    classifier = QuestionClassifier(mock_settings)
    classifier.client = mock_client

    result = await classifier.classify("How do I deploy to production?")

    assert result == QuestionType.HOW_TO


@pytest.mark.asyncio
async def test_classifier_fallback_to_other(mock_settings):
    """Test fallback to OTHER on error."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    classifier = QuestionClassifier(mock_settings)
    classifier.client = mock_client

    result = await classifier.classify("Some random text")

    assert result == QuestionType.OTHER
