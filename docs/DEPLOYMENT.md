# Enterprise Deployment Guide

## Prerequisites

- Python 3.11+
- API credentials for the services you want to enable

## Local Development

```bash
# Clone and install
git clone https://github.com/AdrienTHOMAS/enterprise-mcp-server
cd enterprise-mcp-server
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Configure credentials
cp .env.example .env
# Edit .env with your API tokens

# Verify installation
enterprise-mcp --help
```

## Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV JIRA_BASE_URL=""
ENV JIRA_EMAIL=""
ENV JIRA_API_TOKEN=""
ENV GITHUB_TOKEN=""
ENV CONFLUENCE_BASE_URL=""
ENV CONFLUENCE_EMAIL=""
ENV CONFLUENCE_API_TOKEN=""
ENV SLACK_BOT_TOKEN=""

CMD ["python", "-m", "enterprise_mcp.server"]
```

Build and run:
```bash
docker build -t enterprise-mcp-server .
docker run --env-file .env enterprise-mcp-server
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise": {
      "command": "python",
      "args": ["-m", "enterprise_mcp.server"],
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

## Secrets Management

**Never commit credentials to git.** Recommended approaches:

### AWS Secrets Manager
```python
import boto3, json, os

client = boto3.client("secretsmanager", region_name="us-east-1")
secret = json.loads(client.get_secret_value(SecretId="enterprise-mcp/prod")["SecretString"])
for key, value in secret.items():
    os.environ[key] = value
```

### HashiCorp Vault
```bash
vault kv get -format=json secret/enterprise-mcp | jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"' > .env
```

### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: enterprise-mcp-secrets
type: Opaque
stringData:
  JIRA_API_TOKEN: "your-token"
  GITHUB_TOKEN: "your-token"
  SLACK_BOT_TOKEN: "xoxb-your-token"
```

## Monitoring

The server logs to stderr with structured messages. Key log lines:

```
Enterprise MCP Server ready — 28 tools from: Jira (8 tools), GitHub (8 tools), ...
Calling tool: jira_get_issue with args: ['issue_key']
```

Pipe stderr to your logging aggregator (Datadog, CloudWatch, Splunk):

```bash
enterprise-mcp 2>&1 | your-log-shipper
```

## Production Checklist

- [ ] All 4 sets of API credentials configured and tested
- [ ] `.env` file excluded from version control (`.gitignore`)
- [ ] Credentials stored in a secrets manager (not environment files)
- [ ] Server logs routed to aggregator
- [ ] Rate limit headroom assessed for your usage patterns
- [ ] Error alerting configured for `"error":` patterns in tool responses
- [ ] Token rotation schedule established (Jira/Confluence: 90 days, GitHub: 180 days)
