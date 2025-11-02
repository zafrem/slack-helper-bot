"""Reaction event handlers for feedback."""

from typing import Any

import structlog
from slack_bolt.async_app import AsyncApp

from src.config.channel_config import ChannelConfigManager
from src.config.settings import Settings
from src.models.feedback import FeedbackRating
from src.observability.metrics import feedback_total
from src.slack.services.conversation_service import ConversationService

logger = structlog.get_logger(__name__)


def register_reaction_handlers(
    app: AsyncApp,
    settings: Settings,
    channel_manager: ChannelConfigManager,
) -> None:
    """Register reaction event handlers for feedback.

    Args:
        app: Slack app instance
        settings: Application settings
        channel_manager: Channel configuration manager
    """
    conversation_service = ConversationService()

    # Mapping of emoji reactions to feedback ratings
    FEEDBACK_EMOJI_MAP = {
        "+1": FeedbackRating.HELPFUL,
        "thumbsup": FeedbackRating.HELPFUL,
        "white_check_mark": FeedbackRating.HELPFUL,
        "heavy_check_mark": FeedbackRating.HELPFUL,
        "-1": FeedbackRating.NOT_HELPFUL,
        "thumbsdown": FeedbackRating.NOT_HELPFUL,
        "x": FeedbackRating.NOT_HELPFUL,
    }

    @app.event("reaction_added")
    async def handle_reaction_added(event: dict[str, Any]) -> None:
        """Handle reaction added events.

        Args:
            event: Slack event data
        """
        reaction = event.get("reaction")
        user_id = event.get("user")
        item = event.get("item", {})
        channel_id = item.get("channel")
        message_ts = item.get("ts")

        # Check if channel is enabled
        if not channel_manager.is_channel_enabled(channel_id):
            return

        # Check if this is a feedback reaction
        if reaction not in FEEDBACK_EMOJI_MAP:
            return

        rating = FEEDBACK_EMOJI_MAP[reaction]

        logger.info(
            "Feedback reaction received",
            reaction=reaction,
            rating=rating.value,
            channel_id=channel_id,
            message_ts=message_ts,
            user_id=user_id,
        )

        try:
            # Find the conversation by message timestamp
            conversation = await conversation_service.find_conversation_by_message(message_ts)

            if not conversation:
                logger.warning(
                    "Conversation not found for feedback",
                    message_ts=message_ts,
                )
                return

            # Save feedback
            await conversation_service.save_feedback(
                conversation_id=conversation.id,
                user_id=user_id,
                rating=rating,
                message_ts=message_ts,
            )

            # Record metric
            feedback_total.labels(
                channel_id=channel_id,
                rating=rating.value,
            ).inc()

            logger.info(
                "Feedback saved successfully",
                conversation_id=conversation.id,
                rating=rating.value,
            )

        except Exception as e:
            logger.exception(
                "Error saving feedback",
                channel_id=channel_id,
                message_ts=message_ts,
                error=str(e),
            )
