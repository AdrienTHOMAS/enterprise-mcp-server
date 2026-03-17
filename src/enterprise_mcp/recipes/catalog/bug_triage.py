"""Bug Triage recipe — deduplicate, investigate, and classify incoming bugs."""

from ..base import Recipe, RecipeRegistry, RecipeStep

BUG_TRIAGE = RecipeRegistry.register(
    Recipe(
        name="bug_triage",
        description=(
            "Automated bug triage: searches Jira for duplicate bugs, checks GitHub for "
            "related code changes, searches Datadog logs for error evidence, assesses "
            "severity, and creates or links the bug ticket."
        ),
        category="bug_management",
        system_prompt=(
            "You are a senior engineer triaging an incoming bug report. Follow this process:\n"
            "1. **Deduplicate** — search existing Jira bugs for matches. If a duplicate exists, "
            "link it instead of creating a new ticket.\n"
            "2. **Investigate** — check recent GitHub commits/PRs that touch related code paths.\n"
            "3. **Evidence** — search Datadog logs for error patterns matching the report.\n"
            "4. **Classify** — assess severity based on user impact, frequency, and workaround "
            "availability:\n"
            "   - P1: Service down or data loss for many users, no workaround.\n"
            "   - P2: Major feature broken, workaround exists.\n"
            "   - P3: Minor issue, limited impact.\n"
            "   - P4: Cosmetic or edge case.\n"
            "5. **Track** — create a well-structured Jira ticket with reproduction steps, "
            "evidence links, and recommended priority.\n\n"
            "Be thorough in dedup — false duplicates waste more time than false negatives."
        ),
        starter_prompt=(
            "Triage this bug report: {{bug_summary}}. "
            "Check for duplicates, investigate recent changes, search logs, and create a ticket."
        ),
        required_tools=[
            "jira_search_issues",
            "github_list_pull_requests",
            "datadog_search_logs",
            "jira_create_issue",
        ],
        steps=[
            RecipeStep(
                tool_name="jira_search_issues",
                description="Search for existing similar/duplicate bugs",
                parameters_template={
                    "jql": "project = {{context.project_key}} AND type = Bug AND text ~ \"{{context.bug_summary}}\" ORDER BY created DESC",
                    "max_results": 10,
                },
            ),
            RecipeStep(
                tool_name="github_list_pull_requests",
                description="Check recent PRs for related code changes",
                parameters_template={
                    "repo": "{{context.repo}}",
                    "state": "closed",
                },
            ),
            RecipeStep(
                tool_name="datadog_search_logs",
                description="Search Datadog logs for error evidence",
                parameters_template={
                    "query": "{{context.error_query}}",
                    "time_range": "1h",
                },
            ),
            RecipeStep(
                tool_name="jira_create_issue",
                description="Create the bug ticket with findings",
                parameters_template={
                    "project_key": "{{context.project_key}}",
                    "summary": "{{context.bug_summary}}",
                    "issue_type": "Bug",
                    "description": "{{context.bug_description}}",
                    "priority": "{{context.priority}}",
                },
            ),
        ],
        expected_outputs=[
            "Duplicate check results from Jira",
            "Related recent code changes from GitHub",
            "Error log evidence from Datadog",
            "Created or linked Jira bug ticket with severity assessment",
        ],
        tags=["bug", "triage", "dedup", "severity", "logs"],
    )
)
