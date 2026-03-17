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

    # Server
    server_name: str = Field(default="enterprise-mcp", description="MCP server name")
    log_level: str = Field(default="INFO", description="Logging level")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
