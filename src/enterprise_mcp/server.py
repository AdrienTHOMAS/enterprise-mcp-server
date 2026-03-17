"""Enterprise MCP Server — main entry point.

Exposes 28 tools across Jira, GitHub, Confluence, and Slack to
Claude agents via the Model Context Protocol (MCP).

Usage:
    python -m enterprise_mcp.server
    # or via the installed CLI:
    enterprise-mcp
"""

import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import settings
from .connectors.confluence import ConfluenceConnector
from .connectors.github import GitHubConnector
from .connectors.jira import JiraConnector
from .connectors.slack import SlackConnector
from .tools.confluence_tools import register_confluence_tools
from .tools.github_tools import register_github_tools
from .tools.jira_tools import register_jira_tools
from .tools.registry import get_all_tools, get_handler, tool_count
from .tools.slack_tools import register_slack_tools

# ---- Logging setup ------------------------------------------------------- #

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

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
        logger.warning("Jira credentials not configured — Jira tools disabled")

    if settings.github_token:
        github = GitHubConnector(settings.github_token, settings.github_default_owner)
        register_github_tools(github)
        active.append("GitHub (8 tools)")
    else:
        logger.warning("GitHub token not configured — GitHub tools disabled")

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
        logger.warning("Confluence credentials not configured — Confluence tools disabled")

    if settings.slack_bot_token:
        slack = SlackConnector(settings.slack_bot_token)
        register_slack_tools(slack)
        active.append("Slack (6 tools)")
    else:
        logger.warning("Slack bot token not configured — Slack tools disabled")

    _connectors_ready = True
    logger.info(
        f"Enterprise MCP Server ready — {tool_count()} tools from: "
        + (", ".join(active) if active else "no connectors configured")
    )


# ---- MCP Handlers -------------------------------------------------------- #


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return all registered tool definitions."""
    _init_connectors()
    tools = get_all_tools()
    logger.debug(f"list_tools() returning {len(tools)} tools")
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Dispatch a tool call to the appropriate handler.

    Args:
        name: Tool name as registered in the tool registry.
        arguments: Tool input arguments as provided by the MCP client.

    Returns:
        List containing a single TextContent with the JSON result.
    """
    _init_connectors()
    handler = get_handler(name)

    if handler is None:
        error_msg = f"Unknown tool: {name!r}. Available tools: {[t.name for t in get_all_tools()]}"
        logger.error(error_msg)
        return [TextContent(type="text", text=f'{{"error": "{error_msg}"}}')]

    logger.info(f"Calling tool: {name} with args: {list(arguments.keys())}")
    try:
        result = await handler(**arguments)
        if not isinstance(result, str):
            import json
            result = json.dumps(result, indent=2, default=str)
        return [TextContent(type="text", text=result)]
    except Exception as exc:
        import json
        logger.exception(f"Tool {name!r} raised an exception")
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]


# ---- Entry point --------------------------------------------------------- #


def main() -> None:
    """Run the Enterprise MCP Server over stdio."""
    import asyncio

    logger.info(f"Starting {settings.server_name} MCP server …")
    asyncio.run(_run())


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    main()
