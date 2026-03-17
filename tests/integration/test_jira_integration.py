"""Integration tests for Jira connector with full mock server routes."""

import json

import httpx
import pytest
import respx

from enterprise_mcp.connectors.jira import JiraConnector

JIRA_BASE = "https://test-integration.atlassian.net"
API_BASE = f"{JIRA_BASE}/rest/api/3"
AGILE_BASE = f"{JIRA_BASE}/rest/agile/1.0"


@pytest.fixture
def jira_connector():
    return JiraConnector(JIRA_BASE, "bot@test.com", "integration-token")


@pytest.fixture
def mock_jira_api():
    """Set up a full Jira mock API with all routes."""
    with respx.mock:
        # GET /issue/{key}
        respx.get(f"{API_BASE}/issue/INT-1").mock(
            return_value=httpx.Response(200, json={
                "id": "50001",
                "key": "INT-1",
                "fields": {
                    "summary": "Integration test issue",
                    "status": {"name": "Open"},
                    "assignee": {"displayName": "Integration Bot"},
                    "priority": {"name": "Medium"},
                    "description": None,
                    "issuetype": {"name": "Task"},
                    "created": "2024-06-01T10:00:00.000Z",
                    "updated": "2024-06-01T12:00:00.000Z",
                    "labels": ["integration"],
                    "components": [],
                },
            })
        )

        # POST /search
        respx.post(f"{API_BASE}/search").mock(
            return_value=httpx.Response(200, json={
                "total": 2,
                "maxResults": 50,
                "startAt": 0,
                "issues": [
                    {
                        "id": "50001",
                        "key": "INT-1",
                        "fields": {
                            "summary": "Integration test issue",
                            "status": {"name": "Open"},
                            "priority": {"name": "Medium"},
                            "issuetype": {"name": "Task"},
                        },
                    },
                    {
                        "id": "50002",
                        "key": "INT-2",
                        "fields": {
                            "summary": "Another integration issue",
                            "status": {"name": "In Progress"},
                            "priority": {"name": "High"},
                            "issuetype": {"name": "Bug"},
                        },
                    },
                ],
            })
        )

        # POST /issue (create)
        respx.post(f"{API_BASE}/issue").mock(
            return_value=httpx.Response(201, json={
                "id": "50003",
                "key": "INT-3",
                "self": f"{API_BASE}/issue/50003",
            })
        )

        # PUT /issue/{key} (update fields)
        respx.put(f"{API_BASE}/issue/INT-1").mock(
            return_value=httpx.Response(204)
        )

        # POST /issue/{key}/comment
        respx.post(f"{API_BASE}/issue/INT-1/comment").mock(
            return_value=httpx.Response(201, json={
                "id": "60001",
                "author": {"displayName": "Integration Bot"},
                "body": {"type": "doc", "content": []},
                "created": "2024-06-01T14:00:00.000Z",
            })
        )

        # GET /project/search
        respx.get(f"{API_BASE}/project/search").mock(
            return_value=httpx.Response(200, json={
                "values": [
                    {"id": "10000", "key": "INT", "name": "Integration"},
                    {"id": "10001", "key": "OPS", "name": "Operations"},
                ],
                "total": 2,
            })
        )

        yield


@pytest.mark.asyncio
async def test_full_issue_lifecycle(jira_connector, mock_jira_api):
    """Test creating, reading, commenting, and searching issues."""
    # Create an issue
    created = await jira_connector.create_issue(
        "INT", "Integration test issue", "Task", "Created by integration test"
    )
    assert created["key"] == "INT-3"

    # Read the issue
    issue = await jira_connector.get_issue("INT-1")
    assert issue["key"] == "INT-1"
    assert issue["fields"]["summary"] == "Integration test issue"

    # Add a comment
    comment = await jira_connector.add_comment("INT-1", "Integration test comment")
    assert comment["id"] == "60001"

    # Search issues
    results = await jira_connector.search_issues("project = INT")
    assert results["total"] == 2
    assert len(results["issues"]) == 2


@pytest.mark.asyncio
async def test_list_projects(jira_connector, mock_jira_api):
    """Test listing projects."""
    result = await jira_connector.list_projects()
    assert len(result["values"]) == 2
    assert result["values"][0]["key"] == "INT"


@pytest.mark.asyncio
async def test_update_issue_fields(jira_connector, mock_jira_api):
    """Test updating issue fields."""
    # Update needs both PUT and GET
    result = await jira_connector.update_issue(
        "INT-1", priority="High", summary="Updated summary"
    )
    assert result["fields_updated"] is True
    assert result["issue"]["key"] == "INT-1"
