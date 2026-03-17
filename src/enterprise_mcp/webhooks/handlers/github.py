"""GitHub webhook event handlers."""

from typing import Any

import structlog

logger = structlog.get_logger("webhooks.github")


def handle_github_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Process a GitHub webhook event and extract structured data."""
    repo = payload.get("repository", {})
    sender = payload.get("sender", {})

    base = {
        "repository": repo.get("full_name", ""),
        "sender": sender.get("login", ""),
    }

    if event_type.startswith("pull_request"):
        pr = payload.get("pull_request", {})
        return {
            **base,
            "action": payload.get("action", ""),
            "pr_number": pr.get("number"),
            "pr_title": pr.get("title", ""),
            "pr_state": pr.get("state", ""),
            "head_branch": pr.get("head", {}).get("ref", ""),
            "base_branch": pr.get("base", {}).get("ref", ""),
            "author": pr.get("user", {}).get("login", ""),
        }

    elif event_type == "push":
        commits = payload.get("commits", [])
        return {
            **base,
            "action": "push",
            "ref": payload.get("ref", ""),
            "commit_count": len(commits),
            "head_commit": payload.get("head_commit", {}).get("message", ""),
            "pusher": payload.get("pusher", {}).get("name", ""),
        }

    elif event_type.startswith("review"):
        review = payload.get("review", {})
        pr = payload.get("pull_request", {})
        return {
            **base,
            "action": payload.get("action", ""),
            "pr_number": pr.get("number"),
            "review_state": review.get("state", ""),
            "reviewer": review.get("user", {}).get("login", ""),
            "body": review.get("body", ""),
        }

    return {**base, "action": "unknown", "event_type": event_type}
