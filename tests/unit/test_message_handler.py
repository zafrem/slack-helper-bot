"""Tests for message handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.slack.handlers.message import setup_message_handlers
from src.config.channel_config import ChannelConfigManager, ChannelConfig
from src.config.settings import Settings
from src.models.conversation import Conversation, ConversationStatus


@pytest.fixture
def mock_app():
    """Create mock Slack app."""
    return MagicMock()


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.debug = True
    settings.slack_bot_token = MagicMock()
    settings.slack_bot_token.get_secret_value.return_value = "xoxb-test"
    return settings


@pytest.fixture
def mock_channel_manager():
    """Create mock channel manager."""
    manager = MagicMock(spec=ChannelConfigManager)
    config = ChannelConfig(
        channel_id="C123",
        name="test-channel",
        rag_index="test-index",
        enabled=True,
    )
    manager.get_channel_config.return_value = config
    manager.is_channel_enabled.return_value = True
    return manager


@pytest.fixture
def mock_conversation():
    """Create mock conversation."""
    return Conversation(
        id=1,
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )


def test_setup_message_handlers(mock_app, mock_settings, mock_channel_manager):
    """Test setting up message handlers."""
    setup_message_handlers(mock_app, mock_settings, mock_channel_manager)

    # Should register message event
    mock_app.event.assert_called()


@pytest.mark.asyncio
async def test_handle_message_basic(mock_conversation):
    """Test handling basic message."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    # Mock bot user
    mock_client.auth_test.return_value = {"user_id": "UBOT"}

    event = {
        "type": "message",
        "user": "U123",
        "text": "Hello, I need help",
        "channel": "C123",
        "ts": "1234567890.123456",
    }

    with patch("src.slack.handlers.message.ConversationService") as mock_conv_service, \
         patch("src.slack.handlers.message.MessageProcessor") as mock_processor:

        mock_conv_instance = AsyncMock()
        mock_conv_instance.get_or_create_conversation.return_value = mock_conversation
        mock_conv_service.return_value = mock_conv_instance

        mock_proc_instance = AsyncMock()
        mock_processor.return_value = mock_proc_instance

        from src.slack.handlers.message import handle_message

        await handle_message(event, mock_client, mock_say)

        # Should create conversation
        mock_conv_instance.get_or_create_conversation.assert_called_once()

        # Should process message
        mock_proc_instance.process_message.assert_called_once()

        # Should add acknowledgment reaction
        mock_client.reactions_add.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_with_thread():
    """Test handling message in thread."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()
    mock_client.auth_test.return_value = {"user_id": "UBOT"}

    event = {
        "type": "message",
        "user": "U123",
        "text": "Follow-up question",
        "channel": "C123",
        "ts": "1234567891.123456",
        "thread_ts": "1234567890.123456",  # In thread
    }

    mock_conversation = Conversation(
        id=1,
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )

    with patch("src.slack.handlers.message.ConversationService") as mock_conv_service, \
         patch("src.slack.handlers.message.MessageProcessor") as mock_processor:

        mock_conv_instance = AsyncMock()
        mock_conv_instance.get_or_create_conversation.return_value = mock_conversation
        mock_conv_service.return_value = mock_conv_instance

        mock_proc_instance = AsyncMock()
        mock_processor.return_value = mock_proc_instance

        from src.slack.handlers.message import handle_message

        await handle_message(event, mock_client, mock_say)

        # Should use thread_ts for conversation lookup
        call_args = mock_conv_instance.get_or_create_conversation.call_args
        assert call_args[1]["thread_ts"] == "1234567890.123456"


@pytest.mark.asyncio
async def test_handle_message_with_files():
    """Test handling message with file attachments."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()
    mock_client.auth_test.return_value = {"user_id": "UBOT"}

    event = {
        "type": "message",
        "user": "U123",
        "text": "Check this screenshot",
        "channel": "C123",
        "ts": "1234567890.123456",
        "files": [
            {
                "id": "F123",
                "name": "screenshot.png",
                "url_private": "https://files.slack.com/screenshot.png",
            }
        ],
    }

    mock_conversation = Conversation(
        id=1,
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )

    with patch("src.slack.handlers.message.ConversationService") as mock_conv_service, \
         patch("src.slack.handlers.message.MessageProcessor") as mock_processor:

        mock_conv_instance = AsyncMock()
        mock_conv_instance.get_or_create_conversation.return_value = mock_conversation
        mock_conv_service.return_value = mock_conv_instance

        mock_proc_instance = AsyncMock()
        mock_processor.return_value = mock_proc_instance

        from src.slack.handlers.message import handle_message

        await handle_message(event, mock_client, mock_say)

        # Should process message with files
        call_args = mock_proc_instance.process_message.call_args
        assert "files" in call_args[1]
        assert len(call_args[1]["files"]) == 1


