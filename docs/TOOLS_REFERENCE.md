# Tools Reference

Complete reference for all 28 MCP tools exposed by the Enterprise MCP Server.

---

## Jira Tools (8)

### `jira_get_issue`
Fetch a Jira issue by its key.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `issue_key` | string | ✓ | Issue key (e.g., `PROJ-123`) |
| `include_comments` | boolean | | Include comments (default: false) |

**Example prompt:** *"Get details for PROJ-456 including all comments"*

---

### `jira_search_issues`
Search issues using JQL (Jira Query Language).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `jql` | string | ✓ | JQL query |
| `max_results` | integer | | Max results (default: 50) |

**Example JQL:** `project = PROJ AND priority = High AND status != Done ORDER BY created DESC`

---

### `jira_create_issue`
Create a new Jira issue.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `project_key` | string | ✓ | Project key (e.g., `PROJ`) |
| `summary` | string | ✓ | Issue title |
| `issue_type` | string | | Bug, Task, Story (default: Task) |
| `description` | string | | Plain text description |
| `priority` | string | | Highest, High, Medium, Low |
| `labels` | array | | String labels |

---

### `jira_update_issue`
Update an issue's status, assignee, priority, or summary.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `issue_key` | string | ✓ | Issue key |
| `status_transition_id` | string | | Transition ID for status change |
| `assignee_account_id` | string | | Atlassian account ID |
| `priority` | string | | New priority |
| `summary` | string | | New summary |

---

### `jira_add_comment`
Add a comment to a Jira issue.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `issue_key` | string | ✓ | Issue key |
| `body` | string | ✓ | Comment text |

---

### `jira_get_sprint`
Get the active sprint for a board.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `board_id` | integer | ✓ | Jira board ID |

---

### `jira_list_projects`
List all accessible Jira projects.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `max_results` | integer | | Max projects (default: 50) |

---

### `jira_get_board`
Get a board's configuration and columns.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `board_id` | integer | ✓ | Jira board ID |

---

## GitHub Tools (8)

### `github_get_repo`
Get repository information.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `repo` | string | ✓ | Repository name |
| `owner` | string | | Owner/org (defaults to `GITHUB_DEFAULT_OWNER`) |

---

### `github_list_issues`
List repository issues with filters.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `repo` | string | ✓ | Repository name |
| `owner` | string | | Owner/org |
| `state` | string | | open, closed, all (default: open) |
| `labels` | string | | Comma-separated label names |
| `max_results` | integer | | Max issues (default: 30) |

---

### `github_create_issue`
Create a new GitHub issue.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `repo` | string | ✓ | Repository name |
| `title` | string | ✓ | Issue title |
| `owner` | string | | Owner/org |
| `body` | string | | Markdown description |
| `labels` | array | | Label names |
| `assignees` | array | | GitHub usernames |

---

### `github_get_pull_request`
Get pull request details including reviews.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `repo` | string | ✓ | Repository name |
| `pr_number` | integer | ✓ | PR number |
| `owner` | string | | Owner/org |

---

### `github_list_pull_requests`
List pull requests with filters.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `repo` | string | ✓ | Repository name |
| `owner` | string | | Owner/org |
| `state` | string | | open, closed, all (default: open) |
| `base` | string | | Base branch filter |
| `max_results` | integer | | Max PRs (default: 30) |

---

### `github_search_code`
Search code across repositories.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | ✓ | Search query |
| `owner` | string | | Restrict to org/owner |
| `repo` | string | | Restrict to repository |
| `max_results` | integer | | Max results (default: 30) |

**Example query:** `"def authenticate" language:python`

---

### `github_get_file_content`
Read a file from a repository.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `repo` | string | ✓ | Repository name |
| `path` | string | ✓ | File path (e.g., `src/main.py`) |
| `owner` | string | | Owner/org |
| `ref` | string | | Branch/tag/SHA |

---

### `github_create_review_comment`
Add an inline review comment to a PR.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `repo` | string | ✓ | Repository name |
| `pr_number` | integer | ✓ | PR number |
| `body` | string | ✓ | Comment text |
| `commit_id` | string | ✓ | Commit SHA |
| `path` | string | ✓ | File path |
| `line` | integer | ✓ | Line number |
| `owner` | string | | Owner/org |

---

## Confluence Tools (6)

### `confluence_get_page`
Fetch a Confluence page by ID.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page_id` | string | ✓ | Numeric page ID |
| `include_body` | boolean | | Include body content (default: true) |

---

### `confluence_search`
Search Confluence using CQL or plain text.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | ✓ | CQL query or search text |
| `space_key` | string | | Restrict to space |
| `max_results` | integer | | Max results (default: 25) |

**Example CQL:** `type = page AND title ~ "runbook" AND space = OPS`

---

### `confluence_create_page`
Create a new Confluence page.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `space_id` | string | ✓ | Space ID |
| `title` | string | ✓ | Page title |
| `body` | string | ✓ | Page content (wiki markup) |
| `parent_page_id` | string | | Parent page ID |

---

### `confluence_update_page`
Update an existing page's content.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page_id` | string | ✓ | Page ID |
| `title` | string | ✓ | New title |
| `body` | string | ✓ | New content |
| `version_number` | integer | ✓ | Current version + 1 |

---

### `confluence_list_spaces`
List all accessible Confluence spaces.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `max_results` | integer | | Max spaces (default: 50) |

---

### `confluence_get_children`
Get child pages of a parent page.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page_id` | string | ✓ | Parent page ID |
| `max_results` | integer | | Max children (default: 25) |

---

## Slack Tools (6)

### `slack_post_message`
Send a message to a channel.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | ✓ | Channel ID or name |
| `text` | string | ✓ | Message text |
| `thread_ts` | string | | Reply in thread |

---

### `slack_get_channel_history`
Fetch recent messages from a channel.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | ✓ | Channel ID |
| `limit` | integer | | Messages to return (default: 50) |
| `oldest` | string | | Unix timestamp lower bound |

---

### `slack_list_channels`
List accessible channels.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `exclude_archived` | boolean | | Exclude archived (default: true) |
| `max_results` | integer | | Max channels (default: 200) |

---

### `slack_get_user_info`
Get a user's profile.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `user_id` | string | ✓ | Slack user ID (e.g., `U1234567890`) |

---

### `slack_add_reaction`
Add an emoji reaction to a message.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | ✓ | Channel ID |
| `timestamp` | string | ✓ | Message timestamp |
| `emoji_name` | string | ✓ | Emoji name (e.g., `white_check_mark`) |

---

### `slack_create_thread_reply`
Reply in an existing thread.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | ✓ | Channel ID |
| `thread_ts` | string | ✓ | Parent message timestamp |
| `text` | string | ✓ | Reply text |
