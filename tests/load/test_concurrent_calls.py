"""Load tests for concurrent tool calls."""

import asyncio
import json
import time

import httpx
import pytest
import respx

from enterprise_mcp.connectors.jira import JiraConnector
from enterprise_mcp.tools.jira_tools import register_jira_tools
from enterprise_mcp.tools.registry import _TOOL_DEFINITIONS, _TOOL_REGISTRY, get_handler

JIRA_BASE = "https://load-test.atlassian.net"
API_BASE = f"{JIRA_BASE}/rest/api/3"


@pytest.fixture(autouse=True)
def clean_registry():
    _TOOL_REGISTRY.clear()
    _TOOL_DEFINITIONS.clear()
    yield
    _TOOL_REGISTRY.clear()
    _TOOL_DEFINITIONS.clear()


@pytest.fixture
def setup_tools():
    jira = JiraConnector(JIRA_BASE, "bot@test.com", "token")
    register_jira_tools(jira)


@pytest.mark.asyncio
async def test_100_concurrent_search_calls(setup_tools):
    """Test 100 concurrent Jira search calls complete within reasonable time."""
    with respx.mock:
        respx.post(f"{API_BASE}/search").mock(
            return_value=httpx.Response(200, json={
                "total": 5,
                "maxResults": 50,
                "startAt": 0,
                "issues": [
                    {
                        "key": f"LOAD-{i}",
                        "fields": {
                            "summary": f"Load test issue {i}",
                            "status": {"name": "Open"},
                            "priority": {"name": "Medium"},
                            "issuetype": {"name": "Task"},
                        },
                    }
                    for i in range(5)
                ],
            })
        )

        handler = get_handler("jira_search_issues")
        assert handler is not None

        start = time.monotonic()

        tasks = [
            handler(jql=f"project = LOAD AND id = {i}")
            for i in range(100)
        ]
        results = await asyncio.gather(*tasks)

        elapsed = time.monotonic() - start

        # All calls should succeed
        assert len(results) == 100
        for result in results:
            parsed = json.loads(result)
            assert "error" not in parsed
            assert parsed["total"] == 5

        # Should complete well within 30 seconds (mocked API)
        assert elapsed < 30.0, f"100 concurrent calls took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_50_concurrent_get_issue_calls(setup_tools):
    """Test 50 concurrent get_issue calls."""
    with respx.mock:
        for i in range(50):
            respx.get(f"{API_BASE}/issue/LOAD-{i}").mock(
                return_value=httpx.Response(200, json={
                    "id": str(10000 + i),
                    "key": f"LOAD-{i}",
                    "fields": {
                        "summary": f"Load test issue {i}",
                        "status": {"name": "Open"},
                        "assignee": None,
                        "priority": {"name": "Medium"},
                        "description": None,
                        "issuetype": {"name": "Task"},
                        "created": "2024-06-01T10:00:00.000Z",
                        "updated": "2024-06-01T12:00:00.000Z",
                        "labels": [],
                        "components": [],
                    },
                })
            )

        handler = get_handler("jira_get_issue")
        assert handler is not None

        tasks = [
            handler(issue_key=f"LOAD-{i}")
            for i in range(50)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 50
        for i, result in enumerate(results):
            parsed = json.loads(result)
            assert parsed["key"] == f"LOAD-{i}"


@pytest.mark.asyncio
async def test_mixed_concurrent_operations(setup_tools):
    """Test mixed read/search operations running concurrently."""
    with respx.mock:
        # Mock search
        respx.post(f"{API_BASE}/search").mock(
            return_value=httpx.Response(200, json={
                "total": 1,
                "maxResults": 50,
                "startAt": 0,
                "issues": [{"key": "MIX-1", "fields": {
                    "summary": "Mixed test",
                    "status": {"name": "Open"},
                    "priority": {"name": "Low"},
                    "issuetype": {"name": "Task"},
                }}],
            })
        )

        # Mock get issue
        respx.get(f"{API_BASE}/issue/MIX-1").mock(
            return_value=httpx.Response(200, json={
                "id": "99999",
                "key": "MIX-1",
                "fields": {
                    "summary": "Mixed test issue",
                    "status": {"name": "Open"},
                    "assignee": None,
                    "priority": {"name": "Low"},
                    "description": None,
                    "issuetype": {"name": "Task"},
                    "created": "2024-06-01T10:00:00.000Z",
                    "updated": "2024-06-01T12:00:00.000Z",
                    "labels": [],
                    "components": [],
                },
            })
        )

        # Mock list projects
        respx.get(f"{API_BASE}/project/search").mock(
            return_value=httpx.Response(200, json={
                "values": [{"id": "1", "key": "MIX", "name": "Mixed"}],
                "total": 1,
            })
        )

        search_handler = get_handler("jira_search_issues")
        get_handler_fn = get_handler("jira_get_issue")
        list_handler = get_handler("jira_list_projects")

        tasks = []
        for _ in range(30):
            tasks.append(search_handler(jql="project = MIX"))
        for _ in range(30):
            tasks.append(get_handler_fn(issue_key="MIX-1"))
        for _ in range(20):
            tasks.append(list_handler())

        results = await asyncio.gather(*tasks)
        assert len(results) == 80

        # Verify all results are valid JSON
        for result in results:
            parsed = json.loads(result)
            assert "error" not in parsed
