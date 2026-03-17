"""PagerDuty MCP tools — 5 tools for PagerDuty incident management."""

import json
import logging
from typing import Any

from mcp.types import Tool

from ..connectors.pagerduty import PagerDutyConnector
from .registry import register_tool

logger = logging.getLogger(__name__)


def register_pagerduty_tools(connector: PagerDutyConnector) -> None:
    """Register all PagerDuty tools with the tool registry."""

    register_tool(
        Tool(
            name="pagerduty_get_incident",
            description="Get detailed information about a PagerDuty incident by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "PagerDuty incident ID",
                    },
                },
                "required": ["incident_id"],
            },
        ),
        _make_get_incident(connector),
    )

    register_tool(
        Tool(
            name="pagerduty_list_incidents",
            description=(
                "List PagerDuty incidents filtered by status, urgency, and date range. "
                "Statuses: 'triggered', 'acknowledged', 'resolved'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "statuses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status (triggered, acknowledged, resolved)",
                    },
                    "urgencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by urgency (high, low)",
                    },
                    "since": {
                        "type": "string",
                        "description": "Start of date range (ISO 8601)",
                        "default": "",
                    },
                    "until": {
                        "type": "string",
                        "description": "End of date range (ISO 8601)",
                        "default": "",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of incidents to return",
                        "default": 25,
                    },
                },
                "required": [],
            },
        ),
        _make_list_incidents(connector),
    )

    register_tool(
        Tool(
            name="pagerduty_acknowledge_incident",
            description="Acknowledge a PagerDuty incident to indicate it is being worked on.",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "PagerDuty incident ID",
                    },
                    "from_email": {
                        "type": "string",
                        "description": "Email of the user acknowledging the incident",
                        "default": "",
                    },
                },
                "required": ["incident_id"],
            },
        ),
        _make_acknowledge_incident(connector),
    )

    register_tool(
        Tool(
            name="pagerduty_resolve_incident",
            description="Resolve a PagerDuty incident to mark it as resolved.",
            inputSchema={
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "PagerDuty incident ID",
                    },
                    "from_email": {
                        "type": "string",
                        "description": "Email of the user resolving the incident",
                        "default": "",
                    },
                },
                "required": ["incident_id"],
            },
        ),
        _make_resolve_incident(connector),
    )

    register_tool(
        Tool(
            name="pagerduty_create_incident",
            description="Create a new PagerDuty incident on a specified service.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Incident title",
                    },
                    "service_id": {
                        "type": "string",
                        "description": "PagerDuty service ID to create the incident on",
                    },
                    "urgency": {
                        "type": "string",
                        "description": "Urgency level ('high' or 'low')",
                        "default": "high",
                    },
                    "body": {
                        "type": "string",
                        "description": "Incident body/details",
                        "default": "",
                    },
                    "from_email": {
                        "type": "string",
                        "description": "Email of the user creating the incident",
                        "default": "",
                    },
                },
                "required": ["title", "service_id"],
            },
        ),
        _make_create_incident(connector),
    )


def _make_get_incident(connector: PagerDutyConnector) -> Any:
    async def handler(incident_id: str) -> str:
        try:
            result = await connector.get_incident(incident_id)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"pagerduty_get_incident failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_list_incidents(connector: PagerDutyConnector) -> Any:
    async def handler(
        statuses: list[str] | None = None,
        urgencies: list[str] | None = None,
        since: str = "",
        until: str = "",
        limit: int = 25,
    ) -> str:
        try:
            result = await connector.list_incidents(statuses, urgencies, since, until, limit)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"pagerduty_list_incidents failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_acknowledge_incident(connector: PagerDutyConnector) -> Any:
    async def handler(incident_id: str, from_email: str = "") -> str:
        try:
            result = await connector.acknowledge_incident(incident_id, from_email)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"pagerduty_acknowledge_incident failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_resolve_incident(connector: PagerDutyConnector) -> Any:
    async def handler(incident_id: str, from_email: str = "") -> str:
        try:
            result = await connector.resolve_incident(incident_id, from_email)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"pagerduty_resolve_incident failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_create_incident(connector: PagerDutyConnector) -> Any:
    async def handler(
        title: str,
        service_id: str,
        urgency: str = "high",
        body: str = "",
        from_email: str = "",
    ) -> str:
        try:
            result = await connector.create_incident(title, service_id, urgency, body, from_email)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"pagerduty_create_incident failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler
