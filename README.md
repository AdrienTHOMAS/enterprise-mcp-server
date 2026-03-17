# Enterprise MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![28 Tools](https://img.shields.io/badge/tools-28-purple.svg)](#tools-reference)

**Enterprise-grade MCP server exposing Jira, GitHub, Confluence, and Slack to Claude agents.**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION INCIDENT TRIAGE                       │
│                                                                       │
│  Claude ──► jira_search_issues("priority=P1 AND status=Open")       │
│         ◄── [INFRA-892] Payment service: 500 errors on /checkout     │
│                                                                       │
│  Claude ──► github_list_pull_requests("payment-service")             │
│         ◄── PR #347: "Refactor timeout config" — merged 2h ago       │
│                                                                       │
│  Claude ──► confluence_search("payment service runbook")             │
│         ◄── [OPS] Incident Response: Payment Services — v4           │
│                                                                       │
│  Claude ──► slack_post_message("#incidents", "P1 ACTIVE: payment...") │
│         ◄── Message posted · ts: 1705312800.000001                   │
│                                                                       │
│  "Root cause identified: PR #347 introduced a misconfigured          │
│   connection pool timeout. Rolling back now. ETA: 8 minutes."        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Why This Exists

Enterprise teams adopting Claude face a recurring challenge: **their critical data lives in Jira tickets, GitHub PRs, Confluence pages, and Slack threads** — not in the conversation window.

This MCP server bridges that gap. Instead of copy-pasting context into every prompt, Claude connects directly to your enterprise systems and acts as a true workflow partner: triaging incidents across tools, synthesizing sprint data, answering "what's the status of X?" with actual data, and drafting responses based on real history.

This is the type of artifact a Forward Deployed Engineer delivers to enterprise clients in the first weeks of engagement. It's not a demo — it's the starting point for production integrations.

---

## Architecture

```
                    Claude (MCP Client)
                           │
                    stdio transport
                           │
              ┌────────────▼────────────┐
              │    MCP Server Layer      │
              │   server.py             │
              │   list_tools()          │
              │   call_tool()           │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │     Tool Registry       │
              │   28 tools, auto-disco  │
              └──┬──────┬──────┬──────┬─┘
                 │      │      │      │
           ┌─────▼──┐ ┌─▼──┐ ┌▼───┐ ┌▼────┐
           │  Jira  │ │ GH │ │ CF │ │Slack│
           │ 8 tools│ │8 t.│ │6 t.│ │6 t. │
           └─────┬──┘ └─┬──┘ └┬───┘ └┬────┘
                 │      │     │      │
           ┌─────▼──────▼─────▼──────▼────┐
           │       Connector Layer         │
           │   httpx + tenacity retry      │
           └─────┬──────┬─────┬──────┬────┘
                 │      │     │      │
           ┌─────▼──┐ ┌─▼──┐ ┌▼───┐ ┌▼────┐
           │Jira API│ │GH  │ │CF  │ │Slack│
           │ REST v3│ │REST│ │ v2 │ │ API │
           └────────┘ └────┘ └────┘ └─────┘
```

**Key design choices:**
- **Async throughout** — `httpx.AsyncClient` for all HTTP, never blocks
- **Retry with backoff** — `tenacity` (3 attempts, exp. backoff 1–10s) on every API call
- **Graceful degradation** — connectors with missing credentials are silently skipped
- **Error isolation** — tool handlers catch all exceptions, return structured `{"error": ...}` JSON so Claude can reason about failures

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/AdrienTHOMAS/enterprise-mcp-server
cd enterprise-mcp-server
pip install -e .

# 2. Configure credentials
cp .env.example .env
# Edit .env with your API tokens (configure only the services you need)

# 3. Test the server starts
python -m enterprise_mcp.server

# 4. Run the demo agent
export ANTHROPIC_API_KEY=sk-ant-...
python examples/agent_demo.py
```

That's it. The server auto-discovers all configured connectors and registers their tools.

---

## Tools Reference

### Jira (8 tools)

| Tool | Description |
|------|-------------|
| `jira_get_issue` | Fetch full issue details by key (PROJ-123) |
| `jira_search_issues` | JQL search — find issues, sprints, bugs |
| `jira_create_issue` | Create bug, task, or story |
| `jira_update_issue` | Transition status, reassign, change priority |
| `jira_add_comment` | Add comment to an issue |
| `jira_get_sprint` | Active sprint info for a board |
| `jira_list_projects` | All accessible projects |
| `jira_get_board` | Board configuration and columns |

### GitHub (8 tools)

| Tool | Description |
|------|-------------|
| `github_get_repo` | Repo metadata: stars, forks, open issues |
| `github_list_issues` | Issues with state/label/assignee filters |
| `github_create_issue` | Create issue with labels and assignees |
| `github_get_pull_request` | PR details including review status |
| `github_list_pull_requests` | Open/closed PRs with branch filters |
| `github_search_code` | Search code with GitHub syntax |
| `github_get_file_content` | Read any file from any branch |
| `github_create_review_comment` | Inline PR review comment |

### Confluence (6 tools)

| Tool | Description |
|------|-------------|
| `confluence_get_page` | Page content by ID |
| `confluence_search` | CQL search across spaces |
| `confluence_create_page` | Create page in any space |
| `confluence_update_page` | Update page content and title |
| `confluence_list_spaces` | All accessible spaces |
| `confluence_get_children` | Child pages of a parent |

### Slack (6 tools)

| Tool | Description |
|------|-------------|
| `slack_post_message` | Send message to channel |
| `slack_get_channel_history` | Recent messages with timestamps |
| `slack_list_channels` | All accessible channels |
| `slack_get_user_info` | User profile and status |
| `slack_add_reaction` | Add emoji reaction to message |
| `slack_create_thread_reply` | Reply in existing thread |

---

## Use Cases

### 1. Production Incident Triage

> *"There's a payment service outage. Help me triage it."*

Claude will:
1. Search Jira for open P1/P2 incidents tagged with `payment`
2. Check GitHub for recent commits and merged PRs to the payment service
3. Look up the incident response runbook in Confluence
4. Post a status update with findings to `#incidents`
5. Add a comment to the Jira ticket with the root cause hypothesis

