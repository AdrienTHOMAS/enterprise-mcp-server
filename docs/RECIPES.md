# Agent Recipes

Pre-built agentic workflows that combine multiple MCP tools into structured, multi-step sequences for common enterprise scenarios.

## Overview

Recipes are declarative workflow definitions. Each recipe includes:

- **System prompt** — persona and instructions for the Claude agent
- **Steps** — ordered sequence of tool calls with parameter templates
- **Context** — user-provided parameters that get injected into steps
- **Expected outputs** — what the recipe produces

Recipes don't replace agent reasoning — they provide structure and guardrails for common workflows while letting the agent adapt to the specific situation.

## Available Recipes

### 1. Incident Triage

| | |
|---|---|
| **Name** | `incident_triage` |
| **Category** | `incident_response` |
| **Trigger** | "P1 alert fired", "Production incident reported" |
| **Tools** | Jira, GitHub, Confluence, PagerDuty, Slack |

**Steps:**
1. Search Jira for open P1 incidents in the project
2. Check recent merged PRs in GitHub for potential root causes
3. Find the relevant runbook in Confluence
4. Check if a PagerDuty incident already exists
5. Create PagerDuty incident if needed (conditional)
6. Post status update to Slack #incidents

**Context parameters:**
- `project_key` — Jira project key (e.g., "INFRA")
- `repo` — GitHub repository (e.g., "company/payment-service")
- `service_name` — Affected service name
- `incident_summary` — Brief description of the incident
- `pagerduty_service_id` — PagerDuty service ID
- `slack_channel` — Slack channel for updates
- `create_pagerduty_incident` — Boolean, whether to create a new PD incident

---

### 2. Sprint Review Report

| | |
|---|---|
| **Name** | `sprint_review` |
| **Category** | `reporting` |
| **Trigger** | "Generate sprint report", "End of sprint" |
| **Tools** | Jira, GitHub, Confluence, Slack |

**Steps:**
1. Get active sprint data from Jira board
2. List completed and incomplete stories
3. Get merged PRs during the sprint period
4. Create sprint review page in Confluence
5. Post digest to team Slack channel

**Context parameters:**
- `board_id` — Jira board ID
- `sprint_id` — Sprint ID
- `sprint_name` — Sprint name for the Confluence page title
- `repo` — GitHub repository
- `confluence_space` — Confluence space key
- `parent_page_id` — Parent page for the review
- `slack_channel` — Team channel
- `report_body` / `digest_message` — Generated content

---

### 3. PR Review Assistant

| | |
|---|---|
| **Name** | `pr_review_assistant` |
| **Category** | `code_review` |
| **Trigger** | "Review this PR", "PR opened" |
| **Tools** | GitHub, Confluence |

**Steps:**
1. Fetch PR details and diff
2. Search for similar past PRs
3. Check coding standards in Confluence
4. Post structured review comment

**Context parameters:**
- `repo` — GitHub repository
- `pr_number` — Pull request number
- `review_body` — Generated review content

---

### 4. Developer Onboarding

| | |
|---|---|
| **Name** | `onboarding_checklist` |
| **Category** | `onboarding` |
| **Trigger** | "Onboard new engineer", "New hire setup" |
| **Tools** | Jira, Confluence, GitHub, Slack |

**Steps:**
1. Create onboarding epic in Jira
2. Find setup documentation in Confluence
3. Create GitHub issues for setup tasks
4. Post welcome message to Slack

**Context parameters:**
- `project_key` — Jira project key
- `engineer_name` — New engineer's name
- `team_name` — Team name
- `repo` — Primary GitHub repository
- `slack_channel` — Team channel

---

### 5. Weekly Engineering Digest

| | |
|---|---|
| **Name** | `weekly_digest` |
| **Category** | `reporting` |
| **Trigger** | "Weekly engineering digest", "Monday summary" |
| **Tools** | Jira, GitHub, Confluence, Slack |

**Steps:**
1. Get issues completed in the last week (Jira)
2. List merged PRs from the past week (GitHub)
3. Find recently updated docs (Confluence)
4. Post digest to #engineering (Slack)

**Context parameters:**
- `project_key` — Jira project key
- `repo` — GitHub repository
- `confluence_space` — Confluence space key
- `team_name` — Team name
- `slack_channel` — Channel for the digest
- `digest_message` — Generated digest content

---

### 6. Bug Triage

| | |
|---|---|
| **Name** | `bug_triage` |
| **Category** | `bug_management` |
| **Trigger** | "New bug report", "Triage this bug" |
| **Tools** | Jira, GitHub, Datadog |

**Steps:**
1. Search Jira for duplicate/similar bugs
2. Check recent PRs for related code changes
3. Search Datadog logs for error evidence
4. Create bug ticket with severity assessment

**Context parameters:**
- `project_key` — Jira project key
- `repo` — GitHub repository
- `bug_summary` — Bug title/description
- `bug_description` — Detailed description
- `error_query` — Datadog log search query
- `priority` — Assessed priority (P1-P4)

---

## Creating Custom Recipes

Define a `Recipe` and register it with the `RecipeRegistry`:

```python
from enterprise_mcp.recipes.base import Recipe, RecipeRegistry, RecipeStep

MY_RECIPE = RecipeRegistry.register(
    Recipe(
        name="my_custom_recipe",
        description="What this recipe does",
        category="my_category",
        system_prompt="You are a ... ",
        starter_prompt="Do the thing for {{project_key}}",
        required_tools=["jira_search_issues", "slack_post_message"],
        steps=[
            RecipeStep(
                tool_name="jira_search_issues",
                description="Search for relevant issues",
                parameters_template={
                    "jql": "project = {{context.project_key}}",
                },
            ),
            RecipeStep(
                tool_name="slack_post_message",
                description="Notify the team",
                parameters_template={
                    "channel": "{{context.channel}}",
                    "text": "Found issues in {{context.project_key}}",
                },
                condition="outputs.jira_search_issues",  # Only if previous step had results
            ),
        ],
        expected_outputs=["Jira search results", "Slack notification"],
        tags=["custom"],
    )
)
```

### Parameter Templates

Use `{{context.key}}` to reference user-provided context and `{{outputs.tool_name}}` to reference output from a previous step.

### Conditional Steps

Set `condition` on a step to make it run only when a condition is truthy:
- `"context.some_flag"` — runs if the context parameter is truthy
- `"outputs.some_tool"` — runs if the referenced tool produced output

## Example Prompts for Claude Desktop

```
"A P1 incident was just reported for the payment service — triage it"

"Generate the sprint review report for board 42"

"Review PR #347 in company/api-gateway"

"Onboard Sarah Chen to the platform team"

"Generate this week's engineering digest"

"Triage this bug: users seeing 403 errors on the settings page"
```

These prompts work best when the MCP server has the relevant connectors configured. The agent will use `list_recipes` to find the matching recipe, then `run_recipe` to execute it with the appropriate context.
