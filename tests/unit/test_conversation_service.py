"""Tests for conversation service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.slack.services.conversation_service import ConversationService
from src.models.conversation import Conversation, ConversationStatus, QuestionType, Message
from src.models.feedback import Feedback, FeedbackRating


@pytest.fixture
def conversation_service():
    """Create conversation service instance."""
    return ConversationService()


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock()
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None
    return session


@pytest.fixture
def sample_conversation():
    """Create sample conversation."""
    return Conversation(
        id=1,
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_get_or_create_conversation_new(conversation_service, mock_session):
    """Test creating a new conversation."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        # Mock query returning None (no existing conversation)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        conv = await conversation_service.get_or_create_conversation(
            channel_id="C123",
            thread_ts="1234567890.123456",
            user_id="U123",
            sla_minutes=120,
            first_response_minutes=15,
        )

        # Verify conversation was added
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called


@pytest.mark.asyncio
async def test_get_or_create_conversation_existing(conversation_service, mock_session, sample_conversation):
    """Test retrieving existing conversation."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        # Mock query returning existing conversation
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        conv = await conversation_service.get_or_create_conversation(
            channel_id="C123",
            thread_ts="1234567890.123456",
            user_id="U123",
        )

        # Verify no new conversation was added
        assert not mock_session.add.called
        assert conv == sample_conversation


@pytest.mark.asyncio
async def test_save_message(conversation_service, mock_session):
    """Test saving a message."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        # Mock query returning None (new message)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        message = await conversation_service.save_message(
            conversation_id=1,
            ts="1234567890.123456",
            user_id="U123",
            text="Test message",
            files=[{"url_private": "https://files.slack.com/test.png"}],
        )

        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called


@pytest.mark.asyncio
async def test_save_message_existing(conversation_service, mock_session):
    """Test saving an existing message (should not duplicate)."""
    existing_message = Message(
        id=1,
        conversation_id=1,
        ts="1234567890.123456",
        user_id="U123",
        text="Test message",
    )

    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_message
        mock_session.execute.return_value = mock_result

        message = await conversation_service.save_message(
            conversation_id=1,
            ts="1234567890.123456",
            user_id="U123",
            text="Test message",
        )

        # Should return existing message without adding
        assert not mock_session.add.called
        assert message == existing_message


@pytest.mark.asyncio
async def test_update_conversation_type(conversation_service, mock_session, sample_conversation):
    """Test updating conversation question type."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        await conversation_service.update_conversation_type(
            conversation_id=1,
            question_type=QuestionType.BUG,
        )

        assert mock_session.commit.called
        assert sample_conversation.question_type == QuestionType.BUG


@pytest.mark.asyncio
async def test_update_conversation_summary(conversation_service, mock_session, sample_conversation):
    """Test updating conversation summary."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        await conversation_service.update_conversation_summary(
            conversation_id=1,
            summary="Test summary",
            confirmed=True,
        )

        assert mock_session.commit.called
        assert sample_conversation.summary == "Test summary"
        assert sample_conversation.summary_confirmed is True


@pytest.mark.asyncio
async def test_mark_first_response(conversation_service, mock_session, sample_conversation):
    """Test marking first response time."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        await conversation_service.mark_first_response(conversation_id=1)

        assert mock_session.commit.called
        assert sample_conversation.first_response_at is not None


@pytest.mark.asyncio
async def test_mark_first_response_already_marked(conversation_service, mock_session, sample_conversation):
    """Test marking first response when already marked."""
    sample_conversation.first_response_at = datetime.utcnow()
    original_time = sample_conversation.first_response_at

    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        await conversation_service.mark_first_response(conversation_id=1)

        # Should not update if already set
        assert sample_conversation.first_response_at == original_time


@pytest.mark.asyncio
async def test_find_conversation_by_message(conversation_service, mock_session, sample_conversation):
    """Test finding conversation by message timestamp."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_conversation
        mock_session.execute.return_value = mock_result

        conv = await conversation_service.find_conversation_by_message(
            message_ts="1234567890.123456"
        )

        assert conv == sample_conversation


@pytest.mark.asyncio
async def test_save_feedback(conversation_service, mock_session):
    """Test saving user feedback."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        feedback = await conversation_service.save_feedback(
            conversation_id=1,
            user_id="U123",
            rating=FeedbackRating.HELPFUL,
            message_ts="1234567890.123456",
            note="Great answer!",
        )

        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called


@pytest.mark.asyncio
async def test_save_feedback_not_helpful(conversation_service, mock_session):
    """Test saving negative feedback."""
    with patch("src.slack.services.conversation_service.AsyncSessionLocal", return_value=mock_session):
        feedback = await conversation_service.save_feedback(
            conversation_id=1,
            user_id="U123",
            rating=FeedbackRating.NOT_HELPFUL,
            message_ts="1234567890.123456",
        )

        assert mock_session.add.called
        assert mock_session.commit.called
