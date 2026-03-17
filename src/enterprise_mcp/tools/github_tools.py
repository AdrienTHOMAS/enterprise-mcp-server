"""GitHub MCP tools — 8 tools for GitHub operations."""

import json
import logging
from typing import Any

from mcp.types import Tool

from ..connectors.github import GitHubConnector
from .registry import register_tool

logger = logging.getLogger(__name__)


def register_github_tools(connector: GitHubConnector) -> None:
    """Register all GitHub tools with the tool registry.

    Args:
        connector: Configured GitHubConnector instance.
    """
    default_owner = connector.default_owner

    # ------------------------------------------------------------------ #
    # github_get_repo
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="github_get_repo",
            description=(
                "Get GitHub repository information including description, stars, forks, "
                "open issues count, default branch, and topics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository name",
                    },
                    "owner": {
                        "type": "string",
                        "description": f"Repository owner/org (defaults to '{default_owner}')",
                        "default": default_owner,
                    },
                },
                "required": ["repo"],
            },
        ),
        _make_get_repo(connector),
    )

    # ------------------------------------------------------------------ #
    # github_list_issues
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="github_list_issues",
            description="List GitHub issues for a repository with optional state and label filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "owner": {
                        "type": "string",
                        "description": f"Repository owner/org (defaults to '{default_owner}')",
                        "default": default_owner,
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state: 'open', 'closed', or 'all'",
                        "default": "open",
                    },
                    "labels": {
                        "type": "string",
                        "description": "Comma-separated label names to filter by",
                        "default": "",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of issues to return",
                        "default": 30,
                    },
                },
                "required": ["repo"],
            },
        ),
        _make_list_issues(connector),
    )

    # ------------------------------------------------------------------ #
    # github_create_issue
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="github_create_issue",
            description="Create a new GitHub issue with title, body, labels, and assignees.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "title": {"type": "string", "description": "Issue title"},
                    "owner": {
                        "type": "string",
                        "description": f"Repository owner/org (defaults to '{default_owner}')",
                        "default": default_owner,
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue description (Markdown supported)",
                        "default": "",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Label names to apply",
                    },
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "GitHub usernames to assign",
                    },
                },
                "required": ["repo", "title"],
            },
        ),
        _make_create_issue(connector),
    )

    # ------------------------------------------------------------------ #
    # github_get_pull_request
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="github_get_pull_request",
            description=(
                "Get detailed information about a pull request including title, body, "
                "state, review status, CI checks, and diff statistics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "pr_number": {"type": "integer", "description": "Pull request number"},
                    "owner": {
                        "type": "string",
                        "description": f"Repository owner/org (defaults to '{default_owner}')",
                        "default": default_owner,
                    },
                },
                "required": ["repo", "pr_number"],
            },
        ),
        _make_get_pull_request(connector),
    )

    # ------------------------------------------------------------------ #
    # github_list_pull_requests
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="github_list_pull_requests",
            description="List open (or closed/all) pull requests for a repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "owner": {
                        "type": "string",
                        "description": f"Repository owner/org (defaults to '{default_owner}')",
                        "default": default_owner,
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state: 'open', 'closed', or 'all'",
                        "default": "open",
                    },
                    "base": {
                        "type": "string",
                        "description": "Filter by base branch name",
                        "default": "",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of PRs to return",
                        "default": 30,
                    },
                },
                "required": ["repo"],
            },
        ),
        _make_list_pull_requests(connector),
    )

    # ------------------------------------------------------------------ #
    # github_search_code
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="github_search_code",
            description=(
                "Search for code across GitHub repositories using GitHub's code search syntax. "
                "Supports language filters, path filters, and repo/org scoping."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'def authenticate language:python')",
                    },
                    "owner": {
                        "type": "string",
                        "description": "Restrict search to this org/owner",
                        "default": default_owner,
                    },
                    "repo": {
                        "type": "string",
                        "description": "Restrict search to this repository",
                        "default": "",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 30,
                    },
                },
                "required": ["query"],
            },
        ),
        _make_search_code(connector),
    )

    # ------------------------------------------------------------------ #
    # github_get_file_content
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="github_get_file_content",
            description="Read the content of a file from a GitHub repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {
                        "type": "string",
                        "description": "File path within the repository (e.g., src/main.py)",
                    },
                    "owner": {
                        "type": "string",
                        "description": f"Repository owner/org (defaults to '{default_owner}')",
                        "default": default_owner,
                    },
                    "ref": {
                        "type": "string",
                        "description": "Branch, tag, or commit SHA (defaults to default branch)",
                        "default": "",
                    },
                },
                "required": ["repo", "path"],
            },
        ),
        _make_get_file_content(connector),
    )

    # ------------------------------------------------------------------ #
    # github_create_review_comment
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="github_create_review_comment",
            description=(
                "Add a review comment to a specific line in a pull request diff. "
                "Use this to provide inline code feedback."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository name"},
                    "pr_number": {"type": "integer", "description": "Pull request number"},
                    "body": {
                        "type": "string",
                        "description": "Review comment text (Markdown supported)",
                    },
                    "commit_id": {
                        "type": "string",
                        "description": "SHA of the commit to comment on",
                    },
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file being commented on",
                    },
                    "line": {
                        "type": "integer",
                        "description": "Line number in the file",
                    },
                    "owner": {
                        "type": "string",
                        "description": f"Repository owner/org (defaults to '{default_owner}')",
                        "default": default_owner,
                    },
                },
                "required": ["repo", "pr_number", "body", "commit_id", "path", "line"],
            },
        ),
        _make_create_review_comment(connector),
    )


# ---- Handler factory functions ------------------------------------------ #


def _make_get_repo(connector: GitHubConnector) -> Any:
    async def handler(repo: str, owner: str = "") -> str:
        o = owner or connector.default_owner
        try:
            result = await connector.get_repo(o, repo)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"github_get_repo failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_list_issues(connector: GitHubConnector) -> Any:
    async def handler(
        repo: str, owner: str = "", state: str = "open", labels: str = "", max_results: int = 30
    ) -> str:
        o = owner or connector.default_owner
        try:
            result = await connector.list_issues(o, repo, state, labels, max_results=max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"github_list_issues failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_create_issue(connector: GitHubConnector) -> Any:
    async def handler(
        repo: str,
        title: str,
        owner: str = "",
        body: str = "",
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> str:
        o = owner or connector.default_owner
        try:
            result = await connector.create_issue(o, repo, title, body, labels, assignees)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"github_create_issue failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_get_pull_request(connector: GitHubConnector) -> Any:
    async def handler(repo: str, pr_number: int, owner: str = "") -> str:
        o = owner or connector.default_owner
        try:
            result = await connector.get_pull_request(o, repo, pr_number)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"github_get_pull_request failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_list_pull_requests(connector: GitHubConnector) -> Any:
    async def handler(
        repo: str, owner: str = "", state: str = "open", base: str = "", max_results: int = 30
    ) -> str:
        o = owner or connector.default_owner
        try:
            result = await connector.list_pull_requests(o, repo, state, base, max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"github_list_pull_requests failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_search_code(connector: GitHubConnector) -> Any:
    async def handler(query: str, owner: str = "", repo: str = "", max_results: int = 30) -> str:
        o = owner or connector.default_owner
        try:
            result = await connector.search_code(query, o, repo, max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"github_search_code failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_get_file_content(connector: GitHubConnector) -> Any:
    async def handler(repo: str, path: str, owner: str = "", ref: str = "") -> str:
        o = owner or connector.default_owner
        try:
            result = await connector.get_file_content(o, repo, path, ref)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"github_get_file_content failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_create_review_comment(connector: GitHubConnector) -> Any:
    async def handler(
        repo: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
        owner: str = "",
    ) -> str:
        o = owner or connector.default_owner
        try:
            result = await connector.create_review_comment(
                o, repo, pr_number, body, commit_id, path, line
            )
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"github_create_review_comment failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler
