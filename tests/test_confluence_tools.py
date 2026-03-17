"""Tests for the Confluence connector and tools."""

import httpx
import pytest
import respx

from enterprise_mcp.connectors.confluence import ConfluenceConnector

CONFLUENCE_BASE = "https://test.atlassian.net"
API_V2_BASE = f"{CONFLUENCE_BASE}/wiki/api/v2"
API_V1_BASE = f"{CONFLUENCE_BASE}/wiki/rest/api"
PAGE_ID = "98765"


# ---- get_page ------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_get_page_success(confluence_page_payload):
    """get_page returns page content on HTTP 200."""
    async with respx.mock:
        respx.get(f"{API_V2_BASE}/pages/{PAGE_ID}").mock(
            return_value=httpx.Response(200, json=confluence_page_payload)
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        result = await connector.get_page(PAGE_ID)

    assert result["id"] == PAGE_ID
    assert result["title"] == "Incident Response Runbook"
    assert "body" in result


@pytest.mark.asyncio
async def test_get_page_not_found():
    """get_page raises HTTPStatusError on HTTP 404."""
    async with respx.mock:
        respx.get(f"{API_V2_BASE}/pages/99999").mock(
            return_value=httpx.Response(404, json={"message": "Page not found"})
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_page("99999")


@pytest.mark.asyncio
async def test_get_page_rate_limit():
    """get_page raises HTTPStatusError on HTTP 429."""
    async with respx.mock:
        respx.get(f"{API_V2_BASE}/pages/{PAGE_ID}").mock(
            return_value=httpx.Response(429, json={"message": "Rate limit exceeded"})
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_page(PAGE_ID)


@pytest.mark.asyncio
async def test_get_page_server_error():
    """get_page raises HTTPStatusError on HTTP 500."""
    async with respx.mock:
        respx.get(f"{API_V2_BASE}/pages/{PAGE_ID}").mock(
            return_value=httpx.Response(500, json={"message": "Internal server error"})
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.get_page(PAGE_ID)


# ---- search -------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_search_success(confluence_search_payload):
    """search returns matching pages on HTTP 200."""
    async with respx.mock:
        respx.get(f"{API_V1_BASE}/search").mock(
            return_value=httpx.Response(200, json=confluence_search_payload)
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        result = await connector.search("incident response runbook")

    assert result["totalSize"] == 1
    assert result["results"][0]["title"] == "Incident Response Runbook"


@pytest.mark.asyncio
async def test_search_empty():
    """search returns empty results when no pages match."""
    async with respx.mock:
        respx.get(f"{API_V1_BASE}/search").mock(
            return_value=httpx.Response(200, json={"results": [], "totalSize": 0, "limit": 25, "start": 0})
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        result = await connector.search("nonexistent page xyzzy")

    assert result["totalSize"] == 0
    assert result["results"] == []


# ---- create_page --------------------------------------------------------- #


@pytest.mark.asyncio
async def test_create_page_success():
    """create_page returns the new page on HTTP 200."""
    new_page = {
        "id": "12345",
        "title": "New Runbook",
        "status": "current",
        "version": {"number": 1},
        "_links": {"webui": "/wiki/spaces/OPS/pages/12345"},
    }
    async with respx.mock:
        respx.post(f"{API_V2_BASE}/pages").mock(
            return_value=httpx.Response(200, json=new_page)
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        result = await connector.create_page("11111", "New Runbook", "h1. Runbook content")

    assert result["id"] == "12345"
    assert result["title"] == "New Runbook"


@pytest.mark.asyncio
async def test_create_page_bad_request():
    """create_page raises HTTPStatusError on HTTP 400."""
    async with respx.mock:
        respx.post(f"{API_V2_BASE}/pages").mock(
            return_value=httpx.Response(400, json={"message": "Title is required"})
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.create_page("11111", "", "body content")


# ---- list_spaces --------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_spaces_success(confluence_spaces_payload):
    """list_spaces returns available spaces on HTTP 200."""
    async with respx.mock:
        respx.get(f"{API_V2_BASE}/spaces").mock(
            return_value=httpx.Response(200, json=confluence_spaces_payload)
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        result = await connector.list_spaces()

    assert len(result["results"]) == 2
    keys = [s["key"] for s in result["results"]]
    assert "OPS" in keys
    assert "ENG" in keys


# ---- get_children -------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_children_success():
    """get_children returns child pages on HTTP 200."""
    children = {
        "results": [
            {"id": "11111", "title": "Runbook v2"},
            {"id": "22222", "title": "Post-mortem template"},
        ],
        "_links": {"next": None},
    }
    async with respx.mock:
        respx.get(f"{API_V2_BASE}/pages/{PAGE_ID}/children").mock(
            return_value=httpx.Response(200, json=children)
        )
        connector = ConfluenceConnector(CONFLUENCE_BASE, "user@test.com", "token")
        result = await connector.get_children(PAGE_ID)

    assert len(result["results"]) == 2
