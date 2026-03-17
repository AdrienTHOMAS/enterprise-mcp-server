"""Configuration management using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Enterprise MCP Server configuration loaded from environment variables."""

    # Jira
    jira_base_url: str = Field(
        default="",
        description="Jira Cloud base URL (e.g., https://yourcompany.atlassian.net)",
    )
    jira_email: str = Field(default="", description="Jira user email")
    jira_api_token: str = Field(default="", description="Jira API token")

    # GitHub
    github_token: str = Field(default="", description="GitHub Personal Access Token")
    github_default_owner: str = Field(
        default="", description="Default GitHub org/owner"
    )

    # Confluence
    confluence_base_url: str = Field(
        default="", description="Confluence Cloud base URL"
    )
    confluence_email: str = Field(default="", description="Confluence user email")
    confluence_api_token: str = Field(
        default="", description="Confluence API token"
    )

    # Slack
    slack_bot_token: str = Field(
        default="", description="Slack Bot Token (xoxb-...)"
    )

    # PagerDuty
    pagerduty_api_key: str = Field(default="", description="PagerDuty API key")
    pagerduty_from_email: str = Field(
        default="", description="Default 'From' email for PagerDuty API calls"
    )

    # Datadog
    datadog_api_key: str = Field(default="", description="Datadog API key")
    datadog_app_key: str = Field(default="", description="Datadog Application key")
    datadog_site: str = Field(
        default="datadoghq.com", description="Datadog site (e.g., datadoghq.com, datadoghq.eu)"
    )

    # Redis
    redis_url: str = Field(
        default="", description="Redis connection URL (e.g., redis://localhost:6379/0)"
    )

    # Webhooks
    github_webhook_secret: str = Field(default="", description="GitHub webhook HMAC secret")
    jira_webhook_secret: str = Field(default="", description="Jira webhook HMAC secret")
    slack_signing_secret: str = Field(default="", description="Slack signing secret")

    # OAuth
    github_client_id: str = Field(default="", description="GitHub OAuth App client ID")
    github_client_secret: str = Field(default="", description="GitHub OAuth App client secret")

    # Multi-tenant
    tenant_config_path: str = Field(default="", description="Path to tenant config YAML file")

    # Server
    server_name: str = Field(default="enterprise-mcp", description="MCP server name")
    log_level: str = Field(default="INFO", description="Logging level")
    health_port: int = Field(default=8080, description="Health check HTTP port")
    webhook_port: int = Field(default=8081, description="Webhook server HTTP port")
    otlp_endpoint: str = Field(default="", description="OpenTelemetry OTLP endpoint")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
