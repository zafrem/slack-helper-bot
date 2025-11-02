"""Tests for message processor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.slack.services.message_processor import MessageProcessor
from src.config.channel_config import ChannelConfigManager, ChannelConfig
from src.config.settings import Settings
from src.models.conversation import Conversation, ConversationStatus


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.debug = True
    return settings


@pytest.fixture
def mock_channel_manager():
    """Create mock channel manager."""
    manager = MagicMock(spec=ChannelConfigManager)

    # Mock channel config
    config = ChannelConfig(
        channel_id="C123",
        name="test-channel",
        rag_index="test-index",
        enabled=True,
    )
    manager.get_channel_config.return_value = config

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


@pytest.mark.asyncio
async def test_message_processor_initialization(mock_settings, mock_channel_manager):
    """Test message processor initialization."""
    processor = MessageProcessor(mock_settings, mock_channel_manager)

    assert processor.settings == mock_settings
    assert processor.channel_manager == mock_channel_manager


@pytest.mark.asyncio
async def test_process_message_basic(
    mock_settings,
    mock_channel_manager,
    mock_conversation,
):
    """Test basic message processing."""
    processor = MessageProcessor(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()
    mock_say = AsyncMock()

    await processor.process_message(
        conversation=mock_conversation,
        message_text="Test message",
        files=[],
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
        say=mock_say,
    )

    # Should send acknowledgment
    mock_say.assert_called_once()
    call_args = mock_say.call_args
    assert "thread_ts" in call_args[1]


@pytest.mark.asyncio
async def test_process_message_no_channel_config(
    mock_settings,
    mock_channel_manager,
    mock_conversation,
):
    """Test message processing with no channel config."""
    # Return None for channel config
    mock_channel_manager.get_channel_config.return_value = None

    processor = MessageProcessor(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()
    mock_say = AsyncMock()

    await processor.process_message(
        conversation=mock_conversation,
        message_text="Test message",
        files=[],
        channel_id="C999",
        thread_ts="1234567890.123456",
        client=mock_client,
        say=mock_say,
    )

    # Should not send message
    mock_say.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_with_files(
    mock_settings,
    mock_channel_manager,
    mock_conversation,
):
    """Test message processing with file attachments."""
    processor = MessageProcessor(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()
    mock_say = AsyncMock()

    files = [
        {
            "id": "F123",
            "name": "test.png",
            "url_private": "https://files.slack.com/test.png",
        }
    ]

    await processor.process_message(
        conversation=mock_conversation,
        message_text="Check this image",
        files=files,
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
        say=mock_say,
    )

    mock_say.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_error_handling(
    mock_settings,
    mock_channel_manager,
    mock_conversation,
):
    """Test message processing error handling."""
    processor = MessageProcessor(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()
    mock_say = AsyncMock()
    mock_say.side_effect = Exception("Slack API error")

    # Should not raise exception
    await processor.process_message(
        conversation=mock_conversation,
        message_text="Test message",
        files=[],
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
        say=mock_say,
    )


@pytest.mark.asyncio
async def test_process_message_logs_info(
    mock_settings,
    mock_channel_manager,
    mock_conversation,
):
    """Test that message processing logs information."""
    processor = MessageProcessor(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()
    mock_say = AsyncMock()

    with patch("src.slack.services.message_processor.logger") as mock_logger:
        await processor.process_message(
            conversation=mock_conversation,
            message_text="Test message",
            files=[],
            channel_id="C123",
            thread_ts="1234567890.123456",
            client=mock_client,
            say=mock_say,
        )

        # Should log processing start and completion
        assert mock_logger.info.called
