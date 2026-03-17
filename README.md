# Enterprise MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![38 Tools](https://img.shields.io/badge/tools-38-purple.svg)](#tools-reference)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](#docker-deployment)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF.svg)](.github/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-report-brightgreen.svg)](#testing)

**Production-grade MCP server exposing Jira, GitHub, Confluence, Slack, PagerDuty, and Datadog to Claude agents with 38 tools, Redis caching, circuit breakers, webhooks, and multi-tenant support.**

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PRODUCTION INCIDENT TRIAGE                        │
│                                                                        │
│  Claude ──► jira_search_issues("priority=P1 AND status=Open")         │
│         ◄── [INFRA-892] Payment service: 500 errors on /checkout       │
│                                                                        │
│  Claude ──► pagerduty_list_incidents(statuses=["triggered"])           │
│         ◄── INC-2891: Payment API 5xx spike — urgency: high            │
│                                                                        │
│  Claude ──► datadog_search_logs("service:payment status:error")        │
│         ◄── 342 error logs in last hour — connection pool exhaustion   │
│                                                                        │
│  Claude ──► github_list_pull_requests("payment-service")               │
│         ◄── PR #347: "Refactor timeout config" — merged 2h ago         │
│                                                                        │
│  Claude ──► confluence_search("payment service runbook")               │
│         ◄── [Runbook] Payment Service Recovery Procedures               │
│                                                                        │
│  Claude ──► slack_post_message("#incidents", "Root cause: PR #347...")  │
│         ◄── Message posted to #incidents                                │
│                                                                        │
│  Claude ──► pagerduty_acknowledge_incident("INC-2891")                 │
│         ◄── Incident acknowledged                                       │
└────────────────────────────────────────────────────────────────────────┘
```

## Why Enterprise MCP Server?

Claude can only interact with external systems through **tools**. The Model Context Protocol (MCP) standardizes how these tools are defined and called. This server provides **38 production-ready tools** across 6 enterprise platforms, enabling Claude agents to:

- **Triage production incidents** across Jira, PagerDuty, and Datadog
- **Review and manage code** across GitHub repositories
- **Access and update documentation** in Confluence
- **Communicate with teams** via Slack
- **Monitor infrastructure** through Datadog metrics and logs

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────────────────────┐
│ Claude Agent │────►│            Enterprise MCP Server                │
│  (MCP Client)│◄────│                                                 │
└─────────────┘     │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
                    │  │  Tool    │  │ Circuit  │  │   Redis      │  │
                    │  │ Registry │  │ Breakers │  │   Cache      │  │
                    │  └──────────┘  └──────────┘  └──────────────┘  │
                    │                                                 │
                    │  ┌─────────────────────────────────────────┐   │
                    │  │           Connectors Layer               │   │
                    │  │  Jira │ GitHub │ Confluence │ Slack      │   │
                    │  │  PagerDuty │ Datadog                    │   │
                    │  └─────────────────────────────────────────┘   │
                    │                                                 │
                    │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
                    │  │ Webhook  │  │  Health   │  │  Multi-     │  │
                    │  │ Server   │  │ Endpoint  │  │  Tenant     │  │
                    │  │ :8081    │  │ :8080     │  │  Support    │  │
                    │  └──────────┘  └──────────┘  └──────────────┘  │
                    │                                                 │
                    │  ┌──────────────────────────────────────────┐  │
                    │  │     Observability (structlog + OTel)      │  │
                    │  └──────────────────────────────────────────┘  │
                    └─────────────────────────────────────────────────┘
                                        │
          ┌──────┬──────┬──────┬────────┼────────┬──────┐
          ▼      ▼      ▼      ▼        ▼        ▼      ▼
        Jira  GitHub Conflu  Slack  PagerDuty  Datadog  Redis
```

## Quick Start

### 1. Install

```bash
git clone https://github.com/AdrienTHOMAS/enterprise-mcp-server.git
cd enterprise-mcp-server
make install
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run

```bash
# Run MCP server directly
enterprise-mcp

