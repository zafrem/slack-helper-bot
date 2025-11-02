"""Tests for email integration client."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from src.integrations.email_client import EmailClient
from src.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings with email config."""
    settings = MagicMock(spec=Settings)
    settings.smtp_host = "smtp.test.com"
    settings.smtp_port = 587
    settings.smtp_username = "test@example.com"
    settings.smtp_password = MagicMock()
    settings.smtp_password.get_secret_value.return_value = "test-password"
    settings.smtp_from_email = "bot@example.com"
    settings.smtp_use_tls = True
    settings.jira_url = "https://test.atlassian.net"
    return settings


@pytest.mark.asyncio
async def test_send_escalation_success(mock_settings):
    """Test successful escalation email."""
    with patch("src.integrations.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        client = EmailClient(mock_settings)

        result = await client.send_escalation(
            to_email="user@example.com",
            subject="Escalation: Unresolved Issue",
            summary="Test summary",
            thread_url="https://slack.com/archives/C123/p123456",
        )

        assert result is True
        mock_send.assert_called_once()

        # Check email content
        call_args = mock_send.call_args
        message = call_args[0][0]
        assert message["To"] == "user@example.com"
        assert message["Subject"] == "Escalation: Unresolved Issue"


@pytest.mark.asyncio
async def test_send_escalation_with_jira(mock_settings):
    """Test escalation email with Jira key."""
    with patch("src.integrations.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        client = EmailClient(mock_settings)

        result = await client.send_escalation(
            to_email="user@example.com",
            subject="Escalation: Unresolved Issue",
            summary="Test summary",
            thread_url="https://slack.com/archives/C123/p123456",
            jira_key="TEST-123",
        )

        assert result is True

        # Check that Jira link is in email
        call_args = mock_send.call_args
        message = call_args[0][0]
        body = message.get_payload()[0].get_payload()
        assert "TEST-123" in body
        assert mock_settings.jira_url in body


@pytest.mark.asyncio
async def test_send_escalation_failure(mock_settings):
    """Test escalation email failure."""
    with patch("src.integrations.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("SMTP connection failed")

        client = EmailClient(mock_settings)

        result = await client.send_escalation(
            to_email="user@example.com",
            subject="Escalation: Unresolved Issue",
            summary="Test summary",
            thread_url="https://slack.com/archives/C123/p123456",
        )

        assert result is False


@pytest.mark.asyncio
async def test_send_escalation_smtp_auth(mock_settings):
    """Test SMTP authentication parameters."""
    with patch("src.integrations.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        client = EmailClient(mock_settings)

        await client.send_escalation(
            to_email="user@example.com",
            subject="Test Subject",
            summary="Test summary",
            thread_url="https://slack.com/test",
        )

        # Check SMTP parameters
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["hostname"] == "smtp.test.com"
        assert call_kwargs["port"] == 587
        assert call_kwargs["username"] == "test@example.com"
        assert call_kwargs["password"] == "test-password"
        assert call_kwargs["use_tls"] is True


@pytest.mark.asyncio
async def test_send_escalation_from_email(mock_settings):
    """Test from email address."""
    with patch("src.integrations.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        client = EmailClient(mock_settings)

        await client.send_escalation(
            to_email="user@example.com",
            subject="Test Subject",
            summary="Test summary",
            thread_url="https://slack.com/test",
        )

        call_args = mock_send.call_args
        message = call_args[0][0]
        assert message["From"] == "bot@example.com"


@pytest.mark.asyncio
async def test_send_escalation_content_format(mock_settings):
    """Test email content formatting."""
    with patch("src.integrations.email_client.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        client = EmailClient(mock_settings)

        summary = "User reported a critical bug in the payment system"
        thread_url = "https://slack.com/archives/C123/p123456"

        await client.send_escalation(
            to_email="user@example.com",
            subject="Critical Escalation",
            summary=summary,
            thread_url=thread_url,
            jira_key="BUG-456",
        )

        call_args = mock_send.call_args
        message = call_args[0][0]
        body = message.get_payload()[0].get_payload()

        # Check content includes key elements
        assert "Slack RAG Assistant" in body
        assert "Escalation Notice" in body
        assert summary in body
        assert thread_url in body
        assert "BUG-456" in body
        assert "automated message" in body.lower()
