"""Developer Onboarding recipe — automated setup for new engineers."""

from ..base import Recipe, RecipeRegistry, RecipeStep

ONBOARDING_CHECKLIST = RecipeRegistry.register(
    Recipe(
        name="onboarding_checklist",
        description=(
            "Automated developer onboarding: creates a Jira onboarding epic with setup tasks, "
            "finds setup documentation in Confluence, creates GitHub issues for environment "
            "setup, and invites the new engineer to relevant Slack channels."
        ),
        category="onboarding",
        system_prompt=(
            "You are an engineering team lead onboarding a new developer. Your goal is to "
            "make their first week smooth and productive. Be:\n"
            "1. **Thorough** — cover all setup steps so nothing is missed.\n"
            "2. **Friendly** — this is someone's first impression of the team.\n"
            "3. **Structured** — create clear, ordered tasks with estimates.\n"
            "4. **Contextual** — link to relevant docs, repos, and channels.\n\n"
            "The onboarding epic should cover: dev environment setup, codebase orientation, "
            "access requests, first PR walkthrough, and meet-the-team sessions. Each task "
            "should have a clear definition of done."
        ),
        starter_prompt=(
            "Onboard new engineer {{engineer_name}} to the {{team_name}} team. "
            "Create their onboarding epic, find setup docs, create GitHub issues, "
            "and set up Slack channel invites."
        ),
        required_tools=[
            "jira_create_issue",
            "confluence_search",
            "github_create_issue",
            "slack_post_message",
        ],
        steps=[
            RecipeStep(
                tool_name="jira_create_issue",
                description="Create the onboarding epic in Jira",
                parameters_template={
                    "project_key": "{{context.project_key}}",
                    "summary": "Onboarding: {{context.engineer_name}} — {{context.team_name}}",
                    "issue_type": "Epic",
                    "description": "Onboarding checklist for {{context.engineer_name}} joining {{context.team_name}}.",
                },
            ),
            RecipeStep(
                tool_name="confluence_search",
                description="Find setup documentation and onboarding guides",
                parameters_template={
                    "query": "{{context.team_name}} developer setup onboarding guide",
                    "max_results": 5,
                },
            ),
            RecipeStep(
                tool_name="github_create_issue",
                description="Create GitHub issues for environment setup tasks",
                parameters_template={
                    "repo": "{{context.repo}}",
                    "title": "Onboarding: {{context.engineer_name}} — environment setup",
                    "body": "Setup tasks for new team member. See onboarding epic for full checklist.",
                },
            ),
            RecipeStep(
                tool_name="slack_post_message",
                description="Welcome message and channel invites in Slack",
                parameters_template={
                    "channel": "{{context.slack_channel}}",
                    "text": "Welcome {{context.engineer_name}} to the {{context.team_name}} team! Please check your Jira onboarding epic for setup tasks.",
                },
            ),
        ],
        expected_outputs=[
            "Jira onboarding epic with structured tasks",
            "Links to setup docs and onboarding guides from Confluence",
            "GitHub issues for environment and repo setup",
            "Slack welcome message with channel invites",
        ],
        tags=["onboarding", "new-hire", "setup", "checklist"],
    )
)
