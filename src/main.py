"""Main application entry point for the Slack RAG Assistant."""

import asyncio
import signal
import sys
from typing import Any

import structlog
import uvicorn
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from src.config.settings import get_settings
from src.observability.logging import setup_logging
from src.observability.metrics import setup_metrics
from src.slack.bot import create_slack_app


logger = structlog.get_logger(__name__)


class Application:
    """Main application class."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.settings = get_settings()
        self.app: AsyncApp | None = None
        self.handler: AsyncSocketModeHandler | None = None
        self.web_server: Any = None
        self._shutdown_event = asyncio.Event()

    async def setup(self) -> None:
        """Set up the application components."""
        logger.info("Starting Slack RAG Assistant", version=self.settings.app_version)

        # Set up observability
        setup_logging(self.settings)
        setup_metrics(self.settings)

        # Create Slack app
        self.app = await create_slack_app(self.settings)

        # Create socket mode handler
        self.handler = AsyncSocketModeHandler(
            app=self.app,
            app_token=self.settings.slack_app_token,
        )

        logger.info("Application setup complete")

    async def run(self) -> None:
        """Run the application."""
        if not self.handler:
            raise RuntimeError("Application not set up. Call setup() first.")

        logger.info("Starting Slack bot and web dashboard")

        # Start Slack bot in background
        bot_task = asyncio.create_task(self.handler.start_async())

        # Start web dashboard
        config = uvicorn.Config(
            "src.web.app:app",
            host="0.0.0.0",
            port=8080,
            log_level="info",
        )
        server = uvicorn.Server(config)
        web_task = asyncio.create_task(server.serve())

        logger.info(
            "Services started",
            web_dashboard="http://localhost:8080",
            metrics="http://localhost:9090/metrics",
        )

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        # Cancel tasks
        bot_task.cancel()
        web_task.cancel()

    async def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        logger.info("Shutting down application")

        if self.handler:
            await self.handler.close_async()

        logger.info("Application shutdown complete")

    def handle_signal(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info("Received shutdown signal", signal=signum)
        self._shutdown_event.set()


async def main() -> None:
    """Main entry point."""
    app = Application()

    # Set up signal handlers
    signal.signal(signal.SIGINT, app.handle_signal)
    signal.signal(signal.SIGTERM, app.handle_signal)

    try:
        await app.setup()
        await app.run()
    except Exception as e:
        logger.exception("Application error", error=str(e))
        sys.exit(1)
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
