"""PagerDuty REST API v2 connector."""

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseConnector

logger = structlog.get_logger("connectors.pagerduty")


class PagerDutyConnector(BaseConnector):
    """PagerDuty REST API v2 connector.

    Authenticates via API key (v2 REST API token) and provides methods
    for incident management operations with automatic retry logic.
    """

    BASE_URL = "https://api.pagerduty.com"

    def __init__(self, api_key: str, default_from_email: str = "") -> None:
        self._api_key = api_key
        self.default_from_email = default_from_email
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Token token={self._api_key}",
                    "Accept": "application/vnd.pagerduty+json;version=2",
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
    async def get_incident(self, incident_id: str) -> dict[str, Any]:
        """Fetch a PagerDuty incident by ID.

        Args:
            incident_id: PagerDuty incident ID.

        Returns:
            Incident details including status, urgency, assignments.
        """
        client = await self._get_client()
        response = await client.get(f"/incidents/{incident_id}")
        self._raise_for_status(response, f"get_incident({incident_id})")
        return response.json().get("incident", response.json())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def list_incidents(
        self,
        statuses: list[str] | None = None,
        urgencies: list[str] | None = None,
        since: str = "",
        until: str = "",
        limit: int = 25,
    ) -> dict[str, Any]:
        """List PagerDuty incidents with filters.

        Args:
            statuses: Filter by status (triggered, acknowledged, resolved).
            urgencies: Filter by urgency (high, low).
            since: Start of date range (ISO 8601).
            until: End of date range (ISO 8601).
            limit: Maximum number of incidents to return.

        Returns:
            List of incidents with pagination metadata.
        """
        client = await self._get_client()
        params: dict[str, Any] = {"limit": min(limit, 100), "sort_by": "created_at:desc"}
        if statuses:
            params["statuses[]"] = statuses
        if urgencies:
            params["urgencies[]"] = urgencies
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        response = await client.get("/incidents", params=params)
        self._raise_for_status(response, "list_incidents")
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def acknowledge_incident(
        self, incident_id: str, from_email: str = ""
    ) -> dict[str, Any]:
        """Acknowledge a PagerDuty incident.

        Args:
            incident_id: PagerDuty incident ID.
            from_email: Email of the user acknowledging (required by PagerDuty API).

        Returns:
            Updated incident data.
        """
        client = await self._get_client()
        email = from_email or self.default_from_email
        response = await client.put(
            f"/incidents/{incident_id}",
            json={
                "incident": {
                    "type": "incident_reference",
                    "status": "acknowledged",
                }
            },
            headers={"From": email},
        )
        self._raise_for_status(response, f"acknowledge_incident({incident_id})")
        return response.json().get("incident", response.json())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def resolve_incident(
        self, incident_id: str, from_email: str = ""
    ) -> dict[str, Any]:
        """Resolve a PagerDuty incident.

        Args:
            incident_id: PagerDuty incident ID.
            from_email: Email of the user resolving.

        Returns:
            Updated incident data.
        """
        client = await self._get_client()
        email = from_email or self.default_from_email
        response = await client.put(
            f"/incidents/{incident_id}",
            json={
                "incident": {
                    "type": "incident_reference",
                    "status": "resolved",
                }
            },
            headers={"From": email},
        )
        self._raise_for_status(response, f"resolve_incident({incident_id})")
        return response.json().get("incident", response.json())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_incident(
        self,
        title: str,
        service_id: str,
        urgency: str = "high",
        body: str = "",
        from_email: str = "",
    ) -> dict[str, Any]:
        """Create a new PagerDuty incident.

        Args:
            title: Incident title.
            service_id: PagerDuty service ID to create the incident on.
            urgency: Incident urgency ('high' or 'low').
            body: Incident body/details.
            from_email: Email of the user creating the incident.

        Returns:
            Created incident data.
        """
        client = await self._get_client()
        email = from_email or self.default_from_email
        incident: dict[str, Any] = {
            "type": "incident",
            "title": title,
            "urgency": urgency,
            "service": {"id": service_id, "type": "service_reference"},
        }
        if body:
            incident["body"] = {"type": "incident_body", "details": body}

        response = await client.post(
            "/incidents",
            json={"incident": incident},
            headers={"From": email},
        )
        self._raise_for_status(response, "create_incident")
        return response.json().get("incident", response.json())