# Or with Docker
make docker-up
```

## Tools Reference (38 Tools)

### Jira (8 tools)

| Tool | Description |
|------|-------------|
| `jira_get_issue` | Fetch issue details by key |
| `jira_search_issues` | Search with JQL |
| `jira_create_issue` | Create a new issue |
| `jira_update_issue` | Update fields or transition status |
| `jira_add_comment` | Add a comment to an issue |
| `jira_get_sprint` | Get active sprint for a board |
| `jira_list_projects` | List all accessible projects |
| `jira_get_board` | Get board configuration |

### GitHub (8 tools)

| Tool | Description |
|------|-------------|
| `github_get_repo` | Get repository metadata |
| `github_list_issues` | List issues with filters |
| `github_create_issue` | Create a new issue |
| `github_get_pull_request` | Get PR details + reviews |
| `github_list_pull_requests` | List PRs with filters |
| `github_search_code` | Search code across repos |
| `github_get_file_content` | Read file content |
| `github_create_review_comment` | Add inline PR review comment |

### Confluence (6 tools)

| Tool | Description |
|------|-------------|
| `confluence_get_page` | Fetch page content by ID |
| `confluence_search` | Search with CQL |
| `confluence_create_page` | Create a new page |
| `confluence_update_page` | Update page content |
| `confluence_list_spaces` | List accessible spaces |
| `confluence_get_children` | Get child pages |

### Slack (6 tools)

| Tool | Description |
|------|-------------|
| `slack_post_message` | Send a message to a channel |
| `slack_get_channel_history` | Fetch message history |
| `slack_list_channels` | List all channels |
| `slack_get_user_info` | Get user profile |
| `slack_add_reaction` | Add emoji reaction |
| `slack_create_thread_reply` | Reply in a thread |

### PagerDuty (5 tools)

| Tool | Description |
|------|-------------|
| `pagerduty_get_incident` | Get incident details |
| `pagerduty_list_incidents` | List incidents with filters |
| `pagerduty_acknowledge_incident` | Acknowledge an incident |
| `pagerduty_resolve_incident` | Resolve an incident |
| `pagerduty_create_incident` | Create a new incident |

### Datadog (5 tools)

| Tool | Description |
|------|-------------|
| `datadog_get_metrics` | Query time series metrics |
| `datadog_list_monitors` | List monitors with filters |
| `datadog_get_monitor_status` | Get monitor status |
| `datadog_create_event` | Create a Datadog event |
| `datadog_search_logs` | Search logs |

## Production Deployment

### Docker

```bash
# Build and start all services
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

The `docker-compose.yml` includes:
- **mcp-server**: The MCP server with health checks
- **redis**: Cache backend with persistence
- **redis-commander**: Web UI for Redis debugging (port 8082)

### Environment Management

```bash
# Copy and configure
cp .env.example .env

# Required: at least one connector's credentials
# Optional: Redis, webhooks, OAuth, multi-tenant
```

### Health Checks

The server exposes health endpoints on port 8080:

```bash
# Overall health
curl http://localhost:8080/health

# Response:
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 3600.5,
  "services": {
    "jira": {"status": "healthy", "latency_ms": 45.2},
    "github": {"status": "healthy", "latency_ms": 32.1},
    "cache": {"status": "healthy", "stats": {"backend": "redis", "hit_rate": 0.85}}
  },
  "tool_metrics": {
    "jira_search_issues": {"total_calls": 150, "avg_latency_ms": 120.5, "error_rate": 0.01}
  }
}

# Kubernetes probes
curl http://localhost:8080/health/live   # Liveness
curl http://localhost:8080/health/ready  # Readiness
```

### Webhooks

The webhook server listens on port 8081 for events from:
- **GitHub**: `POST /webhooks/github` (push, PR, review events)
- **Jira**: `POST /webhooks/jira` (issue created/updated/commented)
- **Slack**: `POST /webhooks/slack` (Events API)