```bash
python examples/incident_response.py --service payment-service --severity P1
```

### 2. Sprint Review Generation

> *"Generate a sprint review report for Sprint 24, board 42."*

Claude will:
1. Fetch the active sprint details from Jira
2. Search all completed issues: `sprint = "Sprint 24" AND status = Done`
3. List merged PRs from GitHub for the sprint period
4. Search Confluence for new/updated documentation
5. Draft and post a sprint summary to Slack
6. Return a full markdown report with velocity metrics

```bash
python examples/sprint_review.py --board-id 42 --sprint-name "Sprint 24" --repo my-service
```

### 3. Cross-Tool Status Check

> *"What's the status of the authentication refactor? Check everything."*

Claude will:
1. Search Jira: `text ~ "authentication refactor" ORDER BY updated DESC`
2. Search GitHub code: `"auth refactor" repo:my-org/my-service`
3. List open PRs filtered by base branch `feature/auth-refactor`
4. Search Confluence for design docs
5. Check `#eng-auth` Slack channel history for context
6. Synthesize a complete status report

---

## Configuration

All configuration is via environment variables (or `.env` file):

```bash
# Jira Cloud
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=you@yourcompany.com
JIRA_API_TOKEN=your_api_token          # Atlassian account settings

# GitHub
GITHUB_TOKEN=ghp_your_pat             # github.com/settings/tokens
GITHUB_DEFAULT_OWNER=your-org         # Default org for tool calls

# Confluence Cloud (often same base URL as Jira)
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
CONFLUENCE_EMAIL=you@yourcompany.com
CONFLUENCE_API_TOKEN=your_api_token   # Same token as Jira works

# Slack
SLACK_BOT_TOKEN=xoxb-...              # api.slack.com/apps → OAuth

# Server
SERVER_NAME=enterprise-mcp            # Name shown in Claude
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
```

**Partial configuration is supported** — you can configure only Jira and GitHub and skip Confluence/Slack. The server will register only the tools it has credentials for.

---

## Running with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise": {
      "command": "python",
      "args": ["-m", "enterprise_mcp.server"],
      "cwd": "/path/to/enterprise-mcp-server",
      "env": {
        "JIRA_BASE_URL": "https://yourcompany.atlassian.net",
        "JIRA_EMAIL": "you@yourcompany.com",
        "JIRA_API_TOKEN": "your_token",
        "GITHUB_TOKEN": "ghp_your_token",
        "GITHUB_DEFAULT_OWNER": "your-org",
        "CONFLUENCE_BASE_URL": "https://yourcompany.atlassian.net",
        "CONFLUENCE_EMAIL": "you@yourcompany.com",
        "CONFLUENCE_API_TOKEN": "your_token",
        "SLACK_BOT_TOKEN": "xoxb-your-token"
      }
    }
  }
}
```

Restart Claude Desktop. You'll see 28 tools appear in the tool picker.

---

## Running with Python Agent

```python
import asyncio
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "enterprise_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Discover all available tools
            tools_response = await session.list_tools()
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in tools_response.tools
            ]

            print(f"{len(tools)} tools available")

            # Use with the Anthropic API
            client = anthropic.Anthropic()
            messages = [{"role": "user", "content": "What Jira projects do I have access to?"}]

            while True:
                response = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=4096,
                    tools=tools,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    print(response.content[0].text)
                    break

                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            result = await session.call_tool(block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result.content[0].text,
                            })

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})

asyncio.run(run())
```

---

## Enterprise Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["python", "-m", "enterprise_mcp.server"]
```

```bash
docker build -t enterprise-mcp-server .
docker run --env-file .env enterprise-mcp-server
```

### Secrets Management

**Never commit credentials.** Use your secrets manager of choice:

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id enterprise-mcp/prod \
  | jq -r '.SecretString | fromjson | to_entries[] | "\(.key)=\(.value)"' > .env

# HashiCorp Vault
vault kv get -format=json secret/enterprise-mcp \
  | jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"' > .env
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enterprise-mcp-server
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: enterprise-mcp
          image: enterprise-mcp-server:latest
          envFrom:
            - secretRef:
                name: enterprise-mcp-secrets
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=enterprise_mcp --cov-report=term-missing

# Type check
mypy src/

# Lint
ruff check src/ tests/
```

### Running Tests

Tests use `respx` to mock `httpx` calls — no real API credentials needed:

```bash
pytest tests/test_jira_tools.py -v
pytest tests/test_github_tools.py -v
pytest tests/test_confluence_tools.py -v
pytest tests/test_slack_tools.py -v
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Add tests for any new connector methods
4. Ensure `pytest` and `mypy` pass
5. Submit a pull request

---

## License

MIT — see [LICENSE](LICENSE).

---

*Built as a demonstration of enterprise MCP integration patterns.*
*The architecture, tool design, and deployment patterns reflect real-world Forward Deployed Engineering work.*
