"""End-to-end test simulating a Claude agent using the MCP tools."""

import json

import httpx
import pytest
import respx

from enterprise_mcp.connectors.github import GitHubConnector
from enterprise_mcp.connectors.jira import JiraConnector
from enterprise_mcp.connectors.slack import SlackConnector
from enterprise_mcp.tools.github_tools import register_github_tools
from enterprise_mcp.tools.jira_tools import register_jira_tools
from enterprise_mcp.tools.registry import _TOOL_DEFINITIONS, _TOOL_REGISTRY, get_handler
from enterprise_mcp.tools.slack_tools import register_slack_tools

JIRA_BASE = "https://agent-test.atlassian.net"
JIRA_API = f"{JIRA_BASE}/rest/api/3"
GITHUB_API = "https://api.github.com"
SLACK_API = "https://slack.com/api"


@pytest.fixture(autouse=True)
def clean_registry():
    """Clean the tool registry between tests."""
    _TOOL_REGISTRY.clear()
    _TOOL_DEFINITIONS.clear()
    yield
    _TOOL_REGISTRY.clear()
    _TOOL_DEFINITIONS.clear()


@pytest.fixture
def setup_tools():
    """Register all tools with mock connectors."""
    jira = JiraConnector(JIRA_BASE, "bot@test.com", "token")
    github = GitHubConnector("ghp_test", "test-org")
    slack = SlackConnector("xoxb-test")

    register_jira_tools(jira)
    register_github_tools(github)
    register_slack_tools(slack)


@pytest.mark.asyncio
async def test_incident_triage_workflow(setup_tools):
    """Simulate a Claude agent triaging an incident:
    1. Search Jira for the incident
    2. Check GitHub for recent PRs
    3. Post status update to Slack
    """
    with respx.mock:
        # Mock Jira search
        respx.post(f"{JIRA_API}/search").mock(
            return_value=httpx.Response(200, json={
                "total": 1,
                "maxResults": 50,
                "startAt": 0,
                "issues": [{
                    "key": "INC-42",
                    "fields": {
                        "summary": "Payment service 500 errors",
                        "status": {"name": "Open"},
                        "priority": {"name": "P1"},
                        "issuetype": {"name": "Incident"},
                    },
                }],
            })
        )

        # Mock GitHub PRs
        respx.get(f"{GITHUB_API}/repos/test-org/payment-service/pulls").mock(
            return_value=httpx.Response(200, json=[{
                "number": 99,
                "title": "Hotfix: connection pool exhaustion",
                "state": "open",
                "user": {"login": "engineer1"},
                "head": {"ref": "hotfix/conn-pool"},
                "base": {"ref": "main"},
                "created_at": "2024-06-15T08:00:00Z",
            }])
        )

        # Mock Slack post
        respx.post(f"{SLACK_API}/chat.postMessage").mock(
            return_value=httpx.Response(200, json={
                "ok": True,
                "channel": "C-incidents",
                "ts": "1718438400.000001",
                "message": {"text": "Incident triage update"},
            })
        )

        # Step 1: Search Jira for incidents
        jira_handler = get_handler("jira_search_issues")
        assert jira_handler is not None
        jira_result = json.loads(await jira_handler(jql='project = INC AND priority = P1'))
        assert jira_result["total"] == 1
        assert jira_result["issues"][0]["key"] == "INC-42"

        # Step 2: Check recent PRs on payment-service
        github_handler = get_handler("github_list_pull_requests")
        assert github_handler is not None
        github_result = json.loads(await github_handler(repo="payment-service"))
        assert len(github_result) == 1
        assert github_result[0]["title"] == "Hotfix: connection pool exhaustion"

        # Step 3: Post status to Slack
        slack_handler = get_handler("slack_post_message")
        assert slack_handler is not None
        slack_result = json.loads(await slack_handler(
            channel="C-incidents",
            text="Incident INC-42: Payment 500s. Hotfix PR #99 is open.",
        ))
        assert slack_result["ok"] is True


@pytest.mark.asyncio
async def test_all_tools_registered(setup_tools):
    """Verify that all expected tools are registered and have handlers."""
    expected_jira_tools = [
        "jira_get_issue", "jira_search_issues", "jira_create_issue",
        "jira_update_issue", "jira_add_comment", "jira_get_sprint",
        "jira_list_projects", "jira_get_board",
    ]
    expected_github_tools = [
        "github_get_repo", "github_list_issues", "github_create_issue",
        "github_get_pull_request", "github_list_pull_requests",
        "github_search_code", "github_get_file_content", "github_create_review_comment",
    ]
    expected_slack_tools = [
        "slack_post_message", "slack_get_channel_history", "slack_list_channels",
        "slack_get_user_info", "slack_add_reaction", "slack_create_thread_reply",
    ]

    for tool_name in expected_jira_tools + expected_github_tools + expected_slack_tools:
        handler = get_handler(tool_name)
        assert handler is not None, f"Tool {tool_name} has no handler"
