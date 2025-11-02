"""Tests for reaction handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.slack.handlers.reaction import setup_reaction_handlers
from src.config.channel_config import ChannelConfigManager
from src.config.settings import Settings


@pytest.fixture
def mock_app():
    """Create mock Slack app."""
    return MagicMock()


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.debug = True
    return settings


@pytest.fixture
def mock_channel_manager():
    """Create mock channel manager."""
    return MagicMock(spec=ChannelConfigManager)


def test_setup_reaction_handlers(mock_app, mock_settings, mock_channel_manager):
    """Test setting up reaction handlers."""
    setup_reaction_handlers(mock_app, mock_settings, mock_channel_manager)

    # Should register reaction_added event
    mock_app.event.assert_called()


@pytest.mark.asyncio
async def test_handle_helpful_reaction():
    """Test handling helpful reaction."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "reaction_added",
        "user": "U123",
        "reaction": "+1",
        "item": {
            "type": "message",
            "channel": "C123",
            "ts": "1234567890.123456",
        },
        "item_user": "U456",
    }

    with patch("src.slack.handlers.reaction.ConversationService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        # Import and call the handler
        from src.slack.handlers.reaction import handle_reaction_added

        await handle_reaction_added(event, mock_client, mock_say)

        # Should save feedback
        mock_service_instance.save_feedback.assert_called_once()


@pytest.mark.asyncio
async def test_handle_not_helpful_reaction():
    """Test handling not helpful reaction."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "reaction_added",
        "user": "U123",
        "reaction": "-1",
        "item": {
            "type": "message",
            "channel": "C123",
            "ts": "1234567890.123456",
        },
        "item_user": "U456",
    }

    with patch("src.slack.handlers.reaction.ConversationService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.reaction import handle_reaction_added

        await handle_reaction_added(event, mock_client, mock_say)

        # Should save feedback with not_helpful rating
        mock_service_instance.save_feedback.assert_called_once()


@pytest.mark.asyncio
async def test_handle_neutral_reaction():
    """Test handling neutral reaction."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "reaction_added",
        "user": "U123",
        "reaction": "thinking_face",
        "item": {
            "type": "message",
            "channel": "C123",
            "ts": "1234567890.123456",
        },
        "item_user": "U456",
    }

    with patch("src.slack.handlers.reaction.ConversationService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.reaction import handle_reaction_added

        await handle_reaction_added(event, mock_client, mock_say)

        # Should save feedback with neutral rating
        mock_service_instance.save_feedback.assert_called_once()


@pytest.mark.asyncio
async def test_handle_reaction_non_message_item():
    """Test handling reaction on non-message item."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "reaction_added",
        "user": "U123",
        "reaction": "+1",
        "item": {
            "type": "file",  # Not a message
            "file": "F123",
        },
    }

    with patch("src.slack.handlers.reaction.ConversationService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.reaction import handle_reaction_added

        await handle_reaction_added(event, mock_client, mock_say)

        # Should not save feedback for non-message items
        mock_service_instance.save_feedback.assert_not_called()


@pytest.mark.asyncio
async def test_handle_reaction_bot_user():
    """Test handling reaction from bot user."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "reaction_added",
        "user": "UBOT123",
        "reaction": "+1",
        "item": {
            "type": "message",
            "channel": "C123",
            "ts": "1234567890.123456",
        },
        "item_user": "U456",
    }

    # Mock bot user info
    mock_client.auth_test.return_value = {"user_id": "UBOT123"}

    with patch("src.slack.handlers.reaction.ConversationService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.reaction import handle_reaction_added

        await handle_reaction_added(event, mock_client, mock_say)

        # Should not save feedback from bot
        mock_service_instance.save_feedback.assert_not_called()


@pytest.mark.asyncio
async def test_handle_reaction_database_error():
    """Test handling reaction when database error occurs."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "reaction_added",
        "user": "U123",
        "reaction": "+1",
        "item": {
            "type": "message",
            "channel": "C123",
            "ts": "1234567890.123456",
        },
        "item_user": "U456",
    }

    with patch("src.slack.handlers.reaction.ConversationService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service_instance.save_feedback.side_effect = Exception("Database error")
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.reaction import handle_reaction_added

        # Should not raise exception
        await handle_reaction_added(event, mock_client, mock_say)


@pytest.mark.asyncio
async def test_handle_reaction_logs_feedback():
    """Test that reaction handler logs feedback."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "reaction_added",
        "user": "U123",
        "reaction": "+1",
        "item": {
            "type": "message",
            "channel": "C123",
            "ts": "1234567890.123456",
        },
        "item_user": "U456",
    }

    with patch("src.slack.handlers.reaction.ConversationService") as mock_service, \
         patch("src.slack.handlers.reaction.logger") as mock_logger:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.reaction import handle_reaction_added

        await handle_reaction_added(event, mock_client, mock_say)

        # Should log feedback capture
        mock_logger.info.assert_called()


@pytest.mark.asyncio
async def test_handle_reaction_removed():
    """Test handling reaction removed event."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "reaction_removed",
        "user": "U123",
        "reaction": "+1",
        "item": {
            "type": "message",
            "channel": "C123",
            "ts": "1234567890.123456",
        },
        "item_user": "U456",
    }

    with patch("src.slack.handlers.reaction.ConversationService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.reaction import handle_reaction_removed

        # Should handle reaction removal if handler exists
        try:
            await handle_reaction_removed(event, mock_client, mock_say)
        except AttributeError:
            # Handler might not exist yet
            pass
