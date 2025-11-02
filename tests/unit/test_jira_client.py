"""Tests for Jira integration client."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from jira.exceptions import JIRAError

from src.integrations.jira_client import JiraClient
from src.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings with Jira config."""
    settings = MagicMock(spec=Settings)
    settings.jira_url = "https://test.atlassian.net"
    settings.jira_username = "test@example.com"
    settings.jira_api_token = MagicMock()
    settings.jira_api_token.get_secret_value.return_value = "test-token"
    settings.jira_project_key = "TEST"
    settings.jira_issue_type = "Task"
    return settings


@pytest.fixture
def mock_settings_no_jira():
    """Create mock settings without Jira config."""
    settings = MagicMock(spec=Settings)
    settings.jira_url = None
    return settings


def test_jira_client_initialization(mock_settings):
    """Test Jira client initialization."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        client = JiraClient(mock_settings)

        assert client.settings == mock_settings
        mock_jira.assert_called_once_with(
            server=mock_settings.jira_url,
            basic_auth=(mock_settings.jira_username, "test-token"),
        )


def test_jira_client_no_url(mock_settings_no_jira):
    """Test Jira client when URL not configured."""
    client = JiraClient(mock_settings_no_jira)

    assert client.client is None


@pytest.mark.asyncio
async def test_create_issue_success(mock_settings):
    """Test successful issue creation."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        # Mock successful issue creation
        mock_issue = MagicMock()
        mock_issue.key = "TEST-123"
        mock_jira.return_value.create_issue.return_value = mock_issue

        client = JiraClient(mock_settings)
        issue_key = await client.create_issue(
            summary="Test Issue",
            description="Test Description",
        )

        assert issue_key == "TEST-123"
        mock_jira.return_value.create_issue.assert_called_once()


@pytest.mark.asyncio
async def test_create_issue_with_labels(mock_settings):
    """Test issue creation with labels."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        mock_issue = MagicMock()
        mock_issue.key = "TEST-124"
        mock_jira.return_value.create_issue.return_value = mock_issue

        client = JiraClient(mock_settings)
        issue_key = await client.create_issue(
            summary="Test Issue",
            description="Test Description",
            labels=["bug", "urgent"],
        )

        assert issue_key == "TEST-124"
        call_args = mock_jira.return_value.create_issue.call_args
        assert "labels" in call_args[1]["fields"]
        assert call_args[1]["fields"]["labels"] == ["bug", "urgent"]


@pytest.mark.asyncio
async def test_create_issue_custom_type(mock_settings):
    """Test issue creation with custom issue type."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        mock_issue = MagicMock()
        mock_issue.key = "TEST-125"
        mock_jira.return_value.create_issue.return_value = mock_issue

        client = JiraClient(mock_settings)
        issue_key = await client.create_issue(
            summary="Test Bug",
            description="Bug Description",
            issue_type="Bug",
        )

        assert issue_key == "TEST-125"
        call_args = mock_jira.return_value.create_issue.call_args
        assert call_args[1]["fields"]["issuetype"]["name"] == "Bug"


@pytest.mark.asyncio
async def test_create_issue_failure(mock_settings):
    """Test issue creation failure."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        mock_jira.return_value.create_issue.side_effect = JIRAError("API Error")

        client = JiraClient(mock_settings)
        issue_key = await client.create_issue(
            summary="Test Issue",
            description="Test Description",
        )

        assert issue_key is None


@pytest.mark.asyncio
async def test_create_issue_no_client(mock_settings_no_jira):
    """Test issue creation when client not initialized."""
    client = JiraClient(mock_settings_no_jira)
    issue_key = await client.create_issue(
        summary="Test Issue",
        description="Test Description",
    )

    assert issue_key is None


@pytest.mark.asyncio
async def test_update_issue_success(mock_settings):
    """Test successful issue update."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        mock_issue = MagicMock()
        mock_jira.return_value.issue.return_value = mock_issue

        client = JiraClient(mock_settings)
        result = await client.update_issue(
            issue_key="TEST-123",
            comment="Test comment",
        )

        assert result is True
        mock_jira.return_value.add_comment.assert_called_once_with(
            mock_issue, "Test comment"
        )


@pytest.mark.asyncio
async def test_update_issue_with_fields(mock_settings):
    """Test issue update with fields."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        mock_issue = MagicMock()
        mock_jira.return_value.issue.return_value = mock_issue

        client = JiraClient(mock_settings)
        result = await client.update_issue(
            issue_key="TEST-123",
            fields={"status": "In Progress"},
        )

        assert result is True
        mock_issue.update.assert_called_once_with(fields={"status": "In Progress"})


@pytest.mark.asyncio
async def test_update_issue_failure(mock_settings):
    """Test issue update failure."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        mock_jira.return_value.issue.side_effect = JIRAError("Issue not found")

        client = JiraClient(mock_settings)
        result = await client.update_issue(
            issue_key="TEST-999",
            comment="Test comment",
        )

        assert result is False


@pytest.mark.asyncio
async def test_update_issue_no_client(mock_settings_no_jira):
    """Test issue update when client not initialized."""
    client = JiraClient(mock_settings_no_jira)
    result = await client.update_issue(
        issue_key="TEST-123",
        comment="Test comment",
    )

    assert result is False


def test_jira_client_initialization_error(mock_settings):
    """Test Jira client initialization error handling."""
    with patch("src.integrations.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = JIRAError("Connection failed")

        client = JiraClient(mock_settings)

        assert client.client is None
