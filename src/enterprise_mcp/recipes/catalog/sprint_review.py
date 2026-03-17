"""Sprint Review Report recipe — end-of-sprint summary across Jira, GitHub, Confluence, Slack."""

from ..base import Recipe, RecipeRegistry, RecipeStep

SPRINT_REVIEW = RecipeRegistry.register(
    Recipe(
        name="sprint_review",
        description=(
            "Generates a comprehensive sprint review report: pulls sprint data from Jira, "
            "gathers PR statistics from GitHub, creates a summary page in Confluence, and "
            "posts a digest to the team Slack channel."
        ),
        category="reporting",
        system_prompt=(
            "You are an engineering manager preparing a sprint review for your team and "
            "stakeholders. Focus on:\n"
            "1. Velocity — story points completed vs. committed.\n"
            "2. Completion rate — stories done vs. carried over.\n"
            "3. PR throughput — merged PRs, average review time.\n"
            "4. Blockers — what slowed the team down.\n"
            "5. Highlights — notable achievements or improvements.\n\n"
            "Present data clearly with numbers. Be honest about misses — the goal is "
            "continuous improvement, not vanity metrics. Keep the summary concise enough "
            "to read in 2 minutes."
        ),
        starter_prompt=(
            "Generate the sprint review report for board {{board_id}}. "
            "Pull sprint data, PR stats, and publish the summary."
        ),
        required_tools=[
            "jira_get_sprint",
            "jira_search_issues",
            "github_list_pull_requests",
            "confluence_create_page",
            "slack_post_message",
        ],
        steps=[
            RecipeStep(
                tool_name="jira_get_sprint",
                description="Get the active/latest sprint for the board",
                parameters_template={
                    "board_id": "{{context.board_id}}",
                },
            ),
            RecipeStep(
                tool_name="jira_search_issues",
                description="List all stories in the sprint (completed and incomplete)",
                parameters_template={
                    "jql": "sprint = {{context.sprint_id}} ORDER BY status DESC",
                    "max_results": 50,
                },
            ),
            RecipeStep(
                tool_name="github_list_pull_requests",
                description="Get merged PRs during the sprint period",
                parameters_template={
                    "repo": "{{context.repo}}",
                    "state": "closed",
                },
            ),
            RecipeStep(
                tool_name="confluence_create_page",
                description="Create the sprint review page in Confluence",
                parameters_template={
                    "space_key": "{{context.confluence_space}}",
                    "title": "Sprint Review — {{context.sprint_name}}",
                    "body": "{{context.report_body}}",
                    "parent_id": "{{context.parent_page_id}}",
                },
            ),
            RecipeStep(
                tool_name="slack_post_message",
                description="Post sprint digest to the team channel",
                parameters_template={
                    "channel": "{{context.slack_channel}}",
                    "text": "{{context.digest_message}}",
                },
            ),
        ],
        expected_outputs=[
            "Sprint metadata (name, dates, goal)",
            "Completed vs. incomplete stories with point totals",
            "PR merge statistics for the sprint period",
            "Confluence page with the full sprint review",
            "Slack digest posted to the team channel",
        ],
        tags=["sprint", "review", "report", "velocity", "agile"],
    )
)
