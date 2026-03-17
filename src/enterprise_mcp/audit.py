"""Audit logging — every tool call recorded for enterprise compliance."""

from __future__ import annotations

import csv
import io
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger("audit")

# Patterns that look like secrets/tokens — values will be redacted
_SENSITIVE_KEYS = re.compile(
    r"(token|password|secret|api_key|auth|credential|private_key)", re.IGNORECASE
)

# PII fields that get anonymized by GDPR tool
_PII_FIELDS = {"agent_session_id", "tenant_id", "input_params"}

DEFAULT_AUDIT_PATH = Path.home() / ".enterprise-mcp" / "audit.jsonl"


def _sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive values from tool input parameters."""
    sanitized: dict[str, Any] = {}
    for key, value in params.items():
        if _SENSITIVE_KEYS.search(key):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, str) and len(value) > 500:
            sanitized[key] = value[:500] + "...[truncated]"
        else:
            sanitized[key] = value
    return sanitized


class AuditEntry:
    """Single audit log entry."""

    __slots__ = (
        "timestamp", "tool_name", "input_params", "output_summary",
        "duration_ms", "tenant_id", "agent_session_id", "success", "error",
    )

    def __init__(
        self,
        tool_name: str,
        input_params: dict[str, Any],
        output_summary: str,
        duration_ms: float,
        tenant_id: str = "",
        agent_session_id: str = "",
        success: bool = True,
        error: str = "",
    ) -> None:
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.tool_name = tool_name
        self.input_params = _sanitize_params(input_params)
        self.output_summary = output_summary[:500] if output_summary else ""
        self.duration_ms = round(duration_ms, 2)
        self.tenant_id = tenant_id
        self.agent_session_id = agent_session_id
        self.success = success
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "input_params": self.input_params,
            "output_summary": self.output_summary,
            "duration_ms": self.duration_ms,
            "tenant_id": self.tenant_id,
            "agent_session_id": self.agent_session_id,
            "success": self.success,
            "error": self.error,
        }


class AuditLogger:
    """Append-only audit logger writing JSONL to file."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else DEFAULT_AUDIT_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, entry: AuditEntry) -> None:
        line = json.dumps(entry.to_dict(), default=str)
        with open(self._path, "a") as f:
            f.write(line + "\n")

    def log_tool_call(
        self,
        tool_name: str,
        input_params: dict[str, Any],
        output: str,
        duration_ms: float,
        success: bool = True,
        error: str = "",
        tenant_id: str = "",
        agent_session_id: str = "",
    ) -> None:
        entry = AuditEntry(
            tool_name=tool_name,
            input_params=input_params,
            output_summary=output[:200] if output else "",
            duration_ms=duration_ms,
            tenant_id=tenant_id,
            agent_session_id=agent_session_id,
            success=success,
            error=error,
        )
        self.log(entry)


class AuditQuery:
    """Query the audit log file."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else DEFAULT_AUDIT_PATH

    def query(
        self,
        tool_name: str = "",
        tenant_id: str = "",
        since: str = "",
        until: str = "",
        success: bool | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []

        results: list[dict[str, Any]] = []
        with open(self._path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if tool_name and entry.get("tool_name") != tool_name:
                    continue
                if tenant_id and entry.get("tenant_id") != tenant_id:
                    continue
                if success is not None and entry.get("success") != success:
                    continue
                if since and entry.get("timestamp", "") < since:
                    continue
                if until and entry.get("timestamp", "") > until:
                    continue

                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def export_csv(self, entries: list[dict[str, Any]]) -> str:
        if not entries:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(entries[0].keys()))
        writer.writeheader()
        for entry in entries:
            row = {k: json.dumps(v) if isinstance(v, dict) else v for k, v in entry.items()}
            writer.writerow(row)
        return output.getvalue()

    def anonymize(self, before_date: str) -> int:
        """Anonymize PII in audit entries older than before_date (GDPR compliance).

        Rewrites the audit log, replacing PII fields with '[ANONYMIZED]' for
        entries whose timestamp is before the given ISO 8601 date string.
        Returns the number of entries anonymized.
        """
        if not self._path.exists():
            return 0

        anonymized_count = 0
        lines: list[str] = []

        with open(self._path) as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    entry = json.loads(raw_line)
                except json.JSONDecodeError:
                    lines.append(raw_line)
                    continue

                if entry.get("timestamp", "") < before_date:
                    for field in _PII_FIELDS:
                        if field in entry:
                            entry[field] = "[ANONYMIZED]"
                    anonymized_count += 1

                lines.append(json.dumps(entry, default=str))

        # Atomic write: write to temp file then rename
        tmp_path = self._path.with_suffix(".jsonl.tmp")
        with open(tmp_path, "w") as f:
            for line in lines:
                f.write(line + "\n")
        tmp_path.replace(self._path)

        return anonymized_count


# ── Module-level singleton ───────────────────────────────────────────

_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# ── MCP tool registration ────────────────────────────────────────────

def register_audit_tools() -> None:
    """Register the get_audit_log and anonymize_audit_log MCP tools."""
    from mcp.types import Tool

    from .tools.registry import register_tool

    # get_audit_log — lets agents query their own tool-call history
    register_tool(
        Tool(
            name="get_audit_log",
            description=(
                "Query the audit log of all tool calls. Filter by tool name, "
                "time range, or success/failure. Returns audit entries for compliance."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Filter by tool name (e.g., 'jira_get_issue')",
                        "default": "",
                    },
                    "since": {
                        "type": "string",
                        "description": "Start of time range (ISO 8601 datetime)",
                        "default": "",
                    },
                    "until": {
                        "type": "string",
                        "description": "End of time range (ISO 8601 datetime)",
                        "default": "",
                    },
                    "success": {
                        "type": "boolean",
                        "description": "Filter by success (true) or failure (false)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of entries to return",
                        "default": 50,
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format: 'json' or 'csv'",
                        "default": "json",
                    },
                },
                "required": [],
            },
        ),
        _make_get_audit_log_handler(),
    )

    # anonymize_audit_log — GDPR compliance: redact PII from old entries
    register_tool(
        Tool(
            name="anonymize_audit_log",
            description=(
                "GDPR compliance: anonymize PII (agent IDs, tenant IDs, input params) "
                "from audit log entries older than the specified date. Irreversible."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "before_date": {
                        "type": "string",
                        "description": "Anonymize entries before this ISO 8601 date (e.g., '2026-01-01T00:00:00Z')",
                    },
                },
                "required": ["before_date"],
            },
        ),
        _make_anonymize_handler(),
    )


def _make_get_audit_log_handler():  # type: ignore[no-untyped-def]
    query_engine = AuditQuery()

    async def handler(
        tool_name: str = "",
        since: str = "",
        until: str = "",
        success: bool | None = None,
        limit: int = 50,
        format: str = "json",
    ) -> str:
        entries = query_engine.query(
            tool_name=tool_name,
            since=since,
            until=until,
            success=success,
            limit=limit,
        )
        if format == "csv":
            return query_engine.export_csv(entries)
        return json.dumps(entries, indent=2, default=str)

    return handler


def _make_anonymize_handler():  # type: ignore[no-untyped-def]
    query_engine = AuditQuery()

    async def handler(before_date: str) -> str:
        count = query_engine.anonymize(before_date)
        return json.dumps({
            "anonymized_entries": count,
            "before_date": before_date,
            "status": "completed",
        })

    return handler
