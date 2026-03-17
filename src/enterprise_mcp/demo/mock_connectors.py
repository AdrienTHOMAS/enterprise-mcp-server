"""Mock connectors — drop-in replacements returning realistic data, zero API calls."""

from __future__ import annotations

import asyncio
import copy
import random
from typing import Any

from . import mock_data as _d


class _MockBase:
    """Shared mock utilities."""

    async def _delay(self) -> None:
        await asyncio.sleep(random.uniform(0.02, 0.08))

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> "_MockBase":
        return self

    async def __aexit__(self, *_: object) -> None:
        pass


# ── Jira ─────────────────────────────────────────────────────────────

class MockJiraConnector(_MockBase):

    def __init__(self, *_a: Any, **_kw: Any) -> None:
        pass

    async def get_issue(self, issue_key: str, include_comments: bool = False) -> dict:
        await self._delay()
        for issue in _d.JIRA_ISSUES:
            if issue["key"] == issue_key:
                return copy.deepcopy(issue)
        return {"error": f"Issue {issue_key} not found"}

    async def search_issues(self, jql: str, max_results: int = 50, fields: str = "") -> dict:
        await self._delay()
        results = copy.deepcopy(_d.JIRA_ISSUES[:max_results])
        return {"issues": results, "total": len(results), "maxResults": max_results}

    async def create_issue(self, project_key: str, summary: str, issue_type: str = "Task", description: str = "", priority: str = "", assignee_account_id: str = "", labels: list[str] | None = None) -> dict:
        await self._delay()
        return {"key": f"{project_key}-999", "self": f"https://demo.atlassian.net/rest/api/3/issue/{project_key}-999", "id": "99999"}

    async def update_issue(self, issue_key: str, status_transition_id: str = "", assignee_account_id: str = "", priority: str = "", summary: str = "") -> dict:
        await self._delay()
        issue = await self.get_issue(issue_key)
        return {"fields_updated": True, "issue": issue}

    async def add_comment(self, issue_key: str, body: str) -> dict:
        await self._delay()
        return {"id": "10042", "author": {"displayName": "Demo User"}, "body": body, "created": "2026-03-17T10:00:00Z"}

    async def get_sprint(self, board_id: int) -> dict:
        await self._delay()
        return copy.deepcopy(_d.JIRA_SPRINT)

    async def list_projects(self, max_results: int = 50) -> dict:
        await self._delay()
        return {"values": copy.deepcopy(_d.JIRA_PROJECTS), "total": len(_d.JIRA_PROJECTS)}

    async def get_board(self, board_id: int) -> dict:
        await self._delay()
        return copy.deepcopy(_d.JIRA_BOARD)


# ── GitHub ───────────────────────────────────────────────────────────

class MockGitHubConnector(_MockBase):
    def __init__(self, *_a: Any, **_kw: Any) -> None:
        self.default_owner = "acme-corp"

    async def get_repo(self, owner: str, repo: str) -> dict:
        await self._delay()
        for r in _d.GITHUB_REPOS:
            if r["name"] == repo:
                return copy.deepcopy(r)
        return copy.deepcopy(_d.GITHUB_REPOS[0])

    async def list_issues(self, owner: str, repo: str, state: str = "open", labels: str = "", assignee: str = "", max_results: int = 30) -> list[dict]:
        await self._delay()
        return copy.deepcopy(_d.GITHUB_ISSUES[:max_results])

    async def create_issue(self, owner: str, repo: str, title: str, body: str = "", labels: list[str] | None = None, assignees: list[str] | None = None) -> dict:
        await self._delay()
        return {"number": 350, "title": title, "state": "open", "html_url": f"https://github.com/{owner}/{repo}/issues/350"}

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> dict:
        await self._delay()
        for pr in _d.GITHUB_PRS:
            if pr["number"] == pr_number:
                return copy.deepcopy(pr)
        return copy.deepcopy(_d.GITHUB_PRS[0])

    async def list_pull_requests(self, owner: str, repo: str, state: str = "open", base: str = "", max_results: int = 30) -> list[dict]:
        await self._delay()
        return copy.deepcopy(_d.GITHUB_PRS[:max_results])

    async def search_code(self, query: str, owner: str = "", repo: str = "", max_results: int = 30) -> dict:
        await self._delay()
        return copy.deepcopy(_d.GITHUB_CODE_SEARCH)

    async def get_file_content(self, owner: str, repo: str, path: str, ref: str = "") -> dict:
        await self._delay()
        return copy.deepcopy(_d.GITHUB_FILE_CONTENT)

    async def create_review_comment(self, owner: str, repo: str, pr_number: int, body: str, commit_id: str, path: str, line: int) -> dict:
        await self._delay()
        return {"id": 99001, "body": body, "path": path, "line": line, "created_at": "2026-03-17T10:00:00Z"}


# ── Confluence ───────────────────────────────────────────────────────

class MockConfluenceConnector(_MockBase):
    def __init__(self, *_a: Any, **_kw: Any) -> None:
        pass

    async def get_page(self, page_id: str, include_body: bool = True) -> dict:
        await self._delay()
        page = _d.CONFLUENCE_PAGES.get(page_id)
        if page:
            return copy.deepcopy(page)
        return {"error": f"Page {page_id} not found"}

    async def search(self, query: str, space_key: str = "", max_results: int = 25) -> dict:
        await self._delay()
        return copy.deepcopy(_d.CONFLUENCE_SEARCH_RESULTS)

    async def create_page(self, space_id: str, title: str, body: str, parent_page_id: str = "", body_format: str = "wiki") -> dict:
        await self._delay()
        return {"id": "99001", "title": title, "version": {"number": 1}, "spaceId": space_id}

    async def update_page(self, page_id: str, title: str, body: str, version_number: int, body_format: str = "wiki") -> dict:
        await self._delay()
        return {"id": page_id, "title": title, "version": {"number": version_number}}

    async def list_spaces(self, max_results: int = 50) -> dict:
        await self._delay()
        return copy.deepcopy(_d.CONFLUENCE_SPACES)

    async def get_children(self, page_id: str, max_results: int = 25) -> dict:
        await self._delay()
        return {"results": [], "size": 0}


# ── Slack ────────────────────────────────────────────────────────────

class MockSlackConnector(_MockBase):
    def __init__(self, *_a: Any, **_kw: Any) -> None:
        pass

    async def post_message(self, channel: str, text: str, thread_ts: str = "", blocks: list[dict] | None = None) -> dict:
        await self._delay()
        return {"ok": True, "channel": channel, "ts": "1742180000.000100", "message": {"text": text}}

    async def get_channel_history(self, channel: str, limit: int = 50, oldest: str = "", latest: str = "") -> dict:
        await self._delay()
        msgs = _d.SLACK_MESSAGES.get(channel, {"ok": True, "messages": []})
        return copy.deepcopy(msgs)

    async def list_channels(self, exclude_archived: bool = True, types: str = "", max_results: int = 200) -> dict:
        await self._delay()
        return copy.deepcopy(_d.SLACK_CHANNELS)

    async def get_user_info(self, user_id: str) -> dict:
        await self._delay()
        user = _d.SLACK_USERS.get(user_id, {"ok": True, "user": {"id": user_id, "name": "unknown", "real_name": "Unknown User", "profile": {}}})
        return copy.deepcopy(user)

    async def add_reaction(self, channel: str, timestamp: str, emoji_name: str) -> dict:
        await self._delay()
        return {"ok": True}

    async def create_thread_reply(self, channel: str, thread_ts: str, text: str) -> dict:
        return await self.post_message(channel=channel, text=text, thread_ts=thread_ts)


# ── PagerDuty ────────────────────────────────────────────────────────

class MockPagerDutyConnector(_MockBase):
    def __init__(self, *_a: Any, **_kw: Any) -> None:
        self.default_from_email = "demo@acme-corp.com"

    async def get_incident(self, incident_id: str) -> dict:
        await self._delay()
        for inc in _d.PAGERDUTY_INCIDENTS:
            if inc["id"] == incident_id:
                return copy.deepcopy(inc)
        return copy.deepcopy(_d.PAGERDUTY_INCIDENTS[0])

    async def list_incidents(self, statuses: list[str] | None = None, urgencies: list[str] | None = None, since: str = "", until: str = "", limit: int = 25) -> dict:
        await self._delay()
        incidents = copy.deepcopy(_d.PAGERDUTY_INCIDENTS)
        if statuses:
            incidents = [i for i in incidents if i["status"] in statuses]
        return {"incidents": incidents, "total": len(incidents)}

    async def acknowledge_incident(self, incident_id: str, from_email: str = "") -> dict:
        await self._delay()
        inc = await self.get_incident(incident_id)
        inc["status"] = "acknowledged"
        return inc

    async def resolve_incident(self, incident_id: str, from_email: str = "") -> dict:
        await self._delay()
        inc = await self.get_incident(incident_id)
        inc["status"] = "resolved"
        return inc

    async def create_incident(self, title: str, service_id: str, urgency: str = "high", body: str = "", from_email: str = "") -> dict:
        await self._delay()
        return {"id": "INC-9999", "title": title, "status": "triggered", "urgency": urgency, "service": {"id": service_id}}


# ── Datadog ──────────────────────────────────────────────────────────

class MockDatadogConnector(_MockBase):
    def __init__(self, *_a: Any, **_kw: Any) -> None:
        pass

    async def get_metrics(self, query: str, from_ts: int, to_ts: int) -> dict:
        await self._delay()
        return copy.deepcopy(_d.DATADOG_METRICS)

    async def list_monitors(self, name: str = "", tags: str = "", monitor_type: str = "", page: int = 0, page_size: int = 50) -> list[dict]:
        await self._delay()
        return copy.deepcopy(_d.DATADOG_MONITORS)

    async def get_monitor_status(self, monitor_id: int) -> dict:
        await self._delay()
        for m in _d.DATADOG_MONITORS:
            if m["id"] == monitor_id:
                return copy.deepcopy(m)
        return copy.deepcopy(_d.DATADOG_MONITORS[0])

    async def create_event(self, title: str, text: str, alert_type: str = "info", tags: list[str] | None = None, source_type_name: str = "enterprise-mcp") -> dict:
        await self._delay()
        return copy.deepcopy(_d.DATADOG_EVENT_RESPONSE)

    async def search_logs(self, query: str, from_ts: str = "", to_ts: str = "", limit: int = 50, sort: str = "timestamp", sort_order: str = "desc") -> dict:
        await self._delay()
        return copy.deepcopy(_d.DATADOG_LOGS)
