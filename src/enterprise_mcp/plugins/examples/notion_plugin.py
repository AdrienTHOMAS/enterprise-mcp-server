"""Example Notion connector plugin — shows the plugin pattern for custom connectors.

This plugin demonstrates how to build a connector plugin that integrates
with the Enterprise MCP Server plugin system. Install it by placing in
~/.enterprise-mcp/plugins/notion/ with a plugin.json, or register as
a Python entry point under the 'enterprise_mcp.connectors' group.

Usage as entry point in pyproject.toml:
    [project.entry-points."enterprise_mcp.connectors"]
    notion = "enterprise_mcp.plugins.examples.notion_plugin:NotionPlugin"
"""

from __future__ import annotations

from typing import Any

import httpx
from mcp.types import Tool

from ..base import ConnectorPlugin


class NotionConnector:
    """Async Notion API client."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.notion.com/v1",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def search(self, query: str, page_size: int = 10) -> dict[str, Any]:
        client = await self._get_client()
        resp = await client.post("/search", json={"query": query, "page_size": page_size})
        resp.raise_for_status()
        return resp.json()

    async def get_page(self, page_id: str) -> dict[str, Any]:
        client = await self._get_client()
        resp = await client.get(f"/pages/{page_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_database(self, database_id: str) -> dict[str, Any]:
        client = await self._get_client()
        resp = await client.get(f"/databases/{database_id}")
        resp.raise_for_status()
        return resp.json()

    async def query_database(
        self, database_id: str, filter: dict[str, Any] | None = None, page_size: int = 100,
    ) -> dict[str, Any]:
        client = await self._get_client()
        body: dict[str, Any] = {"page_size": page_size}
        if filter:
            body["filter"] = filter
        resp = await client.post(f"/databases/{database_id}/query", json=body)
        resp.raise_for_status()
        return resp.json()

    async def create_page(
        self, parent_id: str, title: str, properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()
        body: dict[str, Any] = {
            "parent": {"database_id": parent_id},
            "properties": properties or {
                "Name": {"title": [{"text": {"content": title}}]},
            },
        }
        resp = await client.post("/pages", json=body)
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class NotionPlugin(ConnectorPlugin):
    """Notion connector plugin for Enterprise MCP Server.

    Provides 5 tools:
    - notion_search: Search across Notion workspace
    - notion_get_page: Get a Notion page by ID
    - notion_get_database: Get a Notion database schema
    - notion_query_database: Query a Notion database with filters
    - notion_create_page: Create a new page in a database
    """

    def __init__(self) -> None:
        self._connector: NotionConnector | None = None

    @property
    def name(self) -> str:
        return "notion"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def initialize(self, config: dict[str, Any]) -> None:
        api_key = config.get("NOTION_API_KEY", "")
        if not api_key:
            import os
            api_key = os.environ.get("NOTION_API_KEY", "")
        if not api_key:
            raise ValueError("NOTION_API_KEY is required for the Notion plugin")
        self._connector = NotionConnector(api_key)

    def get_tools(self) -> list[tuple[Tool, Any]]:
        c = self._connector
        if c is None:
            return []

        async def search_handler(query: str, page_size: int = 10) -> dict[str, Any]:
            return await c.search(query, page_size)

        async def get_page_handler(page_id: str) -> dict[str, Any]:
            return await c.get_page(page_id)

        async def get_database_handler(database_id: str) -> dict[str, Any]:
            return await c.get_database(database_id)

        async def query_database_handler(
            database_id: str, page_size: int = 100,
        ) -> dict[str, Any]:
            return await c.query_database(database_id, page_size=page_size)

        async def create_page_handler(
            parent_database_id: str, title: str,
        ) -> dict[str, Any]:
            return await c.create_page(parent_database_id, title)

        return [
            (
                Tool(
                    name="notion_search",
                    description="Search across your Notion workspace for pages and databases",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "page_size": {"type": "integer", "description": "Max results (default 10)", "default": 10},
                        },
                        "required": ["query"],
                    },
                ),
                search_handler,
            ),
            (
                Tool(
                    name="notion_get_page",
                    description="Get a Notion page by ID with all properties",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page_id": {"type": "string", "description": "Notion page ID"},
                        },
                        "required": ["page_id"],
                    },
                ),
                get_page_handler,
            ),
            (
                Tool(
                    name="notion_get_database",
                    description="Get a Notion database schema and metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_id": {"type": "string", "description": "Notion database ID"},
                        },
                        "required": ["database_id"],
                    },
                ),
                get_database_handler,
            ),
            (
                Tool(
                    name="notion_query_database",
                    description="Query a Notion database to list pages with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_id": {"type": "string", "description": "Notion database ID"},
                            "page_size": {"type": "integer", "description": "Max results (default 100)", "default": 100},
                        },
                        "required": ["database_id"],
                    },
                ),
                query_database_handler,
            ),
            (
                Tool(
                    name="notion_create_page",
                    description="Create a new page in a Notion database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "parent_database_id": {"type": "string", "description": "Parent database ID"},
                            "title": {"type": "string", "description": "Page title"},
                        },
                        "required": ["parent_database_id", "title"],
                    },
                ),
                create_page_handler,
            ),
        ]

    async def close(self) -> None:
        if self._connector:
            await self._connector.close()

    async def health_check(self) -> dict[str, Any]:
        if self._connector is None:
            return {"status": "not_initialized"}
        try:
            await self._connector.search("health_check", page_size=1)
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
