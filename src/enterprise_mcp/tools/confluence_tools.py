"""Confluence MCP tools — 6 tools for Confluence Cloud operations."""

import json
import logging
from typing import Any

from mcp.types import Tool

from ..connectors.confluence import ConfluenceConnector
from .registry import register_tool

logger = logging.getLogger(__name__)


def register_confluence_tools(connector: ConfluenceConnector) -> None:
    """Register all Confluence tools with the tool registry.

    Args:
        connector: Configured ConfluenceConnector instance.
    """
    # ------------------------------------------------------------------ #
    # confluence_get_page
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="confluence_get_page",
            description=(
                "Fetch the content of a Confluence page by its ID. "
                "Returns the page title, body (storage format), version, and metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Confluence page ID (numeric string)",
                    },
                    "include_body": {
                        "type": "boolean",
                        "description": "Whether to include page body content",
                        "default": True,
                    },
                },
                "required": ["page_id"],
            },
        ),
        _make_get_page(connector),
    )

    # ------------------------------------------------------------------ #
    # confluence_search
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="confluence_search",
            description=(
                "Search Confluence content using CQL (Confluence Query Language) or plain text. "
                "Example CQL: 'type = page AND title ~ \"incident response\" AND space = OPS'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "CQL query or plain text search term",
                    },
                    "space_key": {
                        "type": "string",
                        "description": "Restrict search to this space key",
                        "default": "",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 25,
                    },
                },
                "required": ["query"],
            },
        ),
        _make_search(connector),
    )

    # ------------------------------------------------------------------ #
    # confluence_create_page
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="confluence_create_page",
            description="Create a new page in a Confluence space.",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_id": {
                        "type": "string",
                        "description": "ID of the target Confluence space",
                    },
                    "title": {
                        "type": "string",
                        "description": "Page title",
                    },
                    "body": {
                        "type": "string",
                        "description": "Page content in wiki markup format",
                    },
                    "parent_page_id": {
                        "type": "string",
                        "description": "ID of the parent page (optional)",
                        "default": "",
                    },
                },
                "required": ["space_id", "title", "body"],
            },
        ),
        _make_create_page(connector),
    )

    # ------------------------------------------------------------------ #
    # confluence_update_page
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="confluence_update_page",
            description=(
                "Update the content of an existing Confluence page. "
                "The version number must be the current version + 1."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Confluence page ID to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "New page title",
                    },
                    "body": {
                        "type": "string",
                        "description": "New page content in wiki markup format",
                    },
                    "version_number": {
                        "type": "integer",
                        "description": "New version number (must be current version + 1)",
                    },
                },
                "required": ["page_id", "title", "body", "version_number"],
            },
        ),
        _make_update_page(connector),
    )

    # ------------------------------------------------------------------ #
    # confluence_list_spaces
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="confluence_list_spaces",
            description="List all accessible Confluence spaces with their keys, names, and types.",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of spaces to return",
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
        _make_list_spaces(connector),
    )

    # ------------------------------------------------------------------ #
    # confluence_get_children
    # ------------------------------------------------------------------ #
    register_tool(
        Tool(
            name="confluence_get_children",
            description="Get the child pages of a Confluence page.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Parent page ID",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of child pages to return",
                        "default": 25,
                    },
                },
                "required": ["page_id"],
            },
        ),
        _make_get_children(connector),
    )


# ---- Handler factory functions ------------------------------------------ #


def _make_get_page(connector: ConfluenceConnector) -> Any:
    async def handler(page_id: str, include_body: bool = True) -> str:
        try:
            result = await connector.get_page(page_id, include_body)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"confluence_get_page failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_search(connector: ConfluenceConnector) -> Any:
    async def handler(query: str, space_key: str = "", max_results: int = 25) -> str:
        try:
            result = await connector.search(query, space_key, max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"confluence_search failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_create_page(connector: ConfluenceConnector) -> Any:
    async def handler(
        space_id: str, title: str, body: str, parent_page_id: str = ""
    ) -> str:
        try:
            result = await connector.create_page(space_id, title, body, parent_page_id)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"confluence_create_page failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_update_page(connector: ConfluenceConnector) -> Any:
    async def handler(
        page_id: str, title: str, body: str, version_number: int
    ) -> str:
        try:
            result = await connector.update_page(page_id, title, body, version_number)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"confluence_update_page failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_list_spaces(connector: ConfluenceConnector) -> Any:
    async def handler(max_results: int = 50) -> str:
        try:
            result = await connector.list_spaces(max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"confluence_list_spaces failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler


def _make_get_children(connector: ConfluenceConnector) -> Any:
    async def handler(page_id: str, max_results: int = 25) -> str:
        try:
            result = await connector.get_children(page_id, max_results)
            return json.dumps(result, indent=2, default=str)
        except Exception as exc:
            logger.error(f"confluence_get_children failed: {exc}")
            return json.dumps({"error": str(exc)})

    return handler
