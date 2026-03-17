"""Slack Events API webhook handlers."""

from typing import Any

import structlog

logger = structlog.get_logger("webhooks.slack")


def handle_slack_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Process a Slack Events API payload and extract structured data."""
    event = payload.get("event", {})
    event_type = event.get("type", "")

    base = {
        "team_id": payload.get("team_id", ""),
        "event_type": event_type,
    }

    if event_type == "message":
        return {
            **base,
            "channel": event.get("channel", ""),
            "user": event.get("user", ""),
            "text": event.get("text", ""),
            "ts": event.get("ts", ""),
            "thread_ts": event.get("thread_ts"),
            "subtype": event.get("subtype"),
        }

    elif event_type == "reaction_added":
        return {
            **base,
            "user": event.get("user", ""),
            "reaction": event.get("reaction", ""),
            "item_channel": event.get("item", {}).get("channel", ""),
            "item_ts": event.get("item", {}).get("ts", ""),
        }

    elif event_type == "channel_created":
        channel = event.get("channel", {})
        return {
            **base,
            "channel_id": channel.get("id", ""),
            "channel_name": channel.get("name", ""),
            "creator": channel.get("creator", ""),
        }

    elif event_type == "member_joined_channel":
        return {
            **base,
            "user": event.get("user", ""),
            "channel": event.get("channel", ""),
        }

    return {**base, "raw_event": event}
