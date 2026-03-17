"""Tests for the Jira connector and tools."""

import json

import httpx
import pytest
import respx

from enterprise_mcp.connectors.jira import JiraConnector

JIRA_BASE = "https://test.atlassian.net"
ISSUE_KEY = "PROJ-123"
API_BASE = f"{JIRA_BASE}/rest/api/3"


# ---- get_issue ----------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_issue_success(jira_issue_payload):
    """get_issue returns parsed issue data on HTTP 200."""
    async with respx.mock:
        respx.get(f"{API_BASE}/issue/{ISSUE_KEY}").mock(
            return_value=httpx.Response(200, json=jira_issue_payload)
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        result = await connector.get_issue(ISSUE_KEY)

    assert result["key"] == ISSUE_KEY
    assert result["fields"]["summary"] == "Payment service returns 500 errors"


@pytest.mark.asyncio
async def test_get_issue_not_found():
    """get_issue raises HTTPStatusError on HTTP 404."""
    async with respx.mock:
        respx.get(f"{API_BASE}/issue/PROJ-999").mock(
            return_value=httpx.Response(
                404, json={"errorMessages": ["Issue does not exist or you do not have permission to see it."]}
            )
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_issue("PROJ-999")


@pytest.mark.asyncio
async def test_get_issue_rate_limit():
    """get_issue raises HTTPStatusError after retrying on HTTP 429."""
    async with respx.mock:
        respx.get(f"{API_BASE}/issue/{ISSUE_KEY}").mock(
            return_value=httpx.Response(429, json={"message": "Rate limit exceeded"})
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_issue(ISSUE_KEY)


@pytest.mark.asyncio
async def test_get_issue_server_error():
    """get_issue raises HTTPStatusError on HTTP 500."""
    async with respx.mock:
        respx.get(f"{API_BASE}/issue/{ISSUE_KEY}").mock(
            return_value=httpx.Response(500, json={"message": "Internal server error"})
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_issue(ISSUE_KEY)


# ---- search_issues ------------------------------------------------------- #


@pytest.mark.asyncio
async def test_search_issues_success(jira_search_payload):
    """search_issues returns list of matching issues on HTTP 200."""
    async with respx.mock:
        respx.post(f"{API_BASE}/search").mock(
            return_value=httpx.Response(200, json=jira_search_payload)
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        result = await connector.search_issues('project = PROJ AND status = "In Progress"')

    assert result["total"] == 1
    assert result["issues"][0]["key"] == ISSUE_KEY


@pytest.mark.asyncio
async def test_search_issues_empty():
    """search_issues returns empty list when no matches found."""
    async with respx.mock:
        respx.post(f"{API_BASE}/search").mock(
            return_value=httpx.Response(200, json={"total": 0, "issues": [], "maxResults": 50, "startAt": 0})
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        result = await connector.search_issues("project = EMPTY")

    assert result["total"] == 0
    assert result["issues"] == []


# ---- create_issue -------------------------------------------------------- #


@pytest.mark.asyncio
async def test_create_issue_success(jira_create_payload):
    """create_issue returns the created issue key on HTTP 201."""
    async with respx.mock:
        respx.post(f"{API_BASE}/issue").mock(
            return_value=httpx.Response(201, json=jira_create_payload)
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        result = await connector.create_issue(
            "PROJ", "New bug in payment flow", "Bug", "Detailed description"
        )

    assert result["key"] == "PROJ-124"


@pytest.mark.asyncio
async def test_create_issue_bad_request():
    """create_issue raises HTTPStatusError on HTTP 400 (e.g., invalid project)."""
    async with respx.mock:
        respx.post(f"{API_BASE}/issue").mock(
            return_value=httpx.Response(
                400, json={"errorMessages": [], "errors": {"project": "project is required"}}
            )
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.create_issue("", "No project", "Task")


# ---- add_comment --------------------------------------------------------- #


@pytest.mark.asyncio
async def test_add_comment_success(jira_comment_payload):
    """add_comment returns the created comment on HTTP 201."""
    async with respx.mock:
        respx.post(f"{API_BASE}/issue/{ISSUE_KEY}/comment").mock(
            return_value=httpx.Response(201, json=jira_comment_payload)
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        result = await connector.add_comment(ISSUE_KEY, "This is a test comment.")

    assert result["id"] == "10100"
    assert result["author"]["displayName"] == "Bot User"


@pytest.mark.asyncio
async def test_add_comment_not_found():
    """add_comment raises HTTPStatusError when issue does not exist."""
    async with respx.mock:
        respx.post(f"{API_BASE}/issue/PROJ-9999/comment").mock(
            return_value=httpx.Response(404, json={"errorMessages": ["Issue not found"]})
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.add_comment("PROJ-9999", "Ghost comment")


# ---- list_projects ------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_projects_success():
    """list_projects returns project list on HTTP 200."""
    payload = {
        "values": [
            {"id": "10000", "key": "PROJ", "name": "My Project"},
            {"id": "10001", "key": "OPS", "name": "Operations"},
        ],
        "total": 2,
    }
    async with respx.mock:
        respx.get(f"{API_BASE}/project/search").mock(
            return_value=httpx.Response(200, json=payload)
        )
        connector = JiraConnector(JIRA_BASE, "user@test.com", "token")
        result = await connector.list_projects()

    assert len(result["values"]) == 2
    assert result["values"][0]["key"] == "PROJ"
