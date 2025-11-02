"""Interactive action handlers (buttons, modals, etc.)."""

from typing import Any

import structlog
from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError

from src.config.channel_config import ChannelConfigManager
from src.config.settings import Settings
from src.slack.services.action_service import ActionService

logger = structlog.get_logger(__name__)


def register_action_handlers(
    app: AsyncApp,
    settings: Settings,
    channel_manager: ChannelConfigManager,
) -> None:
    """Register interactive action handlers.

    Args:
        app: Slack app instance
        settings: Application settings
        channel_manager: Channel configuration manager
    """
    action_service = ActionService(settings, channel_manager)

    @app.action("approve_summary")
    async def handle_approve_summary(ack: callable, body: dict[str, Any], client: Any) -> None:
        """Handle summary approval.

        Args:
            ack: Acknowledgment function
            body: Action payload
            client: Slack client
        """
        await ack()

        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]
        message_ts = body["message"]["ts"]

        logger.info(
            "Summary approved",
            user_id=user_id,
            channel_id=channel_id,
            message_ts=message_ts,
        )

        # Extract conversation metadata
        metadata = body.get("message", {}).get("metadata", {})
        thread_ts = metadata.get("event_payload", {}).get("thread_ts")

        if not thread_ts:
            logger.error("Missing thread_ts in metadata")
            return

        try:
            await action_service.handle_summary_approval(
                user_id=user_id,
                channel_id=channel_id,
                thread_ts=thread_ts,
                client=client,
            )
        except Exception as e:
            logger.exception("Error handling summary approval", error=str(e))

    @app.action("edit_summary")
    async def handle_edit_summary(ack: callable, body: dict[str, Any], client: Any) -> None:
        """Handle summary edit request.

        Args:
            ack: Acknowledgment function
            body: Action payload
            client: Slack client
        """
        await ack()

        # Open modal for editing
        trigger_id = body["trigger_id"]

        try:
            await client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": "edit_summary_modal",
                    "title": {"type": "plain_text", "text": "Edit Summary"},
                    "submit": {"type": "plain_text", "text": "Submit"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "summary_input",
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "summary_text",
                                "multiline": True,
                            },
                            "label": {"type": "plain_text", "text": "Summary"},
                        }
                    ],
                },
            )
        except SlackApiError as e:
            logger.exception("Error opening edit modal", error=str(e))

    @app.action("cancel_summary")
    async def handle_cancel_summary(ack: callable, body: dict[str, Any]) -> None:
        """Handle summary cancellation.

        Args:
            ack: Acknowledgment function
            body: Action payload
        """
        await ack()

        logger.info("Summary cancelled", user_id=body["user"]["id"])

        # Update the message to show cancellation
        # Implementation depends on your flow

    @app.action("approve_action")
    async def handle_approve_action(ack: callable, body: dict[str, Any], client: Any) -> None:
        """Handle action approval.

        Args:
            ack: Acknowledgment function
            body: Action payload
            client: Slack client
        """
        await ack()

        user_id = body["user"]["id"]
        channel_id = body["channel"]["id"]

        # Extract action metadata
        metadata = body.get("message", {}).get("metadata", {})
        action_id = metadata.get("event_payload", {}).get("action_id")
        thread_ts = metadata.get("event_payload", {}).get("thread_ts")

        logger.info(
            "Action approved",
            user_id=user_id,
            channel_id=channel_id,
            action_id=action_id,
        )

        try:
            await action_service.handle_action_approval(
                action_id=action_id,
                user_id=user_id,
                channel_id=channel_id,
                thread_ts=thread_ts,
                client=client,
            )
        except Exception as e:
            logger.exception("Error handling action approval", error=str(e))

    @app.action("reject_action")
    async def handle_reject_action(ack: callable, body: dict[str, Any]) -> None:
        """Handle action rejection.

        Args:
            ack: Acknowledgment function
            body: Action payload
        """
        await ack()

        logger.info("Action rejected", user_id=body["user"]["id"])

        # Mark action as rejected in database
        # Implementation depends on your flow
