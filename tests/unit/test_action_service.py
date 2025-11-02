"""Tests for action service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.slack.services.action_service import ActionService
from src.config.channel_config import ChannelConfigManager
from src.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    return settings


@pytest.fixture
def mock_channel_manager():
    """Create mock channel manager."""
    return MagicMock(spec=ChannelConfigManager)


@pytest.mark.asyncio
async def test_action_service_initialization(mock_settings, mock_channel_manager):
    """Test action service initialization."""
    service = ActionService(mock_settings, mock_channel_manager)

    assert service.settings == mock_settings
    assert service.channel_manager == mock_channel_manager


@pytest.mark.asyncio
async def test_handle_summary_approval(mock_settings, mock_channel_manager):
    """Test handling summary approval."""
    service = ActionService(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()

    await service.handle_summary_approval(
        user_id="U123",
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
    )

    # Should post message
    mock_client.chat_postMessage.assert_called_once()
    call_args = mock_client.chat_postMessage.call_args
    assert call_args[1]["channel"] == "C123"
    assert call_args[1]["thread_ts"] == "1234567890.123456"


@pytest.mark.asyncio
async def test_handle_action_approval(mock_settings, mock_channel_manager):
    """Test handling action approval."""
    service = ActionService(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()

    await service.handle_action_approval(
        action_id=1,
        user_id="U123",
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
    )

    # Should post approval message
    mock_client.chat_postMessage.assert_called_once()
    call_args = mock_client.chat_postMessage.call_args
    assert "U123" in call_args[1]["text"]


@pytest.mark.asyncio
async def test_handle_summary_approval_logs(mock_settings, mock_channel_manager):
    """Test that summary approval logs information."""
    service = ActionService(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()

    with patch("src.slack.services.action_service.logger") as mock_logger:
        await service.handle_summary_approval(
            user_id="U123",
            channel_id="C123",
            thread_ts="1234567890.123456",
            client=mock_client,
        )

        mock_logger.info.assert_called()


@pytest.mark.asyncio
async def test_handle_action_approval_logs(mock_settings, mock_channel_manager):
    """Test that action approval logs information."""
    service = ActionService(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()

    with patch("src.slack.services.action_service.logger") as mock_logger:
        await service.handle_action_approval(
            action_id=1,
            user_id="U123",
            channel_id="C123",
            thread_ts="1234567890.123456",
            client=mock_client,
        )

        mock_logger.info.assert_called()
