"""Demo MCP server — uses mock connectors for zero-config evaluation."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from ..tools.confluence_tools import register_confluence_tools
from ..tools.datadog_tools import register_datadog_tools
from ..tools.github_tools import register_github_tools
from ..tools.jira_tools import register_jira_tools
from ..tools.pagerduty_tools import register_pagerduty_tools
from ..tools.registry import get_all_tools, get_handler, tool_count
from ..tools.slack_tools import register_slack_tools
from .mock_connectors import (
    MockConfluenceConnector,
    MockDatadogConnector,
    MockGitHubConnector,
    MockJiraConnector,
    MockPagerDutyConnector,
    MockSlackConnector,
)

app = Server("enterprise-mcp-demo")
_ready = False


def _init_demo() -> None:
    global _ready
    if _ready:
        return

    register_jira_tools(MockJiraConnector())  # type: ignore[arg-type]
    register_github_tools(MockGitHubConnector())  # type: ignore[arg-type]
    register_confluence_tools(MockConfluenceConnector())  # type: ignore[arg-type]
    register_slack_tools(MockSlackConnector())  # type: ignore[arg-type]
    register_pagerduty_tools(MockPagerDutyConnector())  # type: ignore[arg-type]
    register_datadog_tools(MockDatadogConnector())  # type: ignore[arg-type]

    _ready = True


@app.list_tools()
async def list_tools() -> list[Tool]:
    _init_demo()
    return get_all_tools()


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    _init_demo()
    handler = get_handler(name)
    if handler is None:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name!r}"}))]
    try:
        result = await handler(**arguments)
        if not isinstance(result, str):
            result = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=result)]
    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> None:
    asyncio.run(_run())
