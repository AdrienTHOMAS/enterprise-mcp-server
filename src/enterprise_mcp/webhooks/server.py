"""FastAPI webhook server for receiving events from Jira, GitHub, and Slack."""

import hashlib
import hmac
import json
from typing import Any

import structlog
from fastapi import FastAPI, Header, HTTPException, Request

logger = structlog.get_logger("webhooks")

# Event store — in production, backed by Redis pub/sub
_event_subscribers: list[Any] = []
_recent_events: list[dict[str, Any]] = []
MAX_RECENT_EVENTS = 1000


def create_webhook_app(
    github_webhook_secret: str = "",
    jira_webhook_secret: str = "",
    slack_signing_secret: str = "",
) -> FastAPI:
    """Create the FastAPI webhook server application."""

    app = FastAPI(title="Enterprise MCP Webhooks", version="2.0.0")

    def _store_event(source: str, event_type: str, payload: dict[str, Any]) -> None:
        """Store event and notify subscribers."""
        import time

        event = {
            "source": source,
            "event_type": event_type,
            "payload": payload,
            "received_at": time.time(),
        }
        _recent_events.append(event)
        if len(_recent_events) > MAX_RECENT_EVENTS:
            _recent_events.pop(0)

        for subscriber in _event_subscribers:
            try:
                subscriber(event)
            except Exception as exc:
                logger.error("subscriber_error", error=str(exc))

        logger.info("webhook_event_received", source=source, event_type=event_type)

    def _verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook HMAC-SHA256 signature."""
        if not secret:
            return True
        expected = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def _verify_slack_signature(
        payload: bytes, timestamp: str, signature: str, secret: str
    ) -> bool:
        """Verify Slack request signature (HMAC-SHA256)."""
        if not secret:
            return True
        base = f"v0:{timestamp}:{payload.decode()}".encode()
        expected = "v0=" + hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def _verify_jira_signature(payload: bytes, signature: str, secret: str) -> bool:
        """Verify Jira webhook HMAC-SHA256 signature."""
        if not secret:
            return True
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    # ---- GitHub webhook endpoint ----------------------------------------- #

    @app.post("/webhooks/github")
    async def github_webhook(
        request: Request,
        x_hub_signature_256: str = Header("", alias="X-Hub-Signature-256"),
        x_github_event: str = Header("", alias="X-GitHub-Event"),
    ) -> dict[str, str]:
        body = await request.body()

        if github_webhook_secret and not _verify_github_signature(
            body, x_hub_signature_256, github_webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")

        payload = json.loads(body)

        event_type = x_github_event
        if event_type == "pull_request":
            action = payload.get("action", "")
            event_type = f"pull_request.{action}"
        elif event_type == "push":
            event_type = "push"
        elif event_type == "pull_request_review":
            event_type = f"review.{payload.get('action', '')}"

        _store_event("github", event_type, payload)
        return {"status": "ok"}

    # ---- Jira webhook endpoint ------------------------------------------- #

    @app.post("/webhooks/jira")
    async def jira_webhook(
        request: Request,
        x_hub_signature: str = Header("", alias="X-Hub-Signature"),
    ) -> dict[str, str]:
        body = await request.body()

        if jira_webhook_secret and not _verify_jira_signature(
            body, x_hub_signature, jira_webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")

        payload = json.loads(body)
        event_type = payload.get("webhookEvent", "unknown")

        _store_event("jira", event_type, payload)
        return {"status": "ok"}

    # ---- Slack webhook endpoint ------------------------------------------ #

    @app.post("/webhooks/slack")
    async def slack_webhook(
        request: Request,
        x_slack_signature: str = Header("", alias="X-Slack-Signature"),
        x_slack_request_timestamp: str = Header("", alias="X-Slack-Request-Timestamp"),
    ) -> dict[str, Any]:
        body = await request.body()

        if slack_signing_secret and not _verify_slack_signature(
            body, x_slack_request_timestamp, x_slack_signature, slack_signing_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")

        payload = json.loads(body)

        # Handle Slack URL verification challenge
        if payload.get("type") == "url_verification":
            return {"challenge": payload.get("challenge", "")}

        event = payload.get("event", {})
        event_type = event.get("type", payload.get("type", "unknown"))

        _store_event("slack", event_type, payload)
        return {"status": "ok"}

    # ---- Events query endpoint ------------------------------------------- #

    @app.get("/webhooks/events")
    async def list_events(
        source: str = "",
        event_type: str = "",
        limit: int = 50,
    ) -> dict[str, Any]:
        """Query recent webhook events with optional filters."""
        filtered = _recent_events
        if source:
            filtered = [e for e in filtered if e["source"] == source]
        if event_type:
            filtered = [e for e in filtered if e["event_type"] == event_type]
        return {
            "events": filtered[-limit:],
            "total": len(filtered),
        }

    return app


def subscribe(callback: Any) -> None:
    """Subscribe to webhook events."""
    _event_subscribers.append(callback)


def get_recent_events(source: str = "", limit: int = 50) -> list[dict[str, Any]]:
    """Get recent webhook events."""
    events = _recent_events
    if source:
        events = [e for e in events if e["source"] == source]
    return events[-limit:]
