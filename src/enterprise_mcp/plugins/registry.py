"""Plugin registry — register, list, enable/disable plugins at runtime."""

from __future__ import annotations

import json
from typing import Any

from .base import ConnectorPlugin, ToolPlugin
from .loader import get_loaded_plugins

# ── Registry state ───────────────────────────────────────────────────

_disabled_plugins: set[str] = set()


class PluginRegistry:
    """Central registry for managing plugin lifecycle."""

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return metadata for all discovered plugins."""
        plugins = get_loaded_plugins()
        result: list[dict[str, Any]] = []
        for plugin in plugins:
            tool_count = len(plugin.get_tools())
            result.append({
                "name": plugin.name,
                "version": plugin.version,
                "type": "connector" if isinstance(plugin, ConnectorPlugin) else "tool",
                "enabled": plugin.name not in _disabled_plugins,
                "tool_count": tool_count,
            })
        return result

    def enable(self, plugin_name: str) -> bool:
        """Enable a previously disabled plugin. Returns True if state changed."""
        if plugin_name in _disabled_plugins:
            _disabled_plugins.discard(plugin_name)
            return True
        return False

    def disable(self, plugin_name: str) -> bool:
        """Disable a plugin by name. Returns True if state changed."""
        plugins = get_loaded_plugins()
        for plugin in plugins:
            if plugin.name == plugin_name:
                _disabled_plugins.add(plugin_name)
                return True
        return False

    def is_enabled(self, plugin_name: str) -> bool:
        return plugin_name not in _disabled_plugins


# ── Module-level singleton ───────────────────────────────────────────

_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


# ── MCP tool registration ────────────────────────────────────────────

def register_plugin_tools() -> None:
    """Register the list_plugins MCP tool."""
    from mcp.types import Tool

    from ..tools.registry import register_tool

    register_tool(
        Tool(
            name="list_plugins",
            description=(
                "List all available and enabled plugins with version info. "
                "Shows connector and tool plugins discovered from entry points "
                "and the local plugin directory."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        _make_list_plugins_handler(),
    )


def _make_list_plugins_handler():  # type: ignore[no-untyped-def]
    async def handler() -> str:
        registry = get_registry()
        plugins = registry.list_plugins()
        return json.dumps({
            "plugins": plugins,
            "total": len(plugins),
            "enabled": sum(1 for p in plugins if p["enabled"]),
        }, indent=2)

    return handler
