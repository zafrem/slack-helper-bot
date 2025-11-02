"""Action execution models."""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.conversation import Conversation


class ActionStatus(str, Enum):
    """Status of an action."""

    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionRun(Base):
    """Action run model representing an executed action."""

    __tablename__ = "action_runs"

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    parameters: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    status: Mapped[ActionStatus] = mapped_column(
        default=ActionStatus.PENDING_APPROVAL,
        nullable=False,
        index=True,
    )

    approved_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    approved_at: Mapped[str | None] = mapped_column(nullable=True)

    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array

    started_at: Mapped[str | None] = mapped_column(nullable=True)
    completed_at: Mapped[str | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)

    # Relationship
    conversation: Mapped["Conversation"] = relationship(back_populates="actions")

    def __repr__(self) -> str:
        return f"<ActionRun(id={self.id}, name={self.action_name}, status={self.status})>"
