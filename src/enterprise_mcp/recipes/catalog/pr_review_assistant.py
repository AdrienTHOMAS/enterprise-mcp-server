"""PR Review Assistant recipe — structured code review with standards checking."""

from ..base import Recipe, RecipeRegistry, RecipeStep

PR_REVIEW_ASSISTANT = RecipeRegistry.register(
    Recipe(
        name="pr_review_assistant",
        description=(
            "Automated PR review assistant: fetches the PR diff, searches for similar past "
            "PRs, checks coding standards in Confluence, and posts a structured review comment "
            "covering security, performance, and maintainability."
        ),
        category="code_review",
        system_prompt=(
            "You are a senior software engineer conducting a thorough code review. "
            "Your review must cover:\n"
            "1. **Security** — injection risks, auth gaps, secret exposure, unsafe deserialization.\n"
            "2. **Performance** — N+1 queries, unbounded loops, missing pagination, memory leaks.\n"
            "3. **Maintainability** — naming clarity, single responsibility, test coverage, docs.\n"
            "4. **Correctness** — edge cases, error handling, race conditions, data validation.\n\n"
            "Reference the team's coding standards when applicable. Be constructive — suggest "
            "fixes, not just problems. Praise good patterns when you see them. Use inline "
            "comments for specific issues and a summary comment for overall assessment.\n\n"
            "Rate the PR: APPROVE, REQUEST_CHANGES, or COMMENT."
        ),
        starter_prompt=(
            "Review PR #{{pr_number}} in {{repo}}. Check the diff, look for similar PRs, "
            "verify against coding standards, and post your review."
        ),
        required_tools=[
            "github_get_pull_request",
            "github_list_pull_requests",
            "confluence_search",
            "github_create_review_comment",
        ],
        steps=[
            RecipeStep(
                tool_name="github_get_pull_request",
                description="Fetch the PR details and diff",
                parameters_template={
                    "repo": "{{context.repo}}",
                    "pr_number": "{{context.pr_number}}",
                },
            ),
            RecipeStep(
                tool_name="github_list_pull_requests",
                description="Search for similar past PRs in the same area",
                parameters_template={
                    "repo": "{{context.repo}}",
                    "state": "closed",
                },
            ),
            RecipeStep(
                tool_name="confluence_search",
                description="Check coding standards and style guide",
                parameters_template={
                    "query": "coding standards style guide",
                    "max_results": 3,
                },
            ),
            RecipeStep(
                tool_name="github_create_review_comment",
                description="Post structured review comment on the PR",
                parameters_template={
                    "repo": "{{context.repo}}",
                    "pr_number": "{{context.pr_number}}",
                    "body": "{{context.review_body}}",
                },
            ),
        ],
        expected_outputs=[
            "PR diff and metadata",
            "Similar past PRs for context",
            "Applicable coding standards from Confluence",
            "Structured review comment posted on the PR",
        ],
        tags=["pr", "review", "code-review", "security", "quality"],
    )
)
