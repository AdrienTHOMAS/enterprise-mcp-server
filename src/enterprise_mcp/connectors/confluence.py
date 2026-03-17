"""Confluence Cloud REST API v2 connector."""

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseConnector

logger = logging.getLogger(__name__)


class ConfluenceConnector(BaseConnector):
    """Confluence Cloud REST API v2 connector.

    Authenticates via Basic Auth (email + API token) and provides methods
    for reading and writing Confluence pages and spaces.
    """

    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        """Initialize the Confluence connector.

        Args:
            base_url: Confluence Cloud base URL (e.g., https://yourcompany.atlassian.net).
            email: Confluence user email address.
            api_token: Atlassian API token.
        """
        self.base_url = base_url.rstrip("/")
        self._auth = (email, api_token)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return a lazily-initialized async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=f"{self.base_url}/wiki/api/v2",
                auth=self._auth,
                headers={
                    "Accept": "application/json",
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
    async def get_page(
        self, page_id: str, include_body: bool = True
    ) -> dict[str, Any]:
        """Fetch a Confluence page by its ID.

        Args:
            page_id: Confluence page ID (numeric string).
            include_body: Whether to include the page body content. Defaults to True.

        Returns:
            Page data including title, body (HTML/storage format), version, and metadata.
        """
        client = await self._get_client()
        params: dict[str, Any] = {}
        if include_body:
            params["body-format"] = "storage"

        response = await client.get(f"/pages/{page_id}", params=params)
        self._raise_for_status(response, f"get_page({page_id})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search(
        self, query: str, space_key: str = "", max_results: int = 25
    ) -> dict[str, Any]:
        """Search Confluence content using CQL (Confluence Query Language).

        Args:
            query: CQL query or plain text to search for.
            space_key: Restrict search to a specific space key.
            max_results: Maximum number of results to return.

        Returns:
            Search results with page titles, excerpts, and URLs.
        """
        client = await self._get_client()
        cql = query
        if space_key and "space" not in query.lower():
            cql = f'space = "{space_key}" AND ({query})'

        # Use v1 search endpoint (CQL is not available in v2)
        v1_client = httpx.AsyncClient(
            base_url=f"{self.base_url}/wiki/rest/api",
            auth=self._auth,
            headers={"Accept": "application/json"},
            timeout=30.0,
        )
        try:
            response = await v1_client.get(
                "/search",
                params={"cql": cql, "limit": min(max_results, 50)},
            )
            self._raise_for_status(response, f"search({cql!r})")
            return response.json()
        finally:
            await v1_client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_page(
        self,
        space_id: str,
        title: str,
        body: str,
        parent_page_id: str = "",
        body_format: str = "wiki",
    ) -> dict[str, Any]:
        """Create a new Confluence page.

        Args:
            space_id: ID of the space to create the page in.
            title: Page title.
            body: Page content (in wiki markup or storage format).
            parent_page_id: ID of the parent page (optional, creates at space root).
            body_format: Format of the body content ('wiki' or 'storage').

        Returns:
            Created page data including ID, URL, version, and metadata.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "spaceId": space_id,
            "status": "current",
            "title": title,
            "body": {
                "representation": body_format,
                "value": body,
            },
        }
        if parent_page_id:
            payload["parentId"] = parent_page_id

        response = await client.post("/pages", json=payload)
        self._raise_for_status(response, f"create_page({title!r})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        version_number: int,
        body_format: str = "wiki",
    ) -> dict[str, Any]:
        """Update an existing Confluence page.

        Args:
            page_id: Confluence page ID to update.
            title: New page title.
            body: New page content.
            version_number: Current version number (must be incremented by 1).
            body_format: Format of the body content ('wiki' or 'storage').

        Returns:
            Updated page data including new version number.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "id": page_id,
            "status": "current",
            "title": title,
            "body": {
                "representation": body_format,
                "value": body,
            },
            "version": {"number": version_number},
        }
        response = await client.put(f"/pages/{page_id}", json=payload)
        self._raise_for_status(response, f"update_page({page_id})")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def list_spaces(self, max_results: int = 50) -> dict[str, Any]:
        """List all accessible Confluence spaces.

        Args:
            max_results: Maximum number of spaces to return.

        Returns:
            List of spaces with keys, names, types, and homepages.
        """
        client = await self._get_client()
        response = await client.get(
            "/spaces",
            params={"limit": min(max_results, 250), "status": "current"},
        )
        self._raise_for_status(response, "list_spaces")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_children(
        self, page_id: str, max_results: int = 25
    ) -> dict[str, Any]:
        """Get child pages of a Confluence page.

        Args:
            page_id: Parent page ID.
            max_results: Maximum number of child pages to return.

        Returns:
            List of child pages with titles, IDs, and URLs.
        """
        client = await self._get_client()
        response = await client.get(
            f"/pages/{page_id}/children",
            params={"limit": min(max_results, 250)},
        )
        self._raise_for_status(response, f"get_children({page_id})")
        return response.json()
