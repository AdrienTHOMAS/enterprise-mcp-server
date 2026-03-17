"""Weekly Engineering Digest recipe — Monday summary across all systems."""

from ..base import Recipe, RecipeRegistry, RecipeStep

WEEKLY_DIGEST = RecipeRegistry.register(
    Recipe(
        name="weekly_digest",
        description=(
            "Weekly engineering digest: pulls Jira velocity metrics, lists merged GitHub PRs, "
            "finds recently updated Confluence pages, and posts a concise executive summary "
            "to the #engineering Slack channel."
        ),
        category="reporting",
        system_prompt=(
            "You are the engineering chief of staff preparing the weekly digest for "
            "leadership and the broader engineering org. Your summary should be:\n"
            "1. **Concise** — executives read this in 60 seconds.\n"
            "2. **Data-driven** — include specific numbers (PRs merged, points completed).\n"
            "3. **Actionable** — highlight blockers that need leadership attention.\n"
            "4. **Celebratory** — call out notable wins and team achievements.\n\n"
            "Structure: Key Metrics > Highlights > Risks/Blockers > Next Week Focus.\n"
            "Keep it under 500 words. Use bullet points, not paragraphs."
        ),
        starter_prompt=(
            "Generate the weekly engineering digest for the {{team_name}} team. "
            "Pull last week's Jira velocity, merged PRs, Confluence updates, and post the summary."
        ),
        required_tools=[
            "jira_search_issues",
            "github_list_pull_requests",
            "confluence_search",
            "slack_post_message",
        ],
        steps=[
            RecipeStep(
                tool_name="jira_search_issues",
                description="Get issues completed last week for velocity metrics",
                parameters_template={
                    "jql": "project = {{context.project_key}} AND status = Done AND resolved >= -7d ORDER BY resolved DESC",
                    "max_results": 50,
                },
            ),
            RecipeStep(
                tool_name="github_list_pull_requests",
                description="List PRs merged in the last week",
                parameters_template={
                    "repo": "{{context.repo}}",
                    "state": "closed",
                },
            ),
            RecipeStep(
                tool_name="confluence_search",
                description="Find recently updated documentation pages",
                parameters_template={
                    "query": "space = {{context.confluence_space}} AND lastModified >= now('-7d')",
                    "max_results": 10,
                },
            ),
            RecipeStep(
                tool_name="slack_post_message",
                description="Post the weekly digest to #engineering",
                parameters_template={
                    "channel": "{{context.slack_channel}}",
                    "text": "{{context.digest_message}}",
                },
            ),
        ],
        expected_outputs=[
            "Jira velocity metrics (completed issues, story points)",
            "List of merged PRs with authors",
            "Recently updated Confluence documentation",
            "Weekly digest posted to #engineering",
        ],
        tags=["weekly", "digest", "report", "metrics", "executive-summary"],
    )
)
