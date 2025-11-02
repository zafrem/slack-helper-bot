"""Service for managing conversations and messages."""

import json
from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.base import AsyncSessionLocal
from src.models.conversation import Conversation, ConversationStatus, Message, QuestionType
from src.models.feedback import Feedback, FeedbackRating

logger = structlog.get_logger(__name__)


class ConversationService:
    """Service for conversation and message operations."""

    async def get_or_create_conversation(
        self,
        channel_id: str,
        thread_ts: str,
        user_id: str,
        sla_minutes: int = 120,
        first_response_minutes: int = 15,
    ) -> Conversation:
        """Get existing conversation or create a new one.

        Args:
            channel_id: Slack channel ID
            thread_ts: Thread timestamp
            user_id: User ID
            sla_minutes: SLA deadline in minutes
            first_response_minutes: First response deadline in minutes

        Returns:
            Conversation instance
        """
        async with AsyncSessionLocal() as session:
            # Try to find existing conversation
            result = await session.execute(
                select(Conversation)
                .where(Conversation.thread_ts == thread_ts)
                .options(selectinload(Conversation.messages))
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                return conversation

            # Create new conversation
            now = datetime.utcnow()
            conversation = Conversation(
                channel_id=channel_id,
                thread_ts=thread_ts,
                user_id=user_id,
                status=ConversationStatus.ACTIVE,
                sla_deadline=now + timedelta(minutes=sla_minutes),
                first_response_deadline=now + timedelta(minutes=first_response_minutes),
            )

            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)

            logger.info(
                "Conversation created",
                conversation_id=conversation.id,
                thread_ts=thread_ts,
            )

            return conversation

    async def save_message(
        self,
        conversation_id: int,
        ts: str,
        user_id: str,
        text: str,
        files: list[dict[str, Any]] | None = None,
        is_bot_response: bool = False,
        ocr_text: str | None = None,
    ) -> Message:
        """Save a message to the database.

        Args:
            conversation_id: Conversation ID
            ts: Message timestamp
            user_id: User ID
            text: Message text
            files: File attachments
            is_bot_response: Whether this is a bot response
            ocr_text: Extracted text from images

        Returns:
            Message instance
        """
        async with AsyncSessionLocal() as session:
            # Check if message already exists
            result = await session.execute(
                select(Message).where(Message.ts == ts)
            )
            existing_message = result.scalar_one_or_none()

            if existing_message:
                return existing_message

            # Prepare file data
            has_files = bool(files)
            file_urls = json.dumps([f.get("url_private") for f in files]) if files else None

            message = Message(
                conversation_id=conversation_id,
                ts=ts,
                user_id=user_id,
                text=text,
                has_files=has_files,
                file_urls=file_urls,
                is_bot_response=is_bot_response,
                ocr_text=ocr_text,
            )

            session.add(message)
            await session.commit()
            await session.refresh(message)

            logger.debug(
                "Message saved",
                message_id=message.id,
                conversation_id=conversation_id,
                has_files=has_files,
            )

            return message

    async def update_conversation_type(
        self,
        conversation_id: int,
        question_type: QuestionType,
    ) -> None:
        """Update conversation question type.

        Args:
            conversation_id: Conversation ID
            question_type: Question type
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.question_type = question_type
                await session.commit()

                logger.info(
                    "Conversation type updated",
                    conversation_id=conversation_id,
                    question_type=question_type.value,
                )

    async def update_conversation_summary(
        self,
        conversation_id: int,
        summary: str,
        confirmed: bool = False,
    ) -> None:
        """Update conversation summary.

        Args:
            conversation_id: Conversation ID
            summary: Summary text
            confirmed: Whether summary is confirmed
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.summary = summary
                conversation.summary_confirmed = confirmed
                await session.commit()

                logger.info(
                    "Conversation summary updated",
                    conversation_id=conversation_id,
                    confirmed=confirmed,
                )

    async def mark_first_response(self, conversation_id: int) -> None:
        """Mark first response time for a conversation.

        Args:
            conversation_id: Conversation ID
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation and not conversation.first_response_at:
                conversation.first_response_at = datetime.utcnow()
                await session.commit()

                logger.info(
                    "First response marked",
                    conversation_id=conversation_id,
                )

    async def find_conversation_by_message(self, message_ts: str) -> Conversation | None:
        """Find conversation by message timestamp.

        Args:
            message_ts: Message timestamp

        Returns:
            Conversation instance or None
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Conversation)
                .join(Message)
                .where(Message.ts == message_ts)
            )
            return result.scalar_one_or_none()

    async def save_feedback(
        self,
        conversation_id: int,
        user_id: str,
        rating: FeedbackRating,
        message_ts: str | None = None,
        note: str | None = None,
    ) -> Feedback:
        """Save user feedback.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            rating: Feedback rating
            message_ts: Message timestamp
            note: Optional feedback note

        Returns:
            Feedback instance
        """
        async with AsyncSessionLocal() as session:
            feedback = Feedback(
                conversation_id=conversation_id,
                user_id=user_id,
                rating=rating,
                message_ts=message_ts,
                note=note,
            )

            session.add(feedback)
            await session.commit()
            await session.refresh(feedback)

            logger.info(
                "Feedback saved",
                feedback_id=feedback.id,
                conversation_id=conversation_id,
                rating=rating.value,
            )

            return feedback
