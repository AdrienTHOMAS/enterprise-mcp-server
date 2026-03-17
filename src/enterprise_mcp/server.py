"""Enterprise MCP Server — main entry point.

Exposes 38 tools across Jira, GitHub, Confluence, Slack, PagerDuty, and Datadog
to Claude agents via the Model Context Protocol (MCP).

Usage:
    python -m enterprise_mcp.server
    # or via the installed CLI:
    enterprise-mcp
"""

import json
import time
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .audit import get_audit_logger, register_audit_tools
from .config import settings
from .observability import get_logger, setup_logging, traced_tool_call
from .tools.registry import get_all_tools, get_handler, tool_count

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

    if settings.enterprise_mcp_demo:
        # Demo mode: use mock connectors — zero API keys needed
        from .demo.mock_connectors import (
            MockConfluenceConnector,
            MockDatadogConnector,
            MockGitHubConnector,
            MockJiraConnector,
            MockPagerDutyConnector,
            MockSlackConnector,
        )
        from .tools.confluence_tools import register_confluence_tools
        from .tools.datadog_tools import register_datadog_tools
        from .tools.github_tools import register_github_tools
        from .tools.jira_tools import register_jira_tools
        from .tools.pagerduty_tools import register_pagerduty_tools
        from .tools.slack_tools import register_slack_tools

        register_jira_tools(MockJiraConnector())  # type: ignore[arg-type]
        register_github_tools(MockGitHubConnector())  # type: ignore[arg-type]
        register_confluence_tools(MockConfluenceConnector())  # type: ignore[arg-type]
        register_slack_tools(MockSlackConnector())  # type: ignore[arg-type]
        register_pagerduty_tools(MockPagerDutyConnector())  # type: ignore[arg-type]
        register_datadog_tools(MockDatadogConnector())  # type: ignore[arg-type]
        active.append("DEMO MODE (all 6 connectors with mock data)")
    else:
        # Production mode: conditionally register based on env vars
        from .connectors.confluence import ConfluenceConnector
        from .connectors.datadog import DatadogConnector
        from .connectors.github import GitHubConnector
        from .connectors.jira import JiraConnector
        from .connectors.pagerduty import PagerDutyConnector
        from .connectors.slack import SlackConnector
        from .tools.confluence_tools import register_confluence_tools
        from .tools.datadog_tools import register_datadog_tools
        from .tools.github_tools import register_github_tools
        from .tools.jira_tools import register_jira_tools
        from .tools.pagerduty_tools import register_pagerduty_tools
        from .tools.slack_tools import register_slack_tools

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

    # Register enterprise tools (audit, plugins)
    register_audit_tools()

    from .plugins.registry import register_plugin_tools
    register_plugin_tools()

    _connectors_ready = True
    logger.info(
        "server_ready",
        tool_count=tool_count(),
        connectors=", ".join(active) if active else "none",
        demo_mode=settings.enterprise_mcp_demo,
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
    """Dispatch a tool call to the appropriate handler with tracing and audit logging."""
    _init_connectors()
    handler = get_handler(name)

    if handler is None:
        error_msg = f"Unknown tool: {name!r}. Available tools: {[t.name for t in get_all_tools()]}"
        logger.error("unknown_tool", tool_name=name)
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

    audit = get_audit_logger()
    start = time.monotonic()
    try:
        result = await traced_tool_call(name, handler, **arguments)
        if not isinstance(result, str):
            result = json.dumps(result, indent=2, default=str)
        duration_ms = (time.monotonic() - start) * 1000
        audit.log_tool_call(
            tool_name=name, input_params=arguments, output=result,
            duration_ms=duration_ms, success=True,
        )
        return [TextContent(type="text", text=result)]
    except Exception as exc:
        duration_ms = (time.monotonic() - start) * 1000
        audit.log_tool_call(
            tool_name=name, input_params=arguments, output="",
            duration_ms=duration_ms, success=False, error=str(exc),
        )
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
