"""Slack bot initialization and event handlers."""

import structlog
from slack_bolt.async_app import AsyncApp

from src.config.channel_config import ChannelConfigManager
from src.config.settings import Settings
from src.slack.handlers.message import register_message_handlers
from src.slack.handlers.reaction import register_reaction_handlers
from src.slack.handlers.action import register_action_handlers

logger = structlog.get_logger(__name__)


async def create_slack_app(settings: Settings) -> AsyncApp:
    """Create and configure the Slack app.

    Args:
        settings: Application settings

    Returns:
        Configured Slack app
    """
    app = AsyncApp(
        token=settings.slack_bot_token.get_secret_value(),
        signing_secret=settings.slack_signing_secret.get_secret_value(),
    )

    # Load channel configurations
    channel_manager = ChannelConfigManager()

    # Attach to app context
    app.client.channel_manager = channel_manager  # type: ignore

    # Register event handlers
    register_message_handlers(app, settings, channel_manager)
    register_reaction_handlers(app, settings, channel_manager)
    register_action_handlers(app, settings, channel_manager)

    # Health check
    @app.event("app_mention")
    async def handle_app_mention(event: dict, say: callable) -> None:
        """Handle app mentions."""
        user = event.get("user")
        text = event.get("text", "")

        if "health" in text.lower() or "ping" in text.lower():
            await say(
                text=f"<@{user}> I'm healthy and ready to help!",
                thread_ts=event.get("ts"),
            )

    logger.info("Slack app created and configured")
    return app
