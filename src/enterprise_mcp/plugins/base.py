"""Abstract base classes for connector and tool plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from mcp.types import Tool


class ConnectorPlugin(ABC):
    """Base class for custom connector plugins.

    Subclass this to create a connector for a new external service.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name (e.g., 'servicenow')."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version string."""
        ...

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the connector with configuration (e.g., API keys)."""
        ...

    @abstractmethod
    def get_tools(self) -> list[tuple[Tool, Any]]:
        """Return a list of (Tool definition, async handler) tuples to register."""
        ...

    async def close(self) -> None:
        """Clean up resources (optional override)."""
        pass

    async def health_check(self) -> dict[str, Any]:
        """Return health status (optional override)."""
        return {"status": "unknown"}


class ToolPlugin(ABC):
    """Base class for standalone tool plugins (no connector needed)."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        ...

    @abstractmethod
    def get_tools(self) -> list[tuple[Tool, Any]]:
        ...
