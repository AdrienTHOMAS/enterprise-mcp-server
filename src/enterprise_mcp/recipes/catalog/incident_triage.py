"""Incident Triage recipe — multi-system P1 incident response workflow."""

from ..base import Recipe, RecipeRegistry, RecipeStep

INCIDENT_TRIAGE = RecipeRegistry.register(
    Recipe(
        name="incident_triage",
        description=(
            "Automated P1 incident triage: searches Jira for open incidents, checks recent "
            "GitHub commits for potential root causes, finds runbooks in Confluence, creates "
            "or links PagerDuty incidents, and posts a status update to Slack #incidents."
        ),
        category="incident_response",
        system_prompt=(
            "You are a senior Site Reliability Engineer with 10+ years of experience managing "
            "production incidents at scale. Your priorities are:\n"
            "1. Assess blast radius — how many users/services are affected?\n"
            "2. Identify probable root cause from recent changes.\n"
            "3. Find and reference the appropriate runbook.\n"
            "4. Ensure the incident is tracked in PagerDuty with correct urgency.\n"
            "5. Communicate clearly and concisely to the #incidents channel.\n\n"
            "Be direct, avoid speculation without evidence, and always include actionable "
            "next steps. Time is critical during P1s — prioritize speed over completeness."
        ),
        starter_prompt=(
            "A P1 incident has been reported for project {{project_key}}. "
            "Triage the incident: search for open P1 issues, check recent code changes, "
            "find the relevant runbook, ensure PagerDuty tracking, and post a status update."
        ),
        required_tools=[
            "jira_search_issues",
            "github_list_pull_requests",
            "confluence_search",
            "pagerduty_list_incidents",
            "pagerduty_create_incident",
            "slack_post_message",
        ],
        steps=[
            RecipeStep(
                tool_name="jira_search_issues",
                description="Search Jira for open P1 incidents in the project",
                parameters_template={
                    "jql": "project = {{context.project_key}} AND priority = P1 AND status != Done ORDER BY created DESC",
                    "max_results": 5,
                },
            ),
            RecipeStep(
                tool_name="github_list_pull_requests",
                description="Check recent merged PRs for potential root cause",
                parameters_template={
                    "repo": "{{context.repo}}",
                    "state": "closed",
                },
            ),
            RecipeStep(
                tool_name="confluence_search",
                description="Find the runbook for the affected service",
                parameters_template={
                    "query": "{{context.service_name}} runbook",
                    "max_results": 3,
                },
            ),
            RecipeStep(
                tool_name="pagerduty_list_incidents",
                description="Check if a PagerDuty incident already exists",
                parameters_template={
                    "statuses": ["triggered", "acknowledged"],
                },
            ),
            RecipeStep(
                tool_name="pagerduty_create_incident",
                description="Create PagerDuty incident if none exists",
                parameters_template={
                    "title": "P1: {{context.service_name}} — {{context.incident_summary}}",
                    "service_id": "{{context.pagerduty_service_id}}",
                    "urgency": "high",
                },
                condition="context.create_pagerduty_incident",
            ),
            RecipeStep(
                tool_name="slack_post_message",
                description="Post incident status update to #incidents",
                parameters_template={
                    "channel": "{{context.slack_channel}}",
                    "text": "{{context.incident_summary}}",
                },
            ),
        ],
        expected_outputs=[
            "List of open P1 Jira issues",
            "Recent merged PRs (potential root causes)",
            "Relevant runbook links from Confluence",
            "PagerDuty incident status or newly created incident",
            "Slack notification posted to #incidents",
        ],
        tags=["incident", "p1", "sre", "triage", "on-call"],
    )
)