All endpoints validate HMAC-SHA256 signatures when secrets are configured.

## Architecture Decisions

### Why Redis for Caching?

- **Sub-millisecond reads** for frequently accessed data (Jira issues, GitHub files)
- **TTL-based expiration** per resource type (60s for Jira, 300s for GitHub files)
- **Shared cache** across multiple MCP server instances
- **Automatic fallback** to in-memory cache if Redis is unavailable

### Why Circuit Breakers?

External APIs can fail or slow down. Circuit breakers:
- **Prevent cascade failures**: Stop hammering a failing API
- **Fast fail**: Return errors immediately instead of waiting for timeouts
- **Auto-recovery**: Periodically test if the API is back (HALF_OPEN state)
- **Per-service isolation**: A Jira outage doesn't affect GitHub operations

### Why Structured Logging?

- **JSON format**: Machine-parseable for log aggregation (ELK, Datadog, Splunk)
- **Context propagation**: Request ID, tenant ID, tool name in every log line
- **OpenTelemetry spans**: Distributed tracing for tool call latencies

### Why Multi-Tenant?

Enterprise environments often serve multiple teams/clients:
- **Isolated credentials**: Each tenant has their own API tokens
- **Async-safe context**: `contextvars` tracks the current tenant per request
- **YAML or env config**: Flexible configuration loading

## Monitoring

### Metrics

Every tool call is instrumented with:
- **Counter**: Total calls per tool
- **Histogram**: Latency distribution (avg, p99)
- **Error rate**: Per-tool error tracking

### OpenTelemetry

Traces are exported via OTLP. Configure with:
```bash
OTLP_ENDPOINT=http://otel-collector:4317
```

### Performance

- Handles **1000+ concurrent tool calls** (verified by load tests)
- Redis cache reduces API calls by **60-85%** for read operations
- Circuit breakers prevent thundering herd on API failures

## Testing

```bash
# Unit tests
make test

# With coverage report
make test-cov

# Integration tests
make test-integration

# All tests
pytest tests/ -v
```

## Development

```bash
# Install dev dependencies
make install

# Lint
make lint

# Format
make format

# Type check
make typecheck
```

## Configuration Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `JIRA_BASE_URL` | For Jira | Jira Cloud base URL |
| `JIRA_EMAIL` | For Jira | Jira user email |
| `JIRA_API_TOKEN` | For Jira | Jira API token |
| `GITHUB_TOKEN` | For GitHub | GitHub PAT |
| `GITHUB_DEFAULT_OWNER` | No | Default org/owner |
| `CONFLUENCE_BASE_URL` | For Confluence | Confluence base URL |
| `CONFLUENCE_EMAIL` | For Confluence | Confluence email |
| `CONFLUENCE_API_TOKEN` | For Confluence | Confluence API token |
| `SLACK_BOT_TOKEN` | For Slack | Slack bot token |
| `PAGERDUTY_API_KEY` | For PagerDuty | PagerDuty API key |
| `PAGERDUTY_FROM_EMAIL` | No | Default from email |
| `DATADOG_API_KEY` | For Datadog | Datadog API key |
| `DATADOG_APP_KEY` | For Datadog | Datadog application key |
| `DATADOG_SITE` | No | Datadog site (default: datadoghq.com) |
| `REDIS_URL` | No | Redis URL for caching |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `HEALTH_PORT` | No | Health check port (default: 8080) |
| `WEBHOOK_PORT` | No | Webhook port (default: 8081) |
| `OTLP_ENDPOINT` | No | OpenTelemetry collector endpoint |

## Claude Desktop Integration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise": {
      "command": "enterprise-mcp",
      "env": {
        "JIRA_BASE_URL": "https://yourcompany.atlassian.net",
        "JIRA_EMAIL": "you@company.com",
        "JIRA_API_TOKEN": "your-token",
        "GITHUB_TOKEN": "ghp_your-token"
      }
    }
  }
}
```

## License

MIT License — see [LICENSE](LICENSE) for details.
