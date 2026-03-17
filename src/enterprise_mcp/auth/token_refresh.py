"""Automatic token refresh for OAuth tokens."""

import asyncio
import time
from typing import Any

import httpx
import structlog

from .token_store import TokenStore

logger = structlog.get_logger("auth.token_refresh")


class TokenRefresher:
    """Automatically refreshes OAuth tokens before they expire.

    Supports Jira OAuth, Slack OAuth, and GitHub OAuth token refresh.
    Runs as a background task that checks token expiry periodically.
    """

    # Refresh 5 minutes before expiry
    REFRESH_BUFFER_SECONDS = 300

    def __init__(self, token_store: TokenStore) -> None:
        self._store = token_store
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def refresh_token(self, service: str) -> dict[str, Any] | None:
        """Refresh a token for a given service."""
        token_data = self._store.get_token(service)
        if token_data is None:
            return None

        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            logger.debug("no_refresh_token", service=service)
            return None

        token_url = token_data.get("token_url", "")
        client_id = token_data.get("client_id", "")
        client_secret = token_data.get("client_secret", "")

        if not token_url:
            logger.warning("no_token_url", service=service)
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                new_data = response.json()

            # Merge new token data with existing
            updated = {**token_data, **new_data}
            updated["refreshed_at"] = time.time()
            self._store.store_token(service, updated)
            logger.info("token_refreshed", service=service)
            return updated

        except Exception as exc:
            logger.error("token_refresh_failed", service=service, error=str(exc))
            return None

    def _needs_refresh(self, token_data: dict[str, Any]) -> bool:
        """Check if a token needs refreshing."""
        expires_at = token_data.get("expires_at")
        if expires_at is None:
            expires_in = token_data.get("expires_in")
            created_at = token_data.get("created_at", token_data.get("refreshed_at", 0))
            if expires_in and created_at:
                expires_at = created_at + expires_in
            else:
                return False

        return time.time() >= (expires_at - self.REFRESH_BUFFER_SECONDS)

    async def check_and_refresh_all(self) -> None:
        """Check all stored tokens and refresh any that are expiring."""
        for service in self._store.list_services():
            token_data = self._store.get_token(service)
            if token_data and self._needs_refresh(token_data):
                await self.refresh_token(service)

    async def start(self, check_interval: int = 60) -> None:
        """Start the background token refresh loop."""
        self._running = True

        async def _loop() -> None:
            while self._running:
                try:
                    await self.check_and_refresh_all()
                except Exception as exc:
                    logger.error("token_refresh_loop_error", error=str(exc))
                await asyncio.sleep(check_interval)

        self._task = asyncio.create_task(_loop())
        logger.info("token_refresher_started", interval=check_interval)

    async def stop(self) -> None:
        """Stop the background token refresh loop."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("token_refresher_stopped")
