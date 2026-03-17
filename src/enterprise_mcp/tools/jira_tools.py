"""Jira MCP tools — 8 tools for Jira Cloud operations."""

import json
import logging
from typing import Any

from mcp.types import Tool

from ..connectors.jira import JiraConnector
from .registry import register_tool

logger = logging.getLogger(__name__)


def register_jira_tools(connector: JiraConnector) -> None:
    """Register all Jira tools with the tool registry.

    Args:
        connector: Configured JiraConnector instance.
    """
    # ------------------------------------------------------------------ #
    # jira_get_issue
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="jira_get_issue",
            description=(
                "Fetch a Jira issue by its key. Returns full issue details including "
                "status, assignee, priority, description, and optionally comments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., PROJ-123)",
                    },
                    "include_comments": {
                        "type": "boolean",
                        "description": "Whether to include issue comments",
                        "default": False,
                    },
                },
                "required": ["issue_key"],
            },
        ),
        _make_get_issue(connector),
    )

    # ------------------------------------------------------------------ #
    # jira_search_issues
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="jira_search_issues",
            description=(
                "Search Jira issues using JQL (Jira Query Language). "
                "Example JQL: 'project = PROJ AND status = \"In Progress\" AND assignee = currentUser()'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default 50, max 100)",
                        "default": 50,
                    },
                },
                "required": ["jql"],
            },
        ),
        _make_search_issues(connector),
    )

    # ------------------------------------------------------------------ #
    # jira_create_issue
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="jira_create_issue",
            description="Create a new Jira issue in a specified project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Project key (e.g., PROJ)",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Issue title/summary",
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Issue type (Bug, Task, Story, Epic). Defaults to Task",
                        "default": "Task",
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description (plain text)",
                        "default": "",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority name (Highest, High, Medium, Low, Lowest)",
                        "default": "",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to attach to the issue",
                    },
                },
                "required": ["project_key", "summary"],
            },
        ),
        _make_create_issue(connector),
    )

    # ------------------------------------------------------------------ #
    # jira_update_issue
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="jira_update_issue",
            description=(
                "Update a Jira issue: change status via transition, reassign, update priority or summary."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., PROJ-123)",
                    },
                    "status_transition_id": {
                        "type": "string",
                        "description": "Transition ID to move the issue to a new status",
                        "default": "",
                    },
                    "assignee_account_id": {
                        "type": "string",
                        "description": "Atlassian account ID for the new assignee",
                        "default": "",
                    },
                    "priority": {
                        "type": "string",
                        "description": "New priority name (e.g., High, Medium)",
                        "default": "",
                    },
                    "summary": {
                        "type": "string",
                        "description": "New issue summary/title",
                        "default": "",
                    },
                },
                "required": ["issue_key"],
            },
        ),
        _make_update_issue(connector),
    )

    # ------------------------------------------------------------------ #
    # jira_add_comment
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="jira_add_comment",
            description="Add a comment to a Jira issue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., PROJ-123)",
                    },
                    "body": {
                        "type": "string",
                        "description": "Comment text (plain text)",
                    },
                },
                "required": ["issue_key", "body"],
            },
        ),
        _make_add_comment(connector),
    )

    # ------------------------------------------------------------------ #
    # jira_get_sprint
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="jira_get_sprint",
            description=(
                "Get the active sprint for a Jira board, including name, goal, "
                "start date, and end date."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "integer",
                        "description": "Numeric ID of the Jira board",
                    },
                },
                "required": ["board_id"],
            },
        ),
        _make_get_sprint(connector),
    )

    # ------------------------------------------------------------------ #
    # jira_list_projects
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="jira_list_projects",
            description="List all accessible Jira projects with their keys and names.",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of projects to return (default 50)",
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
        _make_list_projects(connector),
    )

    # ------------------------------------------------------------------ #
    # jira_get_board
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="jira_get_board",
            description=(
                "Get a Jira board's configuration including name, type, "
                "and column/status configuration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "integer",
                        "description": "Numeric ID of the Jira board",
                    },
                },
                "required": ["board_id"],
            },
        ),
        _make_get_board(connector),
    )


# ---- Handler factory functions ------------------------------------------ #


def _make_get_issue(connector: JiraConnector) -> Any:
    async def handler(issue_key: str, include_comments: bool = False) -> str:
        try:
            result = await connector.get_issue(issue_key, include_comments)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"jira_get_issue failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_search_issues(connector: JiraConnector) -> Any:
    async def handler(jql: str, max_results: int = 50) -> str:
        try:
            result = await connector.search_issues(jql, max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"jira_search_issues failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_create_issue(connector: JiraConnector) -> Any:
    async def handler(
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: str = "",
        priority: str = "",
        labels: list[str] | None = None,
    ) -> str:
        try:
            result = await connector.create_issue(
                project_key, summary, issue_type, description, priority, labels=labels
            )
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"jira_create_issue failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_update_issue(connector: JiraConnector) -> Any:
    async def handler(
        issue_key: str,
        status_transition_id: str = "",
        assignee_account_id: str = "",
        priority: str = "",
        summary: str = "",
    ) -> str:
        try:
            result = await connector.update_issue(
                issue_key, status_transition_id, assignee_account_id, priority, summary
            )
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"jira_update_issue failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_add_comment(connector: JiraConnector) -> Any:
    async def handler(issue_key: str, body: str) -> str:
        try:
            result = await connector.add_comment(issue_key, body)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"jira_add_comment failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_get_sprint(connector: JiraConnector) -> Any:
    async def handler(board_id: int) -> str:
        try:
            result = await connector.get_sprint(board_id)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"jira_get_sprint failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_list_projects(connector: JiraConnector) -> Any:
    async def handler(max_results: int = 50) -> str:
        try:
            result = await connector.list_projects(max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"jira_list_projects failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_get_board(connector: JiraConnector) -> Any:
    async def handler(board_id: int) -> str:
        try:
            result = await connector.get_board(board_id)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"jira_get_board failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler
