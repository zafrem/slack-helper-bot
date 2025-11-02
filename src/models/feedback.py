"""Feedback models."""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.conversation import Conversation


class FeedbackRating(str, Enum):
    """Feedback rating."""

    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    NEUTRAL = "neutral"


class Feedback(Base):
    """Feedback model for user ratings."""

    __tablename__ = "feedback"

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rating: Mapped[FeedbackRating] = mapped_column(nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # What was rated (message ts)
    message_ts: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationship
    conversation: Mapped["Conversation"] = relationship(back_populates="feedback")

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, rating={self.rating}, user_id={self.user_id})>"
