"""Slack Web API connector."""

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseConnector

logger = logging.getLogger(__name__)


class SlackConnector(BaseConnector):
    """Slack Web API connector.

    Authenticates via Bot Token (xoxb-...) and provides methods for
    sending messages, reading channel history, and managing reactions.
    """

    BASE_URL = "https://slack.com/api"

    def __init__(self, bot_token: str) -> None:
        """Initialize the Slack connector.

        Args:
            bot_token: Slack Bot Token starting with 'xoxb-'.
        """
        self._token = bot_token
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return a lazily-initialized async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                timeout=30.0,
            )
        return self._client

    def _check_slack_response(self, data: dict[str, Any], context: str = "") -> None:
        """Check Slack API response for error flags.

        Slack always returns HTTP 200 but signals errors via the 'ok' field.

        Args:
            data: Parsed JSON response from the Slack API.
            context: Optional context string for error messages.

        Raises:
            RuntimeError: If the Slack API indicates an error.
        """
        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            msg = f"Slack API error: {error}"
            if context:
                msg = f"{context}: {msg}"
            logger.error(msg)
            raise RuntimeError(msg)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def post_message(
        self,
        channel: str,
        text: str,
        thread_ts: str = "",
        blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Post a message to a Slack channel.

        Args:
            channel: Channel ID or name (e.g., '#general' or 'C1234567890').
            text: Message text (plain text fallback for block kit messages).
            thread_ts: Thread timestamp to reply in a thread.
            blocks: Optional Block Kit blocks for rich message formatting.

        Returns:
            Posted message data including timestamp and channel.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        if blocks:
            payload["blocks"] = blocks

        response = await client.post("/chat.postMessage", json=payload)
        self._raise_for_status(response, "post_message")
        data = response.json()
        self._check_slack_response(data, "post_message")
        return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_channel_history(
        self, channel: str, limit: int = 50, oldest: str = "", latest: str = ""
    ) -> dict[str, Any]:
        """Fetch message history from a Slack channel.

        Args:
            channel: Channel ID (e.g., 'C1234567890').
            limit: Number of messages to return (max 1000).
            oldest: Only messages after this Unix timestamp.
            latest: Only messages before this Unix timestamp.

        Returns:
            Channel history with messages, timestamps, and user IDs.
        """
        client = await self._get_client()
        params: dict[str, Any] = {
            "channel": channel,
            "limit": min(limit, 1000),
        }
        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest

        response = await client.get("/conversations.history", params=params)
        self._raise_for_status(response, f"get_channel_history({channel})")
        data = response.json()
        self._check_slack_response(data, "get_channel_history")
        return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def list_channels(
        self,
        exclude_archived: bool = True,
        types: str = "public_channel,private_channel",
        max_results: int = 200,
    ) -> dict[str, Any]:
        """List all Slack channels accessible to the bot.

        Args:
            exclude_archived: Whether to exclude archived channels. Defaults to True.
            types: Comma-separated channel types to include.
            max_results: Maximum number of channels to return.

        Returns:
            List of channels with IDs, names, topics, and member counts.
        """
        client = await self._get_client()
        params: dict[str, Any] = {
            "exclude_archived": exclude_archived,
            "types": types,
            "limit": min(max_results, 1000),
        }
        response = await client.get("/conversations.list", params=params)
        self._raise_for_status(response, "list_channels")
        data = response.json()
        self._check_slack_response(data, "list_channels")
        return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_user_info(self, user_id: str) -> dict[str, Any]:
        """Get information about a Slack user.

        Args:
            user_id: Slack user ID (e.g., 'U1234567890').

        Returns:
            User profile including display name, real name, email, and status.
        """
        client = await self._get_client()
        response = await client.get("/users.info", params={"user": user_id})
        self._raise_for_status(response, f"get_user_info({user_id})")
        data = response.json()
        self._check_slack_response(data, "get_user_info")
        return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def add_reaction(
        self, channel: str, timestamp: str, emoji_name: str
    ) -> dict[str, Any]:
        """Add an emoji reaction to a Slack message.

        Args:
            channel: Channel ID containing the message.
            timestamp: Message timestamp (ts field from the message).
            emoji_name: Emoji name without colons (e.g., 'thumbsup', 'white_check_mark').

        Returns:
            Confirmation of the reaction being added.
        """
        client = await self._get_client()
        payload = {
            "channel": channel,
            "timestamp": timestamp,
            "name": emoji_name,
        }
        response = await client.post("/reactions.add", json=payload)
        self._raise_for_status(response, f"add_reaction({emoji_name})")
        data = response.json()
        self._check_slack_response(data, "add_reaction")
        return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_thread_reply(
        self, channel: str, thread_ts: str, text: str
    ) -> dict[str, Any]:
        """Post a reply in an existing Slack thread.

        Args:
            channel: Channel ID containing the thread.
            thread_ts: Timestamp of the parent message (thread root).
            text: Reply message text.

        Returns:
            Posted reply data including timestamp and thread metadata.
        """
        return await self.post_message(channel=channel, text=text, thread_ts=thread_ts)
