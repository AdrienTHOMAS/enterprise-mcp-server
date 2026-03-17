"""Datadog MCP tools — 5 tools for Datadog monitoring operations."""

import json
import logging
from typing import Any

from mcp.types import Tool

from ..connectors.datadog import DatadogConnector
from .registry import register_tool

logger = logging.getLogger(__name__)


def register_datadog_tools(connector: DatadogConnector) -> None:
    """Register all Datadog tools with the tool registry."""

    register_tool(
        Tool(
            name="datadog_get_metrics",
            description=(
                "Query time series metrics from Datadog. "
                "Example query: 'avg:system.cpu.user{env:prod} by {host}'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Datadog metrics query string",
                    },
                    "from_ts": {
                        "type": "integer",
                        "description": "Start time as Unix epoch seconds",
                    },
                    "to_ts": {
                        "type": "integer",
                        "description": "End time as Unix epoch seconds",
                    },
                },
                "required": ["query", "from_ts", "to_ts"],
            },
        ),
        _make_get_metrics(connector),
    )

    register_tool(
        Tool(
            name="datadog_list_monitors",
            description="List Datadog monitors with optional name, tag, and type filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Filter monitors by name (substring match)",
                        "default": "",
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags to filter by",
                        "default": "",
                    },
                    "monitor_type": {
                        "type": "string",
                        "description": "Filter by type (metric, service check, etc.)",
                        "default": "",
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of monitors per page",
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
        _make_list_monitors(connector),
    )

    register_tool(
        Tool(
            name="datadog_get_monitor_status",
            description="Get the current status and configuration of a Datadog monitor by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitor_id": {
                        "type": "integer",
                        "description": "Numeric Datadog monitor ID",
                    },
                },
                "required": ["monitor_id"],
            },
        ),
        _make_get_monitor_status(connector),
    )

    register_tool(
        Tool(
            name="datadog_create_event",
            description=(
                "Create a Datadog event for tracking deployments, alerts, or notable occurrences. "
                "Alert types: 'error', 'warning', 'info', 'success'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Event title",
                    },
                    "text": {
                        "type": "string",
                        "description": "Event description (supports Markdown)",
                    },
                    "alert_type": {
                        "type": "string",
                        "description": "Event type: error, warning, info, or success",
                        "default": "info",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags (e.g., ['env:prod', 'service:payment'])",
                    },
                },
                "required": ["title", "text"],
            },
        ),
        _make_create_event(connector),
    )

    register_tool(
        Tool(
            name="datadog_search_logs",
            description=(
                "Search Datadog logs using the log search query syntax. "
                "Example: 'service:payment-api status:error @http.status_code:500'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Log search query (Datadog syntax)",
                    },
                    "from_ts": {
                        "type": "string",
                        "description": "Start time (ISO 8601 or relative like 'now-1h')",
                        "default": "now-1h",
                    },
                    "to_ts": {
                        "type": "string",
                        "description": "End time (ISO 8601 or relative like 'now')",
                        "default": "now",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of log entries to return",
                        "default": 50,
                    },
                },
                "required": ["query"],
            },
        ),
        _make_search_logs(connector),
    )


def _make_get_metrics(connector: DatadogConnector) -> Any:
    async def handler(query: str, from_ts: int, to_ts: int) -> str:
        try:
            result = await connector.get_metrics(query, from_ts, to_ts)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"datadog_get_metrics failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_list_monitors(connector: DatadogConnector) -> Any:
    async def handler(
        name: str = "",
        tags: str = "",
        monitor_type: str = "",
        page_size: int = 50,
    ) -> str:
        try:
            result = await connector.list_monitors(name, tags, monitor_type, page_size=page_size)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"datadog_list_monitors failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_get_monitor_status(connector: DatadogConnector) -> Any:
    async def handler(monitor_id: int) -> str:
        try:
            result = await connector.get_monitor_status(monitor_id)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"datadog_get_monitor_status failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_create_event(connector: DatadogConnector) -> Any:
    async def handler(
        title: str,
        text: str,
        alert_type: str = "info",
        tags: list[str] | None = None,
    ) -> str:
        try:
            result = await connector.create_event(title, text, alert_type, tags)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"datadog_create_event failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_search_logs(connector: DatadogConnector) -> Any:
    async def handler(
        query: str,
        from_ts: str = "now-1h",
        to_ts: str = "now",
        limit: int = 50,
    ) -> str:
        try:
            result = await connector.search_logs(query, from_ts, to_ts, limit)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"datadog_search_logs failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler
