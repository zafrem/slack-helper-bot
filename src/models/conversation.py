"""Conversation and message models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.action import ActionRun
    from src.models.feedback import Feedback


class ConversationStatus(str, Enum):
    """Status of a conversation."""

    ACTIVE = "active"
    WAITING_APPROVAL = "waiting_approval"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class QuestionType(str, Enum):
    """Type of question."""

    BUG = "bug"
    HOW_TO = "how_to"
    FEATURE_REQUEST = "feature_request"
    OPS_ACTION = "ops_action"
    OTHER = "other"


class Conversation(Base):
    """Conversation model representing a Slack thread."""

    __tablename__ = "conversations"

    channel_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    thread_ts: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    question_type: Mapped[QuestionType] = mapped_column(nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(
        default=ConversationStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_confirmed: Mapped[bool] = mapped_column(default=False, nullable=False)

    jira_key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    sla_deadline: Mapped[datetime | None] = mapped_column(nullable=True)
    first_response_deadline: Mapped[datetime | None] = mapped_column(nullable=True)
    first_response_at: Mapped[datetime | None] = mapped_column(nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    rag_index: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    actions: Mapped[list["ActionRun"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, thread_ts={self.thread_ts}, status={self.status})>"


class Message(Base):
    """Message model representing a Slack message."""

    __tablename__ = "messages"

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ts: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    # File attachments
    has_files: Mapped[bool] = mapped_column(default=False, nullable=False)
    file_urls: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Bot response
    is_bot_response: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationship
    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, ts={self.ts}, user_id={self.user_id})>"