@pytest.mark.asyncio
async def test_handle_message_bot_message():
    """Test that bot messages are ignored."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()
    mock_client.auth_test.return_value = {"user_id": "UBOT"}

    event = {
        "type": "message",
        "user": "UBOT",  # Bot user
        "text": "Bot response",
        "channel": "C123",
        "ts": "1234567890.123456",
    }

    with patch("src.slack.handlers.message.ConversationService") as mock_conv_service:
        mock_conv_instance = AsyncMock()
        mock_conv_service.return_value = mock_conv_instance

        from src.slack.handlers.message import handle_message

        await handle_message(event, mock_client, mock_say)

        # Should not create conversation for bot messages
        mock_conv_instance.get_or_create_conversation.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_subtype():
    """Test that messages with subtypes are ignored."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()

    event = {
        "type": "message",
        "subtype": "message_changed",  # Has subtype
        "user": "U123",
        "text": "Edited message",
        "channel": "C123",
        "ts": "1234567890.123456",
    }

    with patch("src.slack.handlers.message.ConversationService") as mock_conv_service:
        mock_conv_instance = AsyncMock()
        mock_conv_service.return_value = mock_conv_instance

        from src.slack.handlers.message import handle_message

        await handle_message(event, mock_client, mock_say)

        # Should not process messages with subtypes
        mock_conv_instance.get_or_create_conversation.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_disabled_channel():
    """Test handling message in disabled channel."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()
    mock_client.auth_test.return_value = {"user_id": "UBOT"}

    event = {
        "type": "message",
        "user": "U123",
        "text": "Help needed",
        "channel": "C999",  # Disabled channel
        "ts": "1234567890.123456",
    }

    with patch("src.slack.handlers.message.ChannelConfigManager") as mock_config:
        mock_config_instance = MagicMock()
        mock_config_instance.is_channel_enabled.return_value = False
        mock_config.return_value = mock_config_instance

        with patch("src.slack.handlers.message.ConversationService") as mock_conv_service:
            mock_conv_instance = AsyncMock()
            mock_conv_service.return_value = mock_conv_instance

            from src.slack.handlers.message import handle_message

            await handle_message(event, mock_client, mock_say)

            # Should not process message
            mock_conv_instance.get_or_create_conversation.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_error():
    """Test message handling with error."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()
    mock_client.auth_test.return_value = {"user_id": "UBOT"}

    event = {
        "type": "message",
        "user": "U123",
        "text": "Help needed",
        "channel": "C123",
        "ts": "1234567890.123456",
    }

    with patch("src.slack.handlers.message.ConversationService") as mock_conv_service:
        mock_conv_instance = AsyncMock()
        mock_conv_instance.get_or_create_conversation.side_effect = Exception("Database error")
        mock_conv_service.return_value = mock_conv_instance

        from src.slack.handlers.message import handle_message

        # Should not raise exception
        await handle_message(event, mock_client, mock_say)


@pytest.mark.asyncio
async def test_handle_message_logs_processing():
    """Test that message handling logs information."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()
    mock_client.auth_test.return_value = {"user_id": "UBOT"}

    event = {
        "type": "message",
        "user": "U123",
        "text": "Help needed",
        "channel": "C123",
        "ts": "1234567890.123456",
    }

    mock_conversation = Conversation(
        id=1,
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )

    with patch("src.slack.handlers.message.ConversationService") as mock_conv_service, \
         patch("src.slack.handlers.message.MessageProcessor") as mock_processor, \
         patch("src.slack.handlers.message.logger") as mock_logger:

        mock_conv_instance = AsyncMock()
        mock_conv_instance.get_or_create_conversation.return_value = mock_conversation
        mock_conv_service.return_value = mock_conv_instance

        mock_proc_instance = AsyncMock()
        mock_processor.return_value = mock_proc_instance

        from src.slack.handlers.message import handle_message

        await handle_message(event, mock_client, mock_say)

        # Should log message processing
        assert mock_logger.info.called or mock_logger.debug.called


@pytest.mark.asyncio
async def test_handle_message_updates_metrics():
    """Test that message handling updates metrics."""
    mock_client = AsyncMock()
    mock_say = AsyncMock()
    mock_client.auth_test.return_value = {"user_id": "UBOT"}

    event = {
        "type": "message",
        "user": "U123",
        "text": "Help needed",
        "channel": "C123",
        "ts": "1234567890.123456",
    }

    mock_conversation = Conversation(
        id=1,
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )

    with patch("src.slack.handlers.message.ConversationService") as mock_conv_service, \
         patch("src.slack.handlers.message.MessageProcessor") as mock_processor, \
         patch("src.slack.handlers.message.metrics") as mock_metrics:

        mock_conv_instance = AsyncMock()
        mock_conv_instance.get_or_create_conversation.return_value = mock_conversation
        mock_conv_service.return_value = mock_conv_instance

        mock_proc_instance = AsyncMock()
        mock_processor.return_value = mock_proc_instance

        from src.slack.handlers.message import handle_message

        await handle_message(event, mock_client, mock_say)

        # Should record metrics
        assert mock_metrics.messages_received.inc.called or \
               mock_metrics.messages_processed.inc.called
