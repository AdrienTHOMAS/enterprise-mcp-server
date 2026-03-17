"""Shared fixtures and configuration for the Enterprise MCP Server test suite."""

import pytest
import respx
import httpx


# ---- Jira fixtures ------------------------------------------------------- #

JIRA_BASE = "https://test.atlassian.net"
JIRA_ISSUE_KEY = "PROJ-123"
GITHUB_ORG = "test-org"
GITHUB_REPO = "test-repo"
CONFLUENCE_BASE = "https://test.atlassian.net"
SLACK_CHANNEL = "C12345"


@pytest.fixture
def jira_issue_payload() -> dict:
    return {
        "id": "10000",
        "key": JIRA_ISSUE_KEY,
        "fields": {
            "summary": "Payment service returns 500 errors",
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "Alice Smith", "emailAddress": "alice@test.com"},
            "priority": {"name": "P1"},
            "description": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Critical bug in payment flow."}],
                    }
                ],
            },
            "issuetype": {"name": "Bug"},
            "created": "2024-01-15T10:00:00.000Z",
            "updated": "2024-01-15T12:00:00.000Z",
            "labels": ["production", "payments"],
            "components": [],
        },
    }


@pytest.fixture
def jira_search_payload() -> dict:
    return {
        "total": 1,
        "maxResults": 50,
        "startAt": 0,
        "issues": [
            {
                "id": "10000",
                "key": JIRA_ISSUE_KEY,
                "fields": {
                    "summary": "Payment service returns 500 errors",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "Alice Smith"},
                    "priority": {"name": "P1"},
                    "issuetype": {"name": "Bug"},
                    "created": "2024-01-15T10:00:00.000Z",
                    "updated": "2024-01-15T12:00:00.000Z",
                },
            }
        ],
    }


@pytest.fixture
def jira_create_payload() -> dict:
    return {
        "id": "10001",
        "key": "PROJ-124",
        "self": f"{JIRA_BASE}/rest/api/3/issue/10001",
    }


@pytest.fixture
def jira_comment_payload() -> dict:
    return {
        "id": "10100",
        "author": {"displayName": "Bot User"},
        "body": {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Test comment."}]}],
        },
        "created": "2024-01-15T13:00:00.000Z",
    }


# ---- GitHub fixtures ----------------------------------------------------- #


@pytest.fixture
def github_repo_payload() -> dict:
    return {
        "id": 1,
        "name": GITHUB_REPO,
        "full_name": f"{GITHUB_ORG}/{GITHUB_REPO}",
        "description": "Test repository",
        "stargazers_count": 42,
        "forks_count": 5,
        "open_issues_count": 3,
        "default_branch": "main",
        "topics": ["python", "microservice"],
        "html_url": f"https://github.com/{GITHUB_ORG}/{GITHUB_REPO}",
    }


@pytest.fixture
def github_issues_payload() -> list:
    return [
        {
            "number": 1,
            "title": "Payment timeout on checkout",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignee": None,
            "created_at": "2024-01-15T09:00:00Z",
            "updated_at": "2024-01-15T11:00:00Z",
            "html_url": f"https://github.com/{GITHUB_ORG}/{GITHUB_REPO}/issues/1",
            "body": "Users report timeout errors.",
        }
    ]


@pytest.fixture
def github_pr_payload() -> dict:
    return {
        "number": 42,
        "title": "Fix payment timeout",
        "state": "open",
        "body": "Fixes the timeout issue in the payment flow.",
        "user": {"login": "alice"},
        "head": {"ref": "fix/payment-timeout", "sha": "abc123"},
        "base": {"ref": "main"},
        "created_at": "2024-01-15T08:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
        "html_url": f"https://github.com/{GITHUB_ORG}/{GITHUB_REPO}/pull/42",
        "mergeable": True,
        "additions": 15,
        "deletions": 3,
        "changed_files": 2,
        "reviews": [],
    }


# ---- Confluence fixtures ------------------------------------------------- #


@pytest.fixture
def confluence_page_payload() -> dict:
    return {
        "id": "98765",
        "title": "Incident Response Runbook",
        "status": "current",
        "version": {"number": 3},
        "body": {
            "storage": {
                "value": "<p>Follow these steps during an incident...</p>",
                "representation": "storage",
            }
        },
        "_links": {"webui": "/wiki/spaces/OPS/pages/98765"},
    }


@pytest.fixture
def confluence_search_payload() -> dict:
    return {
        "results": [
            {
                "id": "98765",
                "title": "Incident Response Runbook",
                "type": "page",
                "excerpt": "Follow these steps during an incident...",
                "_links": {"webui": "/wiki/spaces/OPS/pages/98765"},
            }
        ],
        "totalSize": 1,
        "limit": 25,
        "start": 0,
    }


@pytest.fixture
def confluence_spaces_payload() -> dict:
    return {
        "results": [
            {
                "id": "11111",
                "key": "OPS",
                "name": "Operations",
                "type": "global",
                "status": "current",
            },
            {
                "id": "22222",
                "key": "ENG",
                "name": "Engineering",
                "type": "global",
                "status": "current",
            },
        ],
        "_links": {"next": None},
    }


# ---- Slack fixtures ------------------------------------------------------ #


@pytest.fixture
def slack_post_payload() -> dict:
    return {
        "ok": True,
        "channel": SLACK_CHANNEL,
        "ts": "1705312800.000001",
        "message": {"text": "Incident update posted."},
    }


@pytest.fixture
def slack_history_payload() -> dict:
    return {
        "ok": True,
        "messages": [
            {
                "type": "message",
                "user": "U12345",
                "text": "We have a P1 incident on payment-service",
                "ts": "1705312700.000001",
            },
            {
                "type": "message",
                "user": "U67890",
                "text": "On it, checking logs now",
                "ts": "1705312750.000001",
            },
        ],
        "has_more": False,
    }


@pytest.fixture
def slack_channels_payload() -> dict:
    return {
        "ok": True,
        "channels": [
            {"id": SLACK_CHANNEL, "name": "incidents", "is_member": True, "num_members": 45},
            {"id": "C99999", "name": "general", "is_member": True, "num_members": 120},
        ],
        "response_metadata": {"next_cursor": ""},
    }


@pytest.fixture
def slack_user_payload() -> dict:
    return {
        "ok": True,
        "user": {
            "id": "U12345",
            "name": "alice.smith",
            "profile": {
                "display_name": "Alice Smith",
                "real_name": "Alice Smith",
                "email": "alice@test.com",
                "status_text": "On-call",
            },
        },
    }
