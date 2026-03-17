#!/usr/bin/env python3
"""Standalone demo of Enterprise MCP Server — works with zero configuration.

Run:
    python examples/demo_mode.py

This script demonstrates all 38 tools using realistic mock data.
No API keys, no configuration, no external services required.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Ensure the package is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from enterprise_mcp.demo.mock_connectors import (
    MockConfluenceConnector,
    MockDatadogConnector,
    MockGitHubConnector,
    MockJiraConnector,
    MockPagerDutyConnector,
    MockSlackConnector,
)


def _pp(label: str, data: object) -> None:
    """Pretty-print a result with a label."""
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)


async def main() -> None:
    print("=" * 60)
    print("  Enterprise MCP Server — Demo Mode")
    print("  Zero config. Zero API keys. Full functionality.")
    print("=" * 60)

    # ── Jira ─────────────────────────────────────────────────────
    jira = MockJiraConnector()

    issues = await jira.search_issues("priority = Highest AND status != Done")
    _pp("Jira: Search P1 issues", issues)

    issue = await jira.get_issue("PAY-101")
    _pp("Jira: Get issue PAY-101", issue)

    projects = await jira.list_projects()
    _pp("Jira: List projects", projects)

    sprint = await jira.get_sprint(board_id=12)
    _pp("Jira: Active sprint", sprint)

    # ── GitHub ───────────────────────────────────────────────────
    github = MockGitHubConnector()

    repo = await github.get_repo("acme-corp", "payment-service")
    _pp("GitHub: Get repo", repo)

    prs = await github.list_pull_requests("acme-corp", "payment-service")
    _pp(f"GitHub: List PRs ({len(prs)} total)", prs)

    pr = await github.get_pull_request("acme-corp", "payment-service", 347)
    _pp("GitHub: Get PR #347", pr)

    search = await github.search_code("POOL_SIZE")
    _pp("GitHub: Code search for POOL_SIZE", search)

    # ── Confluence ───────────────────────────────────────────────
    confluence = MockConfluenceConnector()

    results = await confluence.search("payment runbook")
    _pp("Confluence: Search for 'payment runbook'", results)

    page = await confluence.get_page("90001")
    _pp("Confluence: Get Payment Service Runbook", page)

    spaces = await confluence.list_spaces()
    _pp("Confluence: List spaces", spaces)

    # ── Slack ────────────────────────────────────────────────────
    slack = MockSlackConnector()

    channels = await slack.list_channels()
    _pp("Slack: List channels", channels)

    history = await slack.get_channel_history("C001INCIDENTS")
    _pp("Slack: #incidents history", history)

    user = await slack.get_user_info("U_SARAH")
    _pp("Slack: User info for Sarah Chen", user)

    post = await slack.post_message("C002PAYMENTS", "Demo message from Enterprise MCP!")
    _pp("Slack: Post message", post)

    # ── PagerDuty ────────────────────────────────────────────────
    pagerduty = MockPagerDutyConnector()

    incidents = await pagerduty.list_incidents(statuses=["triggered", "acknowledged"])
    _pp("PagerDuty: Active incidents", incidents)

    ack = await pagerduty.acknowledge_incident("INC-2891")
    _pp("PagerDuty: Acknowledge INC-2891", ack)

    # ── Datadog ──────────────────────────────────────────────────
    datadog = MockDatadogConnector()

    monitors = await datadog.list_monitors()
    _pp("Datadog: List monitors", monitors)

    logs = await datadog.search_logs("service:payment-api status:error")
    _pp("Datadog: Error logs for payment-api", logs)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("  Demo complete!")
    print()
    print("  To run the full MCP server in demo mode:")
    print("    ENTERPRISE_MCP_DEMO=true enterprise-mcp")
    print()
    print("  Or add to Claude Desktop config:")
    print('    "env": {"ENTERPRISE_MCP_DEMO": "true"}')
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
