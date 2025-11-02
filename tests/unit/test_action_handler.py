"""Tests for action handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.slack.handlers.action import setup_action_handlers
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


def test_setup_action_handlers(mock_app, mock_settings, mock_channel_manager):
    """Test setting up action handlers."""
    setup_action_handlers(mock_app, mock_settings, mock_channel_manager)

    # Should register action handlers
    assert mock_app.action.called or mock_app.view.called


@pytest.mark.asyncio
async def test_handle_approve_summary_action():
    """Test handling approve summary action."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "actions": [{"action_id": "approve_summary"}],
        "channel": {"id": "C123"},
        "message": {"ts": "1234567890.123456"},
    }

    with patch("src.slack.handlers.action.ActionService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_approve_summary

        await handle_approve_summary(mock_ack, mock_body, mock_client)

        # Should acknowledge and handle approval
        mock_ack.assert_called_once()
        mock_service_instance.handle_summary_approval.assert_called_once()


@pytest.mark.asyncio
async def test_handle_reject_summary_action():
    """Test handling reject summary action."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "actions": [{"action_id": "reject_summary"}],
        "channel": {"id": "C123"},
        "message": {"ts": "1234567890.123456"},
    }

    with patch("src.slack.handlers.action.ActionService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_reject_summary

        await handle_reject_summary(mock_ack, mock_body, mock_client)

        # Should acknowledge and handle rejection
        mock_ack.assert_called_once()


@pytest.mark.asyncio
async def test_handle_approve_action():
    """Test handling action approval."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "actions": [
            {
                "action_id": "approve_action",
                "value": "1",  # action_id
            }
        ],
        "channel": {"id": "C123"},
        "message": {"ts": "1234567890.123456"},
    }

    with patch("src.slack.handlers.action.ActionService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_approve_action

        await handle_approve_action(mock_ack, mock_body, mock_client)

        # Should acknowledge and handle action approval
        mock_ack.assert_called_once()
        mock_service_instance.handle_action_approval.assert_called_once_with(
            action_id=1,
            user_id="U123",
            channel_id="C123",
            thread_ts="1234567890.123456",
            client=mock_client,
        )


@pytest.mark.asyncio
async def test_handle_reject_action():
    """Test handling action rejection."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "actions": [
            {
                "action_id": "reject_action",
                "value": "1",  # action_id
            }
        ],
        "channel": {"id": "C123"},
        "message": {"ts": "1234567890.123456"},
    }

    with patch("src.slack.handlers.action.ActionService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_reject_action

        await handle_reject_action(mock_ack, mock_body, mock_client)

        # Should acknowledge and handle rejection
        mock_ack.assert_called_once()


@pytest.mark.asyncio
async def test_handle_escalate_action():
    """Test handling escalation action."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "actions": [{"action_id": "escalate"}],
        "channel": {"id": "C123"},
        "message": {"ts": "1234567890.123456", "thread_ts": "1234567890.123456"},
    }

    with patch("src.slack.handlers.action.ConversationService") as mock_conv_service, \
         patch("src.slack.handlers.action.JiraClient") as mock_jira, \
         patch("src.slack.handlers.action.EmailClient") as mock_email:

        mock_conv_instance = AsyncMock()
        mock_conv_service.return_value = mock_conv_instance

        mock_jira_instance = AsyncMock()
        mock_jira_instance.create_issue.return_value = "TEST-123"
        mock_jira.return_value = mock_jira_instance

        mock_email_instance = AsyncMock()
        mock_email_instance.send_escalation.return_value = True
        mock_email.return_value = mock_email_instance

        from src.slack.handlers.action import handle_escalate

        await handle_escalate(mock_ack, mock_body, mock_client)

        # Should acknowledge
        mock_ack.assert_called_once()


@pytest.mark.asyncio
async def test_handle_modal_submission():
    """Test handling modal submission."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "view": {
            "callback_id": "feedback_modal",
            "state": {
                "values": {
                    "feedback_block": {
                        "feedback_input": {
                            "value": "This is helpful feedback"
                        }
                    }
                }
            },
        },
    }

    with patch("src.slack.handlers.action.ConversationService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_feedback_modal

        await handle_feedback_modal(mock_ack, mock_body, mock_client)

        # Should acknowledge modal submission
        mock_ack.assert_called_once()


@pytest.mark.asyncio
async def test_handle_action_error():
    """Test handling action with error."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "actions": [{"action_id": "approve_action", "value": "1"}],
        "channel": {"id": "C123"},
        "message": {"ts": "1234567890.123456"},
    }

    with patch("src.slack.handlers.action.ActionService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service_instance.handle_action_approval.side_effect = Exception("Database error")
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_approve_action

        # Should not raise exception
        await handle_approve_action(mock_ack, mock_body, mock_client)

        # Should still acknowledge
        mock_ack.assert_called_once()


@pytest.mark.asyncio
async def test_handle_action_logs():
    """Test that action handlers log information."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "actions": [{"action_id": "approve_summary"}],
        "channel": {"id": "C123"},
        "message": {"ts": "1234567890.123456"},
    }

    with patch("src.slack.handlers.action.ActionService") as mock_service, \
         patch("src.slack.handlers.action.logger") as mock_logger:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_approve_summary

        await handle_approve_summary(mock_ack, mock_body, mock_client)

        # Should log action handling
        assert mock_logger.info.called or mock_logger.debug.called


@pytest.mark.asyncio
async def test_handle_action_unauthorized_user():
    """Test handling action from unauthorized user."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U999"},  # Unauthorized user
        "actions": [{"action_id": "approve_action", "value": "1"}],
        "channel": {"id": "C123"},
        "message": {"ts": "1234567890.123456"},
    }

    with patch("src.slack.handlers.action.ActionService") as mock_service, \
         patch("src.slack.handlers.action.ChannelConfigManager") as mock_config:

        mock_config_instance = MagicMock()
        mock_config_instance.is_approver.return_value = False
        mock_config.return_value = mock_config_instance

        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_approve_action

        await handle_approve_action(mock_ack, mock_body, mock_client)

        # Should acknowledge but not execute
        mock_ack.assert_called_once()


@pytest.mark.asyncio
async def test_handle_action_missing_fields():
    """Test handling action with missing fields."""
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    mock_body = {
        "user": {"id": "U123"},
        "actions": [{"action_id": "approve_action"}],  # Missing value
        "channel": {"id": "C123"},
    }

    with patch("src.slack.handlers.action.ActionService") as mock_service:
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        from src.slack.handlers.action import handle_approve_action

        # Should not raise exception
        await handle_approve_action(mock_ack, mock_body, mock_client)

        mock_ack.assert_called_once()
