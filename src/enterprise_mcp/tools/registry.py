"""Tool registry with auto-discovery of all MCP tools."""

import logging
from collections.abc import Callable
from typing import Any

from mcp.types import Tool

logger = logging.getLogger(__name__)

_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {}
_TOOL_DEFINITIONS: list[Tool] = []


def register_tool(tool: Tool, handler: Callable[..., Any]) -> None:
    """Register a tool definition and its handler function.

    Args:
        tool: MCP Tool definition with name, description, and input schema.
        handler: Async callable that handles tool invocations.
    """
    _TOOL_REGISTRY[tool.name] = handler
    _TOOL_DEFINITIONS.append(tool)
    logger.debug(f"Registered tool: {tool.name}")


def get_all_tools() -> list[Tool]:
    """Return all registered tool definitions.

    Returns:
        List of MCP Tool objects ready for the list_tools response.
    """
    return list(_TOOL_DEFINITIONS)


def get_handler(tool_name: str) -> Callable[..., Any] | None:
    """Look up a tool handler by name.

    Args:
        tool_name: Name of the registered tool.

    Returns:
        The handler callable, or None if not found.
    """
    return _TOOL_REGISTRY.get(tool_name)


def tool_count() -> int:
    """Return the total number of registered tools."""
    return len(_TOOL_DEFINITIONS)
