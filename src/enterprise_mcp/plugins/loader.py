"""Dynamic plugin loader — discovers and loads plugins from local dirs and entry points."""

from __future__ import annotations

import importlib
import json
import logging
import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from ..tools.registry import register_tool
from .base import ConnectorPlugin, ToolPlugin

logger = logging.getLogger(__name__)

PLUGIN_DIR = Path.home() / ".enterprise-mcp" / "plugins"
ENTRY_POINT_GROUP = "enterprise_mcp.connectors"

_loaded_plugins: list[ConnectorPlugin | ToolPlugin] = []


def discover_plugins() -> list[ConnectorPlugin | ToolPlugin]:
    """Discover plugins from the local directory and Python entry points."""
    plugins: list[ConnectorPlugin | ToolPlugin] = []

    # 1. Load from local plugin directory
    plugins.extend(_load_from_directory(PLUGIN_DIR))

    # 2. Load from Python entry points
    plugins.extend(_load_from_entry_points())

    return plugins


def _load_from_directory(plugin_dir: Path) -> list[ConnectorPlugin | ToolPlugin]:
    """Load plugins from ~/.enterprise-mcp/plugins/."""
    plugins: list[ConnectorPlugin | ToolPlugin] = []
    if not plugin_dir.is_dir():
        return plugins

    for child in plugin_dir.iterdir():
        if not child.is_dir():
            continue
        plugin_json = child / "plugin.json"
        if not plugin_json.exists():
            continue
        try:
            meta = json.loads(plugin_json.read_text())
            module_name = meta.get("module", child.name)
            entry_class = meta.get("class", "Plugin")

            # Add plugin dir to sys.path if needed
            if str(child) not in sys.path:
                sys.path.insert(0, str(child))

            mod = importlib.import_module(module_name)
            cls = getattr(mod, entry_class)
            instance = cls()
            plugins.append(instance)
            logger.info(f"Loaded plugin from directory: {child.name}")
        except Exception as exc:
            logger.error(f"Failed to load plugin from {child}: {exc}")

    return plugins


def _load_from_entry_points() -> list[ConnectorPlugin | ToolPlugin]:
    """Load plugins registered as Python entry points."""
    plugins: list[ConnectorPlugin | ToolPlugin] = []
    try:
        eps = entry_points()
        group = eps.get(ENTRY_POINT_GROUP, []) if isinstance(eps, dict) else eps.select(group=ENTRY_POINT_GROUP)
    except Exception:
        return plugins

    for ep in group:
        try:
            cls = ep.load()
            instance = cls()
            plugins.append(instance)
            logger.info(f"Loaded plugin from entry point: {ep.name}")
        except Exception as exc:
            logger.error(f"Failed to load entry point plugin {ep.name}: {exc}")

    return plugins


async def load_and_register_plugins(config: dict[str, Any] | None = None) -> int:
    """Discover, initialize, and register all plugin tools. Returns count of new tools."""
    global _loaded_plugins
    plugins = discover_plugins()
    tool_count = 0

    for plugin in plugins:
        try:
            if isinstance(plugin, ConnectorPlugin):
                await plugin.initialize(config or {})

            for tool_def, handler in plugin.get_tools():
                register_tool(tool_def, handler)
                tool_count += 1
                logger.info(f"Registered plugin tool: {tool_def.name} (from {plugin.name})")

            _loaded_plugins.append(plugin)
        except Exception as exc:
            logger.error(f"Failed to register plugin {plugin.name}: {exc}")

    return tool_count


def get_loaded_plugins() -> list[ConnectorPlugin | ToolPlugin]:
    return list(_loaded_plugins)
