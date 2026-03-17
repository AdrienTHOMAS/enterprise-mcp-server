"""Base connector abstract class."""

import logging
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base class for all enterprise system connectors.

    Subclasses must implement `_get_client()` which returns a configured
    `httpx.AsyncClient` for their respective API.
    """

    _client: httpx.AsyncClient | None = None

    @abstractmethod
    async def _get_client(self) -> httpx.AsyncClient:
        """Return a configured async HTTP client for this connector."""
        ...

    async def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BaseConnector":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    @staticmethod
    def _raise_for_status(response: httpx.Response, context: str = "") -> None:
        """Raise a descriptive error for non-2xx HTTP responses.

        Args:
            response: The HTTP response to check.
            context: Optional context string for error messages.
        """
        if response.is_success:
            return
        msg = f"HTTP {response.status_code}"
        if context:
            msg = f"{context}: {msg}"
        try:
            body = response.json()
            if "errorMessages" in body:
                msg += f" — {'; '.join(body['errorMessages'])}"
            elif "message" in body:
                msg += f" — {body['message']}"
        except Exception:
            msg += f" — {response.text[:200]}"
        logger.error(msg)
        response.raise_for_status()
