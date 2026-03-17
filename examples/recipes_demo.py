#!/usr/bin/env python3
"""Demo: Run the incident_triage recipe with mock tool responses.

Shows how an agent would execute a multi-step recipe across Jira, GitHub,
Confluence, PagerDuty, and Slack.

Usage:
    python examples/recipes_demo.py
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

# Import recipe infrastructure
from enterprise_mcp.recipes.base import RecipeRegistry, execute_recipe

# Auto-register all built-in recipes
import enterprise_mcp.recipes.catalog  # noqa: F401


# ---- Mock tool caller (simulates real tool responses) ---------------------- #

MOCK_RESPONSES: dict[str, Any] = {
    "jira_search_issues": {
        "issues": [
            {
                "key": "INFRA-892",
                "summary": "Payment service: 500 errors on /checkout",
                "priority": "P1",
                "status": "Open",
                "assignee": "oncall@company.com",
            }
        ],
        "total": 1,
    },
    "github_list_pull_requests": {
        "pull_requests": [
            {
                "number": 347,
                "title": "Refactor connection pool timeout config",
                "merged_at": "2024-01-15T14:30:00Z",
                "author": "dev@company.com",
                "files_changed": ["src/payment/pool.py", "config/timeouts.yaml"],
            }
        ],
    },
    "confluence_search": {
        "results": [
            {
                "title": "[Runbook] Payment Service Recovery Procedures",
                "url": "https://company.atlassian.net/wiki/spaces/SRE/pages/12345",
                "excerpt": "Step 1: Check connection pool metrics. Step 2: Restart payment pods...",
            }
        ],
    },
    "pagerduty_list_incidents": {
        "incidents": [
            {
                "id": "INC-2891",
                "title": "Payment API 5xx spike",
                "urgency": "high",
                "status": "triggered",
                "created_at": "2024-01-15T15:00:00Z",
            }
        ],
    },
    "slack_post_message": {
        "ok": True,
        "channel": "#incidents",
        "ts": "1705334400.001234",
        "message": "Posted successfully",
    },
}


async def mock_tool_caller(tool_name: str, **params: Any) -> str:
    """Simulate tool calls with realistic mock data."""
    response = MOCK_RESPONSES.get(tool_name, {"info": f"No mock for {tool_name}"})
    return json.dumps(response, indent=2)


# ---- Main ----------------------------------------------------------------- #


async def main() -> None:
    print("=" * 70)
    print("  ENTERPRISE MCP SERVER — RECIPE DEMO")
    print("  Incident Triage Workflow")
    print("=" * 70)
    print()

    # Get the recipe
    recipe = RecipeRegistry.get("incident_triage")
    if not recipe:
        print("ERROR: incident_triage recipe not found")
        return

    print(f"Recipe: {recipe.name}")
    print(f"Category: {recipe.category}")
    print(f"Tools: {', '.join(recipe.required_tools)}")
    print(f"Steps: {len(recipe.steps)}")
    print()
    print("System Prompt:")
    print(f"  {recipe.system_prompt[:200]}...")
    print()

    # Define context for this run
    context = {
        "project_key": "INFRA",
        "repo": "company/payment-service",
        "service_name": "payment-service",
        "incident_summary": "Payment API returning 500 errors on /checkout since 15:00 UTC",
        "pagerduty_service_id": "PABC123",
        "slack_channel": "#incidents",
        "create_pagerduty_incident": False,  # Already exists
    }

    print("Context:")
    for key, value in context.items():
        print(f"  {key}: {value}")
    print()

    # Execute the recipe
    print("-" * 70)
    print("  EXECUTING RECIPE")
    print("-" * 70)
    print()

    result = await execute_recipe(recipe, context, mock_tool_caller)

    for i, step in enumerate(result.steps_taken, 1):
        skipped = step.get("skipped", False)
        status = "SKIPPED" if skipped else "OK"
        icon = "-" if skipped else "+"

        print(f"  [{icon}] Step {i}: {step['description']}  [{status}]")
        if skipped:
            print(f"      Reason: {step.get('reason', 'N/A')}")
        else:
            print(f"      Tool: {step['tool']}")
            print(f"      Duration: {step['duration_seconds']}s")
            # Show a preview of the output
            output = step.get("output", "")
            if len(output) > 120:
                output = output[:120] + "..."
            print(f"      Output: {output}")
        print()

    print("-" * 70)
    print(f"  RESULT: {result.status.upper()}")
    print(f"  Total duration: {result.duration_seconds:.3f}s")
    print(f"  Steps executed: {len([s for s in result.steps_taken if not s.get('skipped')])}/{len(result.steps_taken)}")
    if result.error:
        print(f"  Error: {result.error}")
    print("-" * 70)
    print()

    # Show all available recipes
    print("ALL AVAILABLE RECIPES:")
    print()
    for r in RecipeRegistry.list_all():
        print(f"  {r.name}")
        print(f"    {r.description[:80]}...")
        print(f"    Category: {r.category} | Tools: {len(r.required_tools)} | Steps: {len(r.steps)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
