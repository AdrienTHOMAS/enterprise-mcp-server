"""OAuth 2.0 flows for GitHub and other services."""

import time
from typing import Any

import httpx
import structlog

logger = structlog.get_logger("auth.oauth")


class GitHubOAuthFlow:
    """GitHub OAuth 2.0 device flow and web flow implementation."""

    DEVICE_CODE_URL = "https://github.com/login/device/code"
    ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"

    def __init__(self, client_id: str, client_secret: str = "") -> None:
        self.client_id = client_id
        self.client_secret = client_secret

    async def start_device_flow(self, scope: str = "repo,read:org") -> dict[str, Any]:
        """Initiate GitHub device authorization flow.

        Returns device_code, user_code, and verification_uri for the user
        to complete authorization in their browser.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.DEVICE_CODE_URL,
                data={"client_id": self.client_id, "scope": scope},
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            logger.info(
                "device_flow_started",
                user_code=data.get("user_code"),
                verification_uri=data.get("verification_uri"),
            )
            return data

    async def poll_device_flow(
        self,
        device_code: str,
        interval: int = 5,
        timeout: int = 900,
    ) -> dict[str, Any]:
        """Poll for device flow completion until user authorizes or timeout.

        Returns the access token response when authorization completes.
        """
        start_time = time.monotonic()
        async with httpx.AsyncClient() as client:
            while time.monotonic() - start_time < timeout:
                response = await client.post(
                    self.ACCESS_TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json"},
                )
                data = response.json()

                error = data.get("error")
                if error is None:
                    logger.info("device_flow_completed")
                    return data
                elif error == "authorization_pending":
                    import asyncio
                    await asyncio.sleep(interval)
                elif error == "slow_down":
                    interval += 5
                    import asyncio
                    await asyncio.sleep(interval)
                elif error == "expired_token":
                    raise RuntimeError("Device code expired. Please restart the flow.")
                elif error == "access_denied":
                    raise RuntimeError("User denied the authorization request.")
                else:
                    raise RuntimeError(f"OAuth error: {error} — {data.get('error_description', '')}")

        raise TimeoutError("Device flow authorization timed out")

    async def exchange_code(self, code: str, redirect_uri: str = "") -> dict[str, Any]:
        """Exchange an authorization code for an access token (web flow)."""
        async with httpx.AsyncClient() as client:
            payload: dict[str, str] = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
            }
            if redirect_uri:
                payload["redirect_uri"] = redirect_uri

            response = await client.post(
                self.ACCESS_TOKEN_URL,
                data=payload,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise RuntimeError(
                    f"Token exchange failed: {data['error']} — {data.get('error_description', '')}"
                )

            logger.info("code_exchange_completed")
            return data
