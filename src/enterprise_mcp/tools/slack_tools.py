"""Slack MCP tools — 6 tools for Slack Web API operations."""

import json
import logging
from typing import Any

from mcp.types import Tool

from ..connectors.slack import SlackConnector
from .registry import register_tool

logger = logging.getLogger(__name__)


def register_slack_tools(connector: SlackConnector) -> None:
    """Register all Slack tools with the tool registry.

    Args:
        connector: Configured SlackConnector instance.
    """
    # ------------------------------------------------------------------ #
    # slack_post_message
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="slack_post_message",
            description=(
                "Send a message to a Slack channel. Supports plain text and "
                "optional Block Kit blocks for rich formatting."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID or name (e.g., '#incidents' or 'C1234567890')",
                    },
                    "text": {
                        "type": "string",
                        "description": "Message text (plain text)",
                    },
                    "thread_ts": {
                        "type": "string",
                        "description": "Thread timestamp to reply in a thread",
                        "default": "",
                    },
                },
                "required": ["channel", "text"],
            },
        ),
        _make_post_message(connector),
    )

    # ------------------------------------------------------------------ #
    # slack_get_channel_history
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="slack_get_channel_history",
            description=(
                "Fetch recent message history from a Slack channel. "
                "Returns messages with text, timestamps, and user IDs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID (e.g., 'C1234567890')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of messages to return (max 1000)",
                        "default": 50,
                    },
                    "oldest": {
                        "type": "string",
                        "description": "Only messages after this Unix timestamp",
                        "default": "",
                    },
                },
                "required": ["channel"],
            },
        ),
        _make_get_channel_history(connector),
    )

    # ------------------------------------------------------------------ #
    # slack_list_channels
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="slack_list_channels",
            description=(
                "List all Slack channels accessible to the bot, "
                "including public and private channels."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "exclude_archived": {
                        "type": "boolean",
                        "description": "Whether to exclude archived channels",
                        "default": True,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of channels to return",
                        "default": 200,
                    },
                },
                "required": [],
            },
        ),
        _make_list_channels(connector),
    )

    # ------------------------------------------------------------------ #
    # slack_get_user_info
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="slack_get_user_info",
            description=(
                "Get profile information about a Slack user including "
                "display name, real name, email, and current status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "Slack user ID (e.g., 'U1234567890')",
                    },
                },
                "required": ["user_id"],
            },
        ),
        _make_get_user_info(connector),
    )

    # ------------------------------------------------------------------ #
    # slack_add_reaction
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="slack_add_reaction",
            description=(
                "Add an emoji reaction to a Slack message. "
                "Common reactions: 'white_check_mark', 'eyes', 'sos', 'rotating_light'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID containing the message",
                    },
                    "timestamp": {
                        "type": "string",
                        "description": "Message timestamp (ts field from the message)",
                    },
                    "emoji_name": {
                        "type": "string",
                        "description": "Emoji name without colons (e.g., 'thumbsup', 'white_check_mark')",
                    },
                },
                "required": ["channel", "timestamp", "emoji_name"],
            },
        ),
        _make_add_reaction(connector),
    )

    # ------------------------------------------------------------------ #
    # slack_create_thread_reply
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="slack_create_thread_reply",
            description="Post a reply in an existing Slack thread.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID containing the thread",
                    },
                    "thread_ts": {
                        "type": "string",
                        "description": "Timestamp of the parent message (thread root)",
                    },
                    "text": {
                        "type": "string",
                        "description": "Reply message text",
                    },
                },
                "required": ["channel", "thread_ts", "text"],
            },
        ),
        _make_create_thread_reply(connector),
    )


# ---- Handler factory functions ------------------------------------------ #


def _make_post_message(connector: SlackConnector) -> Any:
    async def handler(channel: str, text: str, thread_ts: str = "") -> str:
        try:
            result = await connector.post_message(channel, text, thread_ts)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"slack_post_message failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_get_channel_history(connector: SlackConnector) -> Any:
    async def handler(channel: str, limit: int = 50, oldest: str = "") -> str:
        try:
            result = await connector.get_channel_history(channel, limit, oldest)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"slack_get_channel_history failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_list_channels(connector: SlackConnector) -> Any:
    async def handler(exclude_archived: bool = True, max_results: int = 200) -> str:
        try:
            result = await connector.list_channels(exclude_archived, max_results=max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"slack_list_channels failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_get_user_info(connector: SlackConnector) -> Any:
    async def handler(user_id: str) -> str:
        try:
            result = await connector.get_user_info(user_id)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"slack_get_user_info failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_add_reaction(connector: SlackConnector) -> Any:
    async def handler(channel: str, timestamp: str, emoji_name: str) -> str:
        try:
            result = await connector.add_reaction(channel, timestamp, emoji_name)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"slack_add_reaction failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_create_thread_reply(connector: SlackConnector) -> Any:
    async def handler(channel: str, thread_ts: str, text: str) -> str:
        try:
            result = await connector.create_thread_reply(channel, thread_ts, text)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"slack_create_thread_reply failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler
