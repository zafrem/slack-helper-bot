"""Message processing service."""

from typing import Any

import structlog

from src.config.channel_config import ChannelConfigManager
from src.config.settings import Settings
from src.models.conversation import Conversation

logger = structlog.get_logger(__name__)


class MessageProcessor:
    """Service for processing incoming messages."""

    def __init__(
        self,
        settings: Settings,
        channel_manager: ChannelConfigManager,
    ) -> None:
        """Initialize message processor.

        Args:
            settings: Application settings
            channel_manager: Channel configuration manager
        """
        self.settings = settings
        self.channel_manager = channel_manager

    async def process_message(
        self,
        conversation: Conversation,
        message_text: str,
        files: list[dict[str, Any]],
        channel_id: str,
        thread_ts: str,
        client: Any,
        say: callable,
    ) -> None:
        """Process an incoming message.

        Args:
            conversation: Conversation instance
            message_text: Message text
            files: File attachments
            channel_id: Channel ID
            thread_ts: Thread timestamp
            client: Slack client
            say: Function to send messages
        """
        logger.info(
            "Processing message",
            conversation_id=conversation.id,
            channel_id=channel_id,
        )

        # Get channel config
        channel_config = self.channel_manager.get_channel_config(channel_id)
        if not channel_config:
            logger.warning("Channel config not found", channel_id=channel_id)
            return

        try:
            # TODO: Implement full message processing pipeline:
            # 1. Extract text from images (if any)
            # 2. Classify the question type
            # 3. Generate summary using template
            # 4. Request user confirmation
            # 5. If confirmed, generate RAG answer or execute action
            # 6. Post response in thread

            # For now, send a simple acknowledgment
            await say(
                text=f"I received your message and I'm working on it! (Channel: {channel_config.name})",
                thread_ts=thread_ts,
            )

            logger.info(
                "Message processing complete",
                conversation_id=conversation.id,
            )

        except Exception as e:
            logger.exception(
                "Error in message processing",
                conversation_id=conversation.id,
                error=str(e),
            )
            raise
