"""Integration tests for database operations."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.conversation import Conversation, ConversationStatus, QuestionType, Message
from src.models.action import ActionRun, ActionStatus
from src.models.feedback import Feedback, FeedbackRating
from src.models.audit import AuditEvent
from src.slack.services.conversation_service import ConversationService
from src.config.settings import Settings


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
async def test_session(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_conversation_crud(test_session):
    """Test conversation CRUD operations."""
    # Create
    conv = Conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )
    test_session.add(conv)
    await test_session.commit()
    await test_session.refresh(conv)

    assert conv.id is not None
    assert conv.channel_id == "C123"
    assert conv.status == ConversationStatus.ACTIVE

    # Update
    conv.status = ConversationStatus.RESOLVED
    conv.question_type = QuestionType.BUG
    await test_session.commit()
    await test_session.refresh(conv)

    assert conv.status == ConversationStatus.RESOLVED
    assert conv.question_type == QuestionType.BUG

    # Read
    from sqlalchemy import select
    result = await test_session.execute(
        select(Conversation).where(Conversation.id == conv.id)
    )
    found_conv = result.scalar_one()

    assert found_conv.id == conv.id
    assert found_conv.channel_id == "C123"


@pytest.mark.asyncio
async def test_message_crud(test_session):
    """Test message CRUD operations."""
    # Create conversation first
    conv = Conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )
    test_session.add(conv)
    await test_session.commit()
    await test_session.refresh(conv)

    # Create message
    msg = Message(
        conversation_id=conv.id,
        ts="1234567890.123456",
        user_id="U123",
        text="Test message",
        has_files=False,
        is_bot_response=False,
    )
    test_session.add(msg)
    await test_session.commit()
    await test_session.refresh(msg)

    assert msg.id is not None
    assert msg.conversation_id == conv.id
    assert msg.text == "Test message"

    # Read
    from sqlalchemy import select
    result = await test_session.execute(
        select(Message).where(Message.conversation_id == conv.id)
    )
    messages = result.scalars().all()

    assert len(messages) == 1
    assert messages[0].text == "Test message"


@pytest.mark.asyncio
async def test_action_run_crud(test_session):
    """Test action run CRUD operations."""
    # Create conversation first
    conv = Conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )
    test_session.add(conv)
    await test_session.commit()
    await test_session.refresh(conv)

    # Create action
    action = ActionRun(
        conversation_id=conv.id,
        action_name="restart_service",
        parameters='{"service": "api-server"}',
        status=ActionStatus.PENDING_APPROVAL,
    )
    test_session.add(action)
    await test_session.commit()
    await test_session.refresh(action)

    assert action.id is not None
    assert action.status == ActionStatus.PENDING_APPROVAL

    # Update status
    action.status = ActionStatus.APPROVED
    action.approved_by = "U456"
    action.approved_at = datetime.utcnow()
    await test_session.commit()
    await test_session.refresh(action)

    assert action.status == ActionStatus.APPROVED
    assert action.approved_by == "U456"

    # Execute action
    action.status = ActionStatus.RUNNING
    action.executed_at = datetime.utcnow()
    await test_session.commit()

    action.status = ActionStatus.COMPLETED
    action.completed_at = datetime.utcnow()
    action.result = '{"status": "success"}'
    await test_session.commit()
    await test_session.refresh(action)

    assert action.status == ActionStatus.COMPLETED
    assert action.result is not None


@pytest.mark.asyncio
async def test_feedback_crud(test_session):
    """Test feedback CRUD operations."""
    # Create conversation first
    conv = Conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )
    test_session.add(conv)
    await test_session.commit()
    await test_session.refresh(conv)

    # Create feedback
    feedback = Feedback(
        conversation_id=conv.id,
        user_id="U123",
        rating=FeedbackRating.HELPFUL,
        message_ts="1234567890.123456",
        note="Very helpful!",
    )
    test_session.add(feedback)
    await test_session.commit()
    await test_session.refresh(feedback)

    assert feedback.id is not None
    assert feedback.rating == FeedbackRating.HELPFUL

    # Read
    from sqlalchemy import select
    result = await test_session.execute(
        select(Feedback).where(Feedback.conversation_id == conv.id)
    )
    feedbacks = result.scalars().all()

    assert len(feedbacks) == 1
    assert feedbacks[0].rating == FeedbackRating.HELPFUL


@pytest.mark.asyncio
async def test_audit_event_crud(test_session):
    """Test audit event CRUD operations."""
    # Create audit event
    event = AuditEvent(
        event_type="message_received",
        actor_id="U123",
        channel_id="C123",
        thread_ts="1234567890.123456",
        payload='{"text": "test"}',
        payload_hash="abc123",
        result="success",
    )
    test_session.add(event)
    await test_session.commit()
    await test_session.refresh(event)

    assert event.id is not None
    assert event.event_type == "message_received"
    assert event.result == "success"

    # Read
    from sqlalchemy import select
    result = await test_session.execute(
        select(AuditEvent).where(AuditEvent.actor_id == "U123")
    )
    events = result.scalars().all()

    assert len(events) == 1
    assert events[0].event_type == "message_received"


@pytest.mark.asyncio
async def test_conversation_with_messages(test_session):
    """Test conversation with multiple messages."""
    # Create conversation
    conv = Conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )
    test_session.add(conv)
    await test_session.commit()
    await test_session.refresh(conv)

    # Add multiple messages
    messages = [
        Message(
            conversation_id=conv.id,
            ts="1234567890.123456",
            user_id="U123",
            text="Initial question",
            has_files=False,
            is_bot_response=False,
        ),
        Message(
            conversation_id=conv.id,
            ts="1234567891.123456",
            user_id="UBOT",
            text="Bot response",
            has_files=False,
            is_bot_response=True,
        ),
        Message(
            conversation_id=conv.id,
            ts="1234567892.123456",
            user_id="U123",
            text="Follow-up question",
            has_files=False,
            is_bot_response=False,
        ),
    ]

    for msg in messages:
        test_session.add(msg)
    await test_session.commit()

    # Read all messages
    from sqlalchemy import select
    result = await test_session.execute(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.ts)
    )
    saved_messages = result.scalars().all()

    assert len(saved_messages) == 3
    assert saved_messages[0].text == "Initial question"
    assert saved_messages[1].is_bot_response is True
    assert saved_messages[2].text == "Follow-up question"


@pytest.mark.asyncio
async def test_conversation_lifecycle(test_session):
    """Test full conversation lifecycle."""
    # 1. Start conversation
    conv = Conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )
    test_session.add(conv)
    await test_session.commit()
    await test_session.refresh(conv)

    assert conv.status == ConversationStatus.ACTIVE

    # 2. Classify question
    conv.question_type = QuestionType.BUG
    await test_session.commit()

    # 3. Generate summary
    conv.summary = "User reported a critical bug"
    conv.status = ConversationStatus.WAITING_APPROVAL
    await test_session.commit()

    assert conv.status == ConversationStatus.WAITING_APPROVAL

    # 4. Approve and resolve
    conv.status = ConversationStatus.RESOLVED
    conv.resolved_at = datetime.utcnow()
    await test_session.commit()

    assert conv.status == ConversationStatus.RESOLVED
    assert conv.resolved_at is not None


@pytest.mark.asyncio
async def test_conversation_service_integration(test_engine):
    """Test ConversationService with real database."""
    from unittest.mock import MagicMock

    # Create mock settings
    settings = MagicMock(spec=Settings)
    settings.database_url = "sqlite+aiosqlite:///:memory:"

    # Create service with test engine
    service = ConversationService(settings)
    service.engine = test_engine

    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Test get or create
    conv = await service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    assert conv is not None
    assert conv.id is not None
    assert conv.channel_id == "C123"

    # Test get existing
    conv2 = await service.get_or_create_conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
    )

    assert conv2.id == conv.id


@pytest.mark.asyncio
async def test_multiple_conversations_same_channel(test_session):
    """Test multiple conversations in same channel."""
    # Create multiple conversations
    conversations = [
        Conversation(
            channel_id="C123",
            thread_ts="1234567890.123456",
            user_id="U123",
            status=ConversationStatus.ACTIVE,
        ),
        Conversation(
            channel_id="C123",
            thread_ts="1234567891.123456",
            user_id="U456",
            status=ConversationStatus.ACTIVE,
        ),
        Conversation(
            channel_id="C123",
            thread_ts="1234567892.123456",
            user_id="U789",
            status=ConversationStatus.RESOLVED,
        ),
    ]

    for conv in conversations:
        test_session.add(conv)
    await test_session.commit()

    # Query conversations by channel
    from sqlalchemy import select
    result = await test_session.execute(
        select(Conversation).where(Conversation.channel_id == "C123")
    )
    channel_convs = result.scalars().all()

    assert len(channel_convs) == 3

    # Query active conversations only
    result = await test_session.execute(
        select(Conversation).where(
            Conversation.channel_id == "C123",
            Conversation.status == ConversationStatus.ACTIVE,
        )
    )
    active_convs = result.scalars().all()

    assert len(active_convs) == 2
