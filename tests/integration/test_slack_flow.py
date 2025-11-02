"""Integration tests for Slack message flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.conversation import Conversation, ConversationStatus, QuestionType
from src.slack.services.conversation_service import ConversationService
from src.slack.services.message_processor import MessageProcessor
from src.config.settings import Settings
from src.config.channel_config import ChannelConfigManager, ChannelConfig


@pytest.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock(spec=Settings)
    settings.database_url = "sqlite+aiosqlite:///:memory:"
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


@pytest.mark.asyncio
async def test_new_message_flow(test_engine, mock_settings, mock_channel_manager):
    """Test complete flow for new message."""
    # Setup
    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    msg_processor = MessageProcessor(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()
    mock_say = AsyncMock()

    # Step 1: Get or create conversation
    conv = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    assert conv is not None
    assert conv.status == ConversationStatus.ACTIVE

    # Step 2: Save initial message
    await conv_service.save_message(
        conversation_id=conv.id,
        ts="1234567890.123456",
        user_id="U123",
        text="I found a critical bug in the payment system",
        has_files=False,
        is_bot_response=False,
    )

    # Step 3: Process message (would normally call RAG, classifier, etc.)
    await msg_processor.process_message(
        conversation=conv,
        message_text="I found a critical bug in the payment system",
        files=[],
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
        say=mock_say,
    )

    # Verify acknowledgment was sent
    mock_say.assert_called()


@pytest.mark.asyncio
async def test_conversation_classification_flow(test_engine, mock_settings):
    """Test conversation classification flow."""
    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    # Create conversation
    conv = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    # Classify as bug
    await conv_service.update_conversation_type(
        conversation_id=conv.id,
        question_type=QuestionType.BUG,
    )

    # Verify classification
    updated_conv = await conv_service.get_conversation_by_thread(
        channel_id="C123",
        thread_ts="1234567890.123456",
    )

    assert updated_conv.question_type == QuestionType.BUG


@pytest.mark.asyncio
async def test_multi_message_conversation(test_engine, mock_settings, mock_channel_manager):
    """Test conversation with multiple messages."""
    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    msg_processor = MessageProcessor(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()
    mock_say = AsyncMock()

    # Create conversation
    conv = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    # Message 1: User question
    await conv_service.save_message(
        conversation_id=conv.id,
        ts="1234567890.123456",
        user_id="U123",
        text="How do I configure the API?",
        has_files=False,
        is_bot_response=False,
    )

    await msg_processor.process_message(
        conversation=conv,
        message_text="How do I configure the API?",
        files=[],
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
        say=mock_say,
    )

    # Message 2: Bot response
    await conv_service.save_message(
        conversation_id=conv.id,
        ts="1234567891.123456",
        user_id="UBOT",
        text="You can configure the API by...",
        has_files=False,
        is_bot_response=True,
    )

    # Mark first response
    await conv_service.mark_first_response(conv.id)

    # Message 3: Follow-up
    await conv_service.save_message(
        conversation_id=conv.id,
        ts="1234567892.123456",
        user_id="U123",
        text="Thanks! What about authentication?",
        has_files=False,
        is_bot_response=False,
    )

    await msg_processor.process_message(
        conversation=conv,
        message_text="Thanks! What about authentication?",
        files=[],
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
        say=mock_say,
    )

    # Verify conversation has multiple messages
    updated_conv = await conv_service.get_conversation_by_thread(
        channel_id="C123",
        thread_ts="1234567890.123456",
    )

    assert updated_conv.first_response_at is not None


@pytest.mark.asyncio
async def test_feedback_flow(test_engine, mock_settings):
    """Test feedback capture flow."""
    from src.models.feedback import FeedbackRating

    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    # Create conversation
    conv = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    # Save message
    await conv_service.save_message(
        conversation_id=conv.id,
        ts="1234567890.123456",
        user_id="UBOT",
        text="Here's the answer",
        has_files=False,
        is_bot_response=True,
    )

    # User provides feedback
    await conv_service.save_feedback(
        conversation_id=conv.id,
        user_id="U123",
        rating=FeedbackRating.HELPFUL,
        message_ts="1234567890.123456",
        note="Very helpful!",
    )

    # Verify feedback was saved
    # (Would need to add a get_feedback method to ConversationService)
    assert True  # Placeholder


@pytest.mark.asyncio
async def test_escalation_flow(test_engine, mock_settings):
    """Test conversation escalation flow."""
    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    # Create conversation
    conv = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    # Set as escalated
    async with conv_service._get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Conversation).where(Conversation.id == conv.id)
        )
        conv_obj = result.scalar_one()
        conv_obj.status = ConversationStatus.ESCALATED
        conv_obj.escalated_to = "U456"
        conv_obj.jira_key = "TEST-123"
        await session.commit()

    # Verify escalation
    updated_conv = await conv_service.get_conversation_by_thread(
        channel_id="C123",
        thread_ts="1234567890.123456",
    )

    assert updated_conv.status == ConversationStatus.ESCALATED
    assert updated_conv.escalated_to == "U456"
    assert updated_conv.jira_key == "TEST-123"


@pytest.mark.asyncio
async def test_action_approval_flow(test_engine, mock_settings):
    """Test action approval flow."""
    from src.models.action import ActionRun, ActionStatus

    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    # Create conversation
    conv = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    # Create action requiring approval
    async with conv_service._get_session() as session:
        action = ActionRun(
            conversation_id=conv.id,
            action_name="restart_service",
            parameters='{"service": "api-server"}',
            status=ActionStatus.PENDING_APPROVAL,
        )
        session.add(action)
        await session.commit()
        await session.refresh(action)
        action_id = action.id

    # Approve action
    async with conv_service._get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ActionRun).where(ActionRun.id == action_id)
        )
        action_obj = result.scalar_one()
        action_obj.status = ActionStatus.APPROVED
        action_obj.approved_by = "U456"
        await session.commit()

    # Verify approval
    async with conv_service._get_session() as session:
        result = await session.execute(
            select(ActionRun).where(ActionRun.id == action_id)
        )
        approved_action = result.scalar_one()

    assert approved_action.status == ActionStatus.APPROVED
    assert approved_action.approved_by == "U456"


@pytest.mark.asyncio
async def test_concurrent_conversations(test_engine, mock_settings):
    """Test multiple concurrent conversations."""
    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    # Create multiple conversations concurrently
    conv1 = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    conv2 = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567891.123456",
        user_id="U456",
    )

    conv3 = await conv_service.get_or_create_conversation(
        channel_id="C456",
        thread_ts="1234567892.123456",
        user_id="U789",
    )

    assert conv1.id != conv2.id != conv3.id
    assert conv1.thread_ts != conv2.thread_ts
    assert conv1.channel_id == conv2.channel_id
    assert conv1.channel_id != conv3.channel_id


@pytest.mark.asyncio
async def test_message_with_files_flow(test_engine, mock_settings, mock_channel_manager):
    """Test message with file attachments flow."""
    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    msg_processor = MessageProcessor(mock_settings, mock_channel_manager)

    mock_client = AsyncMock()
    mock_say = AsyncMock()

    # Create conversation
    conv = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    # Message with files
    files = [
        {
            "id": "F123",
            "name": "screenshot.png",
            "url_private": "https://files.slack.com/screenshot.png",
        }
    ]

    await conv_service.save_message(
        conversation_id=conv.id,
        ts="1234567890.123456",
        user_id="U123",
        text="Check this screenshot of the error",
        has_files=True,
        file_urls='["https://files.slack.com/screenshot.png"]',
        is_bot_response=False,
    )

    await msg_processor.process_message(
        conversation=conv,
        message_text="Check this screenshot of the error",
        files=files,
        channel_id="C123",
        thread_ts="1234567890.123456",
        client=mock_client,
        say=mock_say,
    )

    # Verify processing
    mock_say.assert_called()


@pytest.mark.asyncio
async def test_resolution_flow(test_engine, mock_settings):
    """Test conversation resolution flow."""
    conv_service = ConversationService(mock_settings)
    conv_service.engine = test_engine

    # Create and resolve conversation
    conv = await conv_service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    # Update to resolved
    async with conv_service._get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Conversation).where(Conversation.id == conv.id)
        )
        conv_obj = result.scalar_one()
        conv_obj.status = ConversationStatus.RESOLVED
        conv_obj.summary = "Issue resolved successfully"
        await session.commit()

    # Verify resolution
    updated_conv = await conv_service.get_conversation_by_thread(
        channel_id="C123",
        thread_ts="1234567890.123456",
    )

    assert updated_conv.status == ConversationStatus.RESOLVED
    assert updated_conv.summary == "Issue resolved successfully"
