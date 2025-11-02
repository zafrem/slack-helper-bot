"""Email integration client."""

import structlog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from src.config.settings import Settings

logger = structlog.get_logger(__name__)


class EmailClient:
    """Client for sending escalation emails."""

    def __init__(self, settings: Settings) -> None:
        """Initialize email client.

        Args:
            settings: Application settings
        """
        self.settings = settings

    async def send_escalation(
        self,
        to_email: str,
        subject: str,
        summary: str,
        thread_url: str,
        jira_key: str | None = None,
    ) -> bool:
        """Send escalation email.

        Args:
            to_email: Recipient email
            subject: Email subject
            summary: Conversation summary
            thread_url: Slack thread URL
            jira_key: Jira issue key

        Returns:
            True if successful, False otherwise
        """
        logger.info("Sending escalation email", to_email=to_email)

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.settings.smtp_from_email or self.settings.smtp_username
            message["To"] = to_email
            message["Subject"] = subject

            # Create email body
            text_body = f"""
Slack RAG Assistant - Escalation Notice

Summary:
{summary}

This conversation has been escalated due to SLA breach or complexity.

Slack Thread: {thread_url}
"""

            if jira_key:
                text_body += f"\nJira Issue: {self.settings.jira_url}/browse/{jira_key}\n"

            text_body += """
Please review and take appropriate action.

---
This is an automated message from Slack RAG Assistant.
"""

            # Attach text body
            message.attach(MIMEText(text_body, "plain"))

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_username,
                password=self.settings.smtp_password.get_secret_value() if self.settings.smtp_password else None,
                use_tls=self.settings.smtp_use_tls,
            )

            logger.info("Escalation email sent successfully", to_email=to_email)
            return True

        except Exception as e:
            logger.exception("Failed to send escalation email", error=str(e))
            return False
