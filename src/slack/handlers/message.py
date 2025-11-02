"""Message event handlers."""

import time
from typing import Any

import structlog
from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError

from src.config.channel_config import ChannelConfigManager
from src.config.settings import Settings
from src.observability.metrics import (
    first_response_time_seconds,
    messages_processed_total,
    messages_received_total,
)
from src.slack.services.conversation_service import ConversationService
from src.slack.services.message_processor import MessageProcessor

logger = structlog.get_logger(__name__)


def register_message_handlers(
    app: AsyncApp,
    settings: Settings,
    channel_manager: ChannelConfigManager,
) -> None:
    """Register message event handlers.

    Args:
        app: Slack app instance
        settings: Application settings
        channel_manager: Channel configuration manager
    """
    conversation_service = ConversationService()
    message_processor = MessageProcessor(settings, channel_manager)

    @app.event("message")
    async def handle_message(event: dict[str, Any], client: Any, say: callable) -> None:
        """Handle incoming messages.

        Args:
            event: Slack event data
            client: Slack client
            say: Function to send messages
        """
        start_time = time.time()

        # Skip bot messages and message changes
        if event.get("subtype") in ["bot_message", "message_changed", "message_deleted"]:
            return

        channel_id = event.get("channel")
        user_id = event.get("user")
        text = event.get("text", "")
        ts = event.get("ts")
        thread_ts = event.get("thread_ts", ts)  # Use message ts if not in a thread

        logger.info(
            "Message received",
            channel_id=channel_id,
            user_id=user_id,
            thread_ts=thread_ts,
            has_files=bool(event.get("files")),
        )

        # Record metric
        messages_received_total.labels(
            channel_id=channel_id,
            message_type="user_message",
        ).inc()

        # Check if channel is configured
        if not channel_manager.is_channel_enabled(channel_id):
            logger.debug("Channel not enabled", channel_id=channel_id)
            return

        try:
            # Check if this is a new conversation or continuation
            conversation = await conversation_service.get_or_create_conversation(
                channel_id=channel_id,
                thread_ts=thread_ts,
                user_id=user_id,
            )

            # Save the message
            await conversation_service.save_message(
                conversation_id=conversation.id,
                ts=ts,
                user_id=user_id,
                text=text,
                files=event.get("files", []),
            )

            # Send acknowledgment (reaction or quick reply)
            try:
                await client.reactions_add(
                    channel=channel_id,
                    timestamp=ts,
                    name="eyes",  # 👀 emoji to show we're processing
                )
            except SlackApiError as e:
                logger.warning("Failed to add reaction", error=str(e))

            # Process the message
            await message_processor.process_message(
                conversation=conversation,
                message_text=text,
                files=event.get("files", []),
                channel_id=channel_id,
                thread_ts=thread_ts,
                client=client,
                say=say,
            )

            # Record metrics
            duration = time.time() - start_time
            first_response_time_seconds.labels(channel_id=channel_id).observe(duration)
            messages_processed_total.labels(
                channel_id=channel_id,
                status="success",
            ).inc()

            logger.info(
                "Message processed successfully",
                channel_id=channel_id,
                thread_ts=thread_ts,
                duration_seconds=duration,
            )

        except Exception as e:
            logger.exception(
                "Error processing message",
                channel_id=channel_id,
                thread_ts=thread_ts,
                error=str(e),
            )
            messages_processed_total.labels(
                channel_id=channel_id,
                status="error",
            ).inc()

            # Send error message to user
            try:
                await say(
                    text="Sorry, I encountered an error processing your message. Please try again.",
                    thread_ts=thread_ts,
                )
            except Exception as send_error:
                logger.exception("Failed to send error message", error=str(send_error))
