"""Jira webhook event handlers."""

from typing import Any

import structlog

logger = structlog.get_logger("webhooks.jira")


def handle_jira_event(event: dict[str, Any]) -> dict[str, Any]:
    """Process a Jira webhook event and extract structured data."""
    event_type = event.get("webhookEvent", "")
    payload = event

    if event_type == "jira:issue_created":
        issue = payload.get("issue", {})
        return {
            "action": "created",
            "issue_key": issue.get("key", ""),
            "summary": issue.get("fields", {}).get("summary", ""),
            "issue_type": issue.get("fields", {}).get("issuetype", {}).get("name", ""),
            "priority": issue.get("fields", {}).get("priority", {}).get("name", ""),
            "assignee": issue.get("fields", {}).get("assignee", {}).get("displayName", ""),
            "project": issue.get("fields", {}).get("project", {}).get("key", ""),
        }

    elif event_type == "jira:issue_updated":
        issue = payload.get("issue", {})
        changelog = payload.get("changelog", {})
        changes = []
        for item in changelog.get("items", []):
            changes.append({
                "field": item.get("field", ""),
                "from": item.get("fromString", ""),
                "to": item.get("toString", ""),
            })
        return {
            "action": "updated",
            "issue_key": issue.get("key", ""),
            "summary": issue.get("fields", {}).get("summary", ""),
            "changes": changes,
        }

    elif event_type == "comment_created":
        issue = payload.get("issue", {})
        comment = payload.get("comment", {})
        return {
            "action": "commented",
            "issue_key": issue.get("key", ""),
            "author": comment.get("author", {}).get("displayName", ""),
            "body": comment.get("body", ""),
        }

    return {"action": "unknown", "event_type": event_type}
