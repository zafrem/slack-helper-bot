"""Tests for database models."""

import pytest
from datetime import datetime

from src.models.conversation import (
    Conversation,
    ConversationStatus,
    QuestionType,
    Message,
)
from src.models.action import ActionRun, ActionStatus
from src.models.feedback import Feedback, FeedbackRating
from src.models.audit import AuditEvent


def test_conversation_model_creation():
    """Test Conversation model creation."""
    conv = Conversation(
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )

    assert conv.channel_id == "C123"
    assert conv.thread_ts == "1234567890.123456"
    assert conv.user_id == "U123"
    assert conv.status == ConversationStatus.ACTIVE
    assert conv.question_type is None
    assert conv.summary is None


def test_conversation_status_enum():
    """Test ConversationStatus enum values."""
    assert ConversationStatus.ACTIVE.value == "active"
    assert ConversationStatus.WAITING_APPROVAL.value == "waiting_approval"
    assert ConversationStatus.RESOLVED.value == "resolved"
    assert ConversationStatus.ESCALATED.value == "escalated"
    assert ConversationStatus.CLOSED.value == "closed"


def test_question_type_enum():
    """Test QuestionType enum values."""
    assert QuestionType.BUG.value == "bug"
    assert QuestionType.HOW_TO.value == "how_to"
    assert QuestionType.FEATURE_REQUEST.value == "feature_request"
    assert QuestionType.OPS_ACTION.value == "ops_action"
    assert QuestionType.OTHER.value == "other"


def test_message_model_creation():
    """Test Message model creation."""
    msg = Message(
        conversation_id=1,
        ts="1234567890.123456",
        user_id="U123",
        text="Test message",
        has_files=False,
        is_bot_response=False,
    )

    assert msg.conversation_id == 1
    assert msg.ts == "1234567890.123456"
    assert msg.user_id == "U123"
    assert msg.text == "Test message"
    assert msg.has_files is False
    assert msg.is_bot_response is False


def test_message_with_files():
    """Test Message model with file attachments."""
    msg = Message(
        conversation_id=1,
        ts="1234567890.123456",
        user_id="U123",
        text="Check this screenshot",
        has_files=True,
        file_urls='["https://files.slack.com/test.png"]',
        ocr_text="Extracted text from image",
    )

    assert msg.has_files is True
    assert msg.file_urls is not None
    assert msg.ocr_text == "Extracted text from image"


def test_action_run_model_creation():
    """Test ActionRun model creation."""
    action = ActionRun(
        conversation_id=1,
        action_name="restart_service",
        parameters='{"service": "api-server"}',
        status=ActionStatus.PENDING_APPROVAL,
    )

    assert action.conversation_id == 1
    assert action.action_name == "restart_service"
    assert action.parameters == '{"service": "api-server"}'
    assert action.status == ActionStatus.PENDING_APPROVAL


def test_action_status_enum():
    """Test ActionStatus enum values."""
    assert ActionStatus.PENDING_APPROVAL.value == "pending_approval"
    assert ActionStatus.APPROVED.value == "approved"
    assert ActionStatus.REJECTED.value == "rejected"
    assert ActionStatus.RUNNING.value == "running"
    assert ActionStatus.COMPLETED.value == "completed"
    assert ActionStatus.FAILED.value == "failed"
    assert ActionStatus.CANCELLED.value == "cancelled"


def test_feedback_model_creation():
    """Test Feedback model creation."""
    feedback = Feedback(
        conversation_id=1,
        user_id="U123",
        rating=FeedbackRating.HELPFUL,
        message_ts="1234567890.123456",
        note="Very helpful response!",
    )

    assert feedback.conversation_id == 1
    assert feedback.user_id == "U123"
    assert feedback.rating == FeedbackRating.HELPFUL
    assert feedback.message_ts == "1234567890.123456"
    assert feedback.note == "Very helpful response!"


def test_feedback_rating_enum():
    """Test FeedbackRating enum values."""
    assert FeedbackRating.HELPFUL.value == "helpful"
    assert FeedbackRating.NOT_HELPFUL.value == "not_helpful"
    assert FeedbackRating.NEUTRAL.value == "neutral"


def test_audit_event_model_creation():
    """Test AuditEvent model creation."""
    event = AuditEvent(
        event_type="message_received",
        actor_id="U123",
        channel_id="C123",
        thread_ts="1234567890.123456",
        payload='{"text": "test"}',
        payload_hash="abc123",
        result="success",
    )

    assert event.event_type == "message_received"
    assert event.actor_id == "U123"
    assert event.channel_id == "C123"
    assert event.thread_ts == "1234567890.123456"
    assert event.result == "success"


def test_conversation_repr():
    """Test Conversation __repr__ method."""
    conv = Conversation(
        id=1,
        channel_id="C123",
        thread_ts="1234567890.123456",
        user_id="U123",
        status=ConversationStatus.ACTIVE,
    )

    repr_str = repr(conv)
    assert "Conversation" in repr_str
    assert "id=1" in repr_str
    assert "1234567890.123456" in repr_str


def test_message_repr():
    """Test Message __repr__ method."""
    msg = Message(
        id=1,
        conversation_id=1,
        ts="1234567890.123456",
        user_id="U123",
        text="Test",
    )

    repr_str = repr(msg)
    assert "Message" in repr_str
    assert "id=1" in repr_str
    assert "U123" in repr_str


def test_action_run_repr():
    """Test ActionRun __repr__ method."""
    action = ActionRun(
        id=1,
        conversation_id=1,
        action_name="restart_service",
        status=ActionStatus.COMPLETED,
    )

    repr_str = repr(action)
    assert "ActionRun" in repr_str
    assert "restart_service" in repr_str
    assert "completed" in repr_str


def test_feedback_repr():
    """Test Feedback __repr__ method."""
    feedback = Feedback(
        id=1,
        conversation_id=1,
        user_id="U123",
        rating=FeedbackRating.HELPFUL,
    )

    repr_str = repr(feedback)
    assert "Feedback" in repr_str
    assert "helpful" in repr_str


def test_audit_event_repr():
    """Test AuditEvent __repr__ method."""
    event = AuditEvent(
        id=1,
        event_type="test_event",
        actor_id="U123",
    )

    repr_str = repr(event)
    assert "AuditEvent" in repr_str
    assert "test_event" in repr_str
