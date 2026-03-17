"""Plugin system for extending Enterprise MCP Server with custom connectors."""

from .base import ConnectorPlugin, ToolPlugin
from .loader import discover_plugins, load_and_register_plugins
from .registry import PluginRegistry, get_registry

__all__ = [
    "ConnectorPlugin",
    "ToolPlugin",
    "PluginRegistry",
    "discover_plugins",
    "get_registry",
    "load_and_register_plugins",
]
