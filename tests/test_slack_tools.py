"""Tests for the Slack connector and tools."""

import httpx
import pytest
import respx

from enterprise_mcp.connectors.slack import SlackConnector

SLACK_API = "https://slack.com/api"
CHANNEL = "C12345"


# ---- post_message -------------------------------------------------------- #


@pytest.mark.asyncio
async def test_post_message_success(slack_post_payload):
    """post_message returns the message data on success."""
    async with respx.mock:
        respx.post(f"{SLACK_API}/chat.postMessage").mock(
            return_value=httpx.Response(200, json=slack_post_payload)
        )
        connector = SlackConnector("xoxb-test-token")
        result = await connector.post_message(CHANNEL, "Incident update posted.")

    assert result["ok"] is True
    assert result["ts"] == "1705312800.000001"


@pytest.mark.asyncio
async def test_post_message_channel_not_found():
    """post_message raises RuntimeError when Slack returns ok=False."""
    async with respx.mock:
        respx.post(f"{SLACK_API}/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": False, "error": "channel_not_found"})
        )
        connector = SlackConnector("xoxb-test-token")
        with pytest.raises(RuntimeError, match="channel_not_found"):
            await connector.post_message("C_INVALID", "Hello")


@pytest.mark.asyncio
async def test_post_message_http_error():
    """post_message raises HTTPStatusError on HTTP 429."""
    async with respx.mock:
        respx.post(f"{SLACK_API}/chat.postMessage").mock(
            return_value=httpx.Response(429, json={"message": "Rate limit exceeded"})
        )
        connector = SlackConnector("xoxb-test-token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.post_message(CHANNEL, "Hello")


@pytest.mark.asyncio
async def test_post_message_server_error():
    """post_message raises HTTPStatusError on HTTP 500."""
    async with respx.mock:
        respx.post(f"{SLACK_API}/chat.postMessage").mock(
            return_value=httpx.Response(500, json={"message": "Internal error"})
        )
        connector = SlackConnector("xoxb-test-token")
        with pytest.raises(httpx.HTTPStatusError):
            await connector.post_message(CHANNEL, "Hello")


# ---- get_channel_history ------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_channel_history_success(slack_history_payload):
    """get_channel_history returns messages on success."""
    async with respx.mock:
        respx.get(f"{SLACK_API}/conversations.history").mock(
            return_value=httpx.Response(200, json=slack_history_payload)
        )
        connector = SlackConnector("xoxb-test-token")
        result = await connector.get_channel_history(CHANNEL)

    assert result["ok"] is True
    assert len(result["messages"]) == 2
    assert result["messages"][0]["user"] == "U12345"


@pytest.mark.asyncio
async def test_get_channel_history_not_in_channel():
    """get_channel_history raises RuntimeError when bot is not in channel."""
    async with respx.mock:
        respx.get(f"{SLACK_API}/conversations.history").mock(
            return_value=httpx.Response(200, json={"ok": False, "error": "not_in_channel"})
        )
        connector = SlackConnector("xoxb-test-token")
        with pytest.raises(RuntimeError, match="not_in_channel"):
            await connector.get_channel_history(CHANNEL)


# ---- list_channels ------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_channels_success(slack_channels_payload):
    """list_channels returns all channels on success."""
    async with respx.mock:
        respx.get(f"{SLACK_API}/conversations.list").mock(
            return_value=httpx.Response(200, json=slack_channels_payload)
        )
        connector = SlackConnector("xoxb-test-token")
        result = await connector.list_channels()

    assert result["ok"] is True
    assert len(result["channels"]) == 2
    names = [c["name"] for c in result["channels"]]
    assert "incidents" in names


# ---- get_user_info ------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_user_info_success(slack_user_payload):
    """get_user_info returns user profile on success."""
    async with respx.mock:
        respx.get(f"{SLACK_API}/users.info").mock(
            return_value=httpx.Response(200, json=slack_user_payload)
        )
        connector = SlackConnector("xoxb-test-token")
        result = await connector.get_user_info("U12345")

    assert result["ok"] is True
    assert result["user"]["profile"]["display_name"] == "Alice Smith"


@pytest.mark.asyncio
async def test_get_user_info_not_found():
    """get_user_info raises RuntimeError when user not found."""
    async with respx.mock:
        respx.get(f"{SLACK_API}/users.info").mock(
            return_value=httpx.Response(200, json={"ok": False, "error": "user_not_found"})
        )
        connector = SlackConnector("xoxb-test-token")
        with pytest.raises(RuntimeError, match="user_not_found"):
            await connector.get_user_info("U_INVALID")


# ---- add_reaction -------------------------------------------------------- #


@pytest.mark.asyncio
async def test_add_reaction_success():
    """add_reaction returns ok=True on success."""
    async with respx.mock:
        respx.post(f"{SLACK_API}/reactions.add").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        connector = SlackConnector("xoxb-test-token")
        result = await connector.add_reaction(CHANNEL, "1705312800.000001", "white_check_mark")

    assert result["ok"] is True


@pytest.mark.asyncio
async def test_add_reaction_already_reacted():
    """add_reaction raises RuntimeError when reaction already exists."""
    async with respx.mock:
        respx.post(f"{SLACK_API}/reactions.add").mock(
            return_value=httpx.Response(200, json={"ok": False, "error": "already_reacted"})
        )
        connector = SlackConnector("xoxb-test-token")
        with pytest.raises(RuntimeError, match="already_reacted"):
            await connector.add_reaction(CHANNEL, "1705312800.000001", "thumbsup")


# ---- create_thread_reply ------------------------------------------------- #


@pytest.mark.asyncio
async def test_create_thread_reply_success(slack_post_payload):
    """create_thread_reply posts a reply in the given thread."""
    async with respx.mock:
        respx.post(f"{SLACK_API}/chat.postMessage").mock(
            return_value=httpx.Response(200, json=slack_post_payload)
        )
        connector = SlackConnector("xoxb-test-token")
        result = await connector.create_thread_reply(CHANNEL, "1705312700.000001", "On it!")

    assert result["ok"] is True
