"""Jira integration client."""

import structlog
from jira import JIRA
from jira.exceptions import JIRAError

from src.config.settings import Settings

logger = structlog.get_logger(__name__)


class JiraClient:
    """Client for Jira integration."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Jira client.

        Args:
            settings: Application settings
        """
        self.settings = settings

        if not settings.jira_url:
            logger.warning("Jira URL not configured")
            self.client = None
            return

        try:
            self.client = JIRA(
                server=settings.jira_url,
                basic_auth=(
                    settings.jira_username,
                    settings.jira_api_token.get_secret_value() if settings.jira_api_token else "",
                ),
            )
            logger.info("Jira client initialized", server=settings.jira_url)
        except JIRAError as e:
            logger.exception("Failed to initialize Jira client", error=str(e))
            self.client = None

    async def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str | None = None,
        labels: list[str] | None = None,
    ) -> str | None:
        """Create a Jira issue.

        Args:
            summary: Issue summary
            description: Issue description
            issue_type: Issue type (defaults to settings)
            labels: Issue labels

        Returns:
            Jira issue key or None if failed
        """
        if not self.client:
            logger.warning("Jira client not initialized")
            return None

        try:
            issue_dict = {
                "project": {"key": self.settings.jira_project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type or self.settings.jira_issue_type},
            }

            if labels:
                issue_dict["labels"] = labels

            issue = self.client.create_issue(fields=issue_dict)

            logger.info(
                "Jira issue created",
                issue_key=issue.key,
                summary=summary,
            )

            return issue.key

        except JIRAError as e:
            logger.exception("Failed to create Jira issue", error=str(e))
            return None

    async def update_issue(
        self,
        issue_key: str,
        comment: str | None = None,
        fields: dict | None = None,
    ) -> bool:
        """Update a Jira issue.

        Args:
            issue_key: Jira issue key
            comment: Comment to add
            fields: Fields to update

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.warning("Jira client not initialized")
            return False

        try:
            issue = self.client.issue(issue_key)

            if comment:
                self.client.add_comment(issue, comment)

            if fields:
                issue.update(fields=fields)

            logger.info("Jira issue updated", issue_key=issue_key)
            return True

        except JIRAError as e:
            logger.exception("Failed to update Jira issue", error=str(e))
            return False
