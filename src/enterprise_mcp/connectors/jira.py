"""Jira Cloud REST API v3 connector."""

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseConnector

logger = logging.getLogger(__name__)


class JiraConnector(BaseConnector):
    """Jira Cloud REST API v3 connector.

    Handles authentication via Basic Auth (email + API token) and
    provides methods for common Jira operations with automatic retry
    and exponential backoff on transient failures.
    """

    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        """Initialize the Jira connector.

        Args:
            base_url: Jira Cloud base URL (e.g., https://yourcompany.atlassian.net).
            email: Jira user email address.
            api_token: Jira API token (generated in Atlassian account settings).
        """
        self.base_url = base_url.rstrip("/")
        self._auth = (email, api_token)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return a lazily-initialized async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=f"{self.base_url}/rest/api/3",
                auth=self._auth,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_issue(
        self, issue_key: str, include_comments: bool = False
    ) -> dict[str, Any]:
        """Fetch a Jira issue by its key.

        Args:
            issue_key: The Jira issue key (e.g., PROJ-123).
            include_comments: Whether to include issue comments in the response.

        Returns:
            Full issue details including status, assignee, priority, description.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses after retries.
        """
        client = await self._get_client()
        fields = "summary,status,assignee,priority,description,issuetype,created,updated,labels,components"
        params: dict[str, Any] = {"fields": fields}
        if include_comments:
            params["fields"] += ",comment"
        response = await client.get(f"/issue/{issue_key}", params=params)
        self._raise_for_status(response, f"get_issue({issue_key})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        fields: str = "summary,status,assignee,priority,issuetype,created,updated",
    ) -> dict[str, Any]:
        """Search Jira issues using JQL (Jira Query Language).

        Args:
            jql: JQL query string (e.g., 'project = PROJ AND status = "In Progress"').
            max_results: Maximum number of results to return (default 50, max 100).
            fields: Comma-separated list of fields to include in each issue.

        Returns:
            Search results containing matching issues and pagination metadata.
        """
        client = await self._get_client()
        payload = {
            "jql": jql,
            "maxResults": min(max_results, 100),
            "fields": fields.split(","),
        }
        response = await client.post("/search", json=payload)
        self._raise_for_status(response, f"search_issues({jql!r})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: str = "",
        priority: str = "",
        assignee_account_id: str = "",
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new Jira issue.

        Args:
            project_key: The key of the project to create the issue in (e.g., PROJ).
            summary: Issue summary/title.
            issue_type: Issue type name (e.g., Bug, Task, Story). Defaults to Task.
            description: Plain text description for the issue.
            priority: Priority name (e.g., High, Medium, Low).
            assignee_account_id: Atlassian account ID of the assignee.
            labels: List of label strings to attach.

        Returns:
            Created issue data with key and self URL.
        """
        client = await self._get_client()
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            }
        if priority:
            fields["priority"] = {"name": priority}
        if assignee_account_id:
            fields["assignee"] = {"accountId": assignee_account_id}
        if labels:
            fields["labels"] = labels

        response = await client.post("/issue", json={"fields": fields})
        self._raise_for_status(response, "create_issue")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def update_issue(
        self,
        issue_key: str,
        status_transition_id: str = "",
        assignee_account_id: str = "",
        priority: str = "",
        summary: str = "",
    ) -> dict[str, Any]:
        """Update a Jira issue's fields and/or transition its status.

        Args:
            issue_key: The Jira issue key (e.g., PROJ-123).
            status_transition_id: Transition ID to move the issue to a new status.
            assignee_account_id: Atlassian account ID for the new assignee.
            priority: New priority name (e.g., High, Medium).
            summary: New issue summary/title.

        Returns:
            Updated issue details or transition result.
        """
        client = await self._get_client()
        results: dict[str, Any] = {}

        # Update fields
        update_fields: dict[str, Any] = {}
        if assignee_account_id:
            update_fields["assignee"] = {"accountId": assignee_account_id}
        if priority:
            update_fields["priority"] = {"name": priority}
        if summary:
            update_fields["summary"] = summary

        if update_fields:
            response = await client.put(
                f"/issue/{issue_key}", json={"fields": update_fields}
            )
            self._raise_for_status(response, f"update_issue fields({issue_key})")
            results["fields_updated"] = True

        # Transition status
        if status_transition_id:
            response = await client.post(
                f"/issue/{issue_key}/transitions",
                json={"transition": {"id": status_transition_id}},
            )
            self._raise_for_status(response, f"update_issue transition({issue_key})")
            results["transitioned"] = True

        # Fetch fresh data
        fresh = await self.get_issue(issue_key)
        results["issue"] = fresh
        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def add_comment(self, issue_key: str, body: str) -> dict[str, Any]:
        """Add a comment to a Jira issue.

        Args:
            issue_key: The Jira issue key (e.g., PROJ-123).
            body: Plain text comment body.

        Returns:
            Created comment data including ID, author, and creation time.
        """
        client = await self._get_client()
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": body}],
                    }
                ],
            }
        }
        response = await client.post(f"/issue/{issue_key}/comment", json=payload)
        self._raise_for_status(response, f"add_comment({issue_key})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_sprint(self, board_id: int) -> dict[str, Any]:
        """Get the active sprint for a Jira board.

        Args:
            board_id: Numeric ID of the Jira board.

        Returns:
            Active sprint details including name, start/end dates, and goal.
        """
        # Sprint API uses the agile endpoint
        client = await self._get_client()
        # Override base URL for agile endpoint
        agile_url = f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint"
        response = await client.get(
            agile_url, params={"state": "active"}, base_url=None  # type: ignore[call-arg]
        )
        # Use full URL directly
        agile_client = httpx.AsyncClient(
            auth=self._auth,
            headers={"Accept": "application/json"},
            timeout=30.0,
        )
        try:
            response = await agile_client.get(
                f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint",
                params={"state": "active"},
            )
            self._raise_for_status(response, f"get_sprint(board={board_id})")
            data = response.json()
            sprints = data.get("values", [])
            return sprints[0] if sprints else {"message": "No active sprint found"}
        finally:
            await agile_client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def list_projects(self, max_results: int = 50) -> dict[str, Any]:
        """List all accessible Jira projects.

        Args:
            max_results: Maximum number of projects to return.

        Returns:
            List of projects with keys, names, and types.
        """
        client = await self._get_client()
        response = await client.get(
            "/project/search",
            params={"maxResults": max_results, "orderBy": "name"},
        )
        self._raise_for_status(response, "list_projects")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_board(self, board_id: int) -> dict[str, Any]:
        """Get a Jira board configuration and its columns.

        Args:
            board_id: Numeric ID of the Jira board.

        Returns:
            Board details including name, type, and column configuration.
        """
        agile_client = httpx.AsyncClient(
            auth=self._auth,
            headers={"Accept": "application/json"},
            timeout=30.0,
        )
        try:
            response = await agile_client.get(
                f"{self.base_url}/rest/agile/1.0/board/{board_id}",
            )
            self._raise_for_status(response, f"get_board({board_id})")
            board = response.json()

            # Also fetch board configuration (columns)
            config_response = await agile_client.get(
                f"{self.base_url}/rest/agile/1.0/board/{board_id}/configuration",
            )
            if config_response.is_success:
                board["configuration"] = config_response.json()
            return board
        finally:
            await agile_client.aclose()
