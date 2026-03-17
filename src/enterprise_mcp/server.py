"""Enterprise MCP Server — main entry point.

Exposes 40 tools across Jira, GitHub, Confluence, Slack, PagerDuty, Datadog, and Recipes
to Claude agents via the Model Context Protocol (MCP).

Usage:
    python -m enterprise_mcp.server
    # or via the installed CLI:
    enterprise-mcp
"""

import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import settings
from .connectors.confluence import ConfluenceConnector
from .connectors.datadog import DatadogConnector
from .connectors.github import GitHubConnector
from .connectors.jira import JiraConnector
from .connectors.pagerduty import PagerDutyConnector
from .connectors.slack import SlackConnector
from .observability import get_logger, setup_logging, traced_tool_call
from .tools.confluence_tools import register_confluence_tools
from .tools.datadog_tools import register_datadog_tools
from .tools.github_tools import register_github_tools
from .tools.jira_tools import register_jira_tools
from .tools.pagerduty_tools import register_pagerduty_tools
from .tools.recipe_tools import register_recipe_tools
from .tools.registry import get_all_tools, get_handler, tool_count
from .tools.slack_tools import register_slack_tools

# ---- Logging setup ------------------------------------------------------- #

setup_logging(log_level=settings.log_level, json_output=True)
logger = get_logger(__name__)

# ---- MCP Server ---------------------------------------------------------- #

app = Server(settings.server_name)

# ---- Connector initialisation -------------------------------------------- #

_connectors_ready = False


def _init_connectors() -> None:
    """Initialise connectors and register tools (called once on first request)."""
    global _connectors_ready
    if _connectors_ready:
        return

    active: list[str] = []

    if settings.jira_base_url and settings.jira_email and settings.jira_api_token:
        jira = JiraConnector(
            settings.jira_base_url, settings.jira_email, settings.jira_api_token
        )
        register_jira_tools(jira)
        active.append("Jira (8 tools)")
    else:
        logger.warning("connector_disabled", service="jira", reason="credentials not configured")

    if settings.github_token:
        github = GitHubConnector(settings.github_token, settings.github_default_owner)
        register_github_tools(github)
        active.append("GitHub (8 tools)")
    else:
        logger.warning("connector_disabled", service="github", reason="token not configured")

    if (
        settings.confluence_base_url
        and settings.confluence_email
        and settings.confluence_api_token
    ):
        confluence = ConfluenceConnector(
            settings.confluence_base_url,
            settings.confluence_email,
            settings.confluence_api_token,
        )
        register_confluence_tools(confluence)
        active.append("Confluence (6 tools)")
    else:
        logger.warning("connector_disabled", service="confluence", reason="credentials not configured")

    if settings.slack_bot_token:
        slack = SlackConnector(settings.slack_bot_token)
        register_slack_tools(slack)
        active.append("Slack (6 tools)")
    else:
        logger.warning("connector_disabled", service="slack", reason="token not configured")

    if settings.pagerduty_api_key:
        pagerduty = PagerDutyConnector(
            settings.pagerduty_api_key, settings.pagerduty_from_email
        )
        register_pagerduty_tools(pagerduty)
        active.append("PagerDuty (5 tools)")
    else:
        logger.warning("connector_disabled", service="pagerduty", reason="API key not configured")

    if settings.datadog_api_key and settings.datadog_app_key:
        datadog = DatadogConnector(
            settings.datadog_api_key, settings.datadog_app_key, settings.datadog_site
        )
        register_datadog_tools(datadog)
        active.append("Datadog (5 tools)")
    else:
        logger.warning("connector_disabled", service="datadog", reason="API keys not configured")

    # Always register recipe tools (they delegate to connector tools at runtime)
    register_recipe_tools()
    active.append("Recipes (2 tools)")

    _connectors_ready = True
    logger.info(
        "server_ready",
        tool_count=tool_count(),
        connectors=", ".join(active) if active else "none",
    )


# ---- MCP Handlers -------------------------------------------------------- #


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return all registered tool definitions."""
    _init_connectors()
    tools = get_all_tools()
    logger.debug("list_tools", count=len(tools))
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Dispatch a tool call to the appropriate handler with tracing."""
    _init_connectors()
    handler = get_handler(name)

    if handler is None:
        error_msg = f"Unknown tool: {name!r}. Available tools: {[t.name for t in get_all_tools()]}"
        logger.error("unknown_tool", tool_name=name)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

    try:
        result = await traced_tool_call(name, handler, **arguments)
        if not isinstance(result, str):
            result = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=result)]
    except Exception as exc:
        logger.exception("tool_call_exception", tool_name=name)
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]


# ---- Entry point --------------------------------------------------------- #


def main() -> None:
    """Run the Enterprise MCP Server over stdio."""
    import asyncio

    logger.info("server_starting", server_name=settings.server_name)
    asyncio.run(_run())


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    main()
