"""Datadog API v1/v2 connector."""

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseConnector

logger = structlog.get_logger("connectors.datadog")


class DatadogConnector(BaseConnector):
    """Datadog API v1/v2 connector.

    Authenticates via API key and Application key. Provides methods for
    querying metrics, monitors, and logs with automatic retry logic.
    """

    def __init__(
        self,
        api_key: str,
        app_key: str,
        site: str = "datadoghq.com",
    ) -> None:
        self._api_key = api_key
        self._app_key = app_key
        self._site = site
        self._base_url = f"https://api.{site}"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "DD-API-KEY": self._api_key,
                    "DD-APPLICATION-KEY": self._app_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_metrics(
        self,
        query: str,
        from_ts: int,
        to_ts: int,
    ) -> dict[str, Any]:
        """Query time series metrics from Datadog.

        Args:
            query: Datadog metrics query string (e.g., 'avg:system.cpu.user{*}').
            from_ts: Start time as Unix epoch seconds.
            to_ts: End time as Unix epoch seconds.

        Returns:
            Time series data with point values.
        """
        client = await self._get_client()
        response = await client.get(
            "/api/v1/query",
            params={"query": query, "from": from_ts, "to": to_ts},
        )
        self._raise_for_status(response, f"get_metrics({query!r})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def list_monitors(
        self,
        name: str = "",
        tags: str = "",
        monitor_type: str = "",
        page: int = 0,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        """List Datadog monitors with optional filters.

        Args:
            name: Filter monitors by name (substring match).
            tags: Comma-separated list of tags to filter by.
            monitor_type: Filter by monitor type (e.g., 'metric', 'service check').
            page: Page number for pagination.
            page_size: Number of monitors per page.

        Returns:
            List of monitors with details.
        """
        client = await self._get_client()
        params: dict[str, Any] = {"page": page, "page_size": min(page_size, 100)}
        if name:
            params["name"] = name
        if tags:
            params["monitor_tags"] = tags
        if monitor_type:
            params["type"] = monitor_type

        response = await client.get("/api/v1/monitor", params=params)
        self._raise_for_status(response, "list_monitors")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_monitor_status(self, monitor_id: int) -> dict[str, Any]:
        """Get the current status of a Datadog monitor.

        Args:
            monitor_id: Numeric monitor ID.

        Returns:
            Monitor details including current state and options.
        """
        client = await self._get_client()
        response = await client.get(f"/api/v1/monitor/{monitor_id}")
        self._raise_for_status(response, f"get_monitor_status({monitor_id})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_event(
        self,
        title: str,
        text: str,
        alert_type: str = "info",
        tags: list[str] | None = None,
        source_type_name: str = "enterprise-mcp",
    ) -> dict[str, Any]:
        """Create a Datadog event.

        Args:
            title: Event title.
            text: Event description (supports Markdown).
            alert_type: Event type: 'error', 'warning', 'info', or 'success'.
            tags: List of tags to attach (e.g., ['env:prod', 'service:payment']).
            source_type_name: Source type for the event.

        Returns:
            Created event data with ID.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "title": title,
            "text": text,
            "alert_type": alert_type,
            "source_type_name": source_type_name,
        }
        if tags:
            payload["tags"] = tags

        response = await client.post("/api/v1/events", json=payload)
        self._raise_for_status(response, "create_event")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search_logs(
        self,
        query: str,
        from_ts: str = "",
        to_ts: str = "",
        limit: int = 50,
        sort: str = "timestamp",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """Search Datadog logs.

        Args:
            query: Log search query (Datadog log search syntax).
            from_ts: Start time (ISO 8601 or relative like 'now-1h').
            to_ts: End time (ISO 8601 or relative like 'now').
            limit: Maximum number of log entries.
            sort: Field to sort by.
            sort_order: Sort order ('asc' or 'desc').

        Returns:
            Log search results with matching entries.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "filter": {"query": query, "from": from_ts or "now-1h", "to": to_ts or "now"},
            "sort": f"{sort}",
            "page": {"limit": min(limit, 1000)},
        }

        response = await client.post("/api/v2/logs/events/search", json=payload)
        self._raise_for_status(response, f"search_logs({query!r})")
        return response.json()
