"""Audit event models."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class AuditEvent(Base):
    """Audit event model for tracking all system events."""

    __tablename__ = "audit_events"

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    channel_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    thread_ts: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    payload: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    result: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditEvent(id={self.id}, type={self.event_type}, actor={self.actor_id})>"
