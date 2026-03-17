"""Multi-tenant support for isolated per-tenant configuration."""

import os
import re
from contextvars import ContextVar
from typing import Any

import structlog
import yaml
from pydantic import BaseModel

logger = structlog.get_logger("tenants")

# Context variable to track the current tenant in async contexts
_current_tenant: ContextVar[str] = ContextVar("current_tenant", default="default")


class TenantConfig(BaseModel):
    """Configuration for a single tenant."""

    tenant_id: str
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    github_token: str = ""
    github_default_owner: str = ""
    confluence_base_url: str = ""
    confluence_email: str = ""
    confluence_api_token: str = ""
    slack_bot_token: str = ""
    pagerduty_api_key: str = ""
    datadog_api_key: str = ""
    datadog_app_key: str = ""

    def resolve_env_vars(self) -> "TenantConfig":
        """Resolve ${ENV_VAR} references in all string fields."""
        data = self.model_dump()
        resolved: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved[key] = os.environ.get(env_var, "")
            else:
                resolved[key] = value
        return TenantConfig(**resolved)


class TenantContext:
    """Async-safe tenant context manager."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._token: Any = None

    def __enter__(self) -> "TenantContext":
        self._token = _current_tenant.set(self._tenant_id)
        return self

    def __exit__(self, *_: object) -> None:
        if self._token is not None:
            _current_tenant.reset(self._token)

    async def __aenter__(self) -> "TenantContext":
        return self.__enter__()

    async def __aexit__(self, *_: object) -> None:
        self.__exit__()


def get_current_tenant() -> str:
    """Get the current tenant ID from async context."""
    return _current_tenant.get()


class TenantRegistry:
    """Registry of tenant configurations loaded from YAML or environment."""

    def __init__(self) -> None:
        self._tenants: dict[str, TenantConfig] = {}

    def load_from_yaml(self, path: str) -> None:
        """Load tenant configurations from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        tenants_data = data.get("tenants", {})
        for tenant_id, config in tenants_data.items():
            config["tenant_id"] = tenant_id
            tenant = TenantConfig(**config)
            self._tenants[tenant_id] = tenant.resolve_env_vars()

        logger.info("tenants_loaded", count=len(self._tenants), source="yaml")

    def load_from_env(self, prefix: str = "TENANT") -> None:
        """Load tenant configurations from environment variables.

        Expects format: TENANT_<ID>_<FIELD>=value
        Example: TENANT_ACME_JIRA_BASE_URL=https://acme.atlassian.net
        """
        tenant_vars: dict[str, dict[str, str]] = {}
        pattern = re.compile(rf"^{prefix}_([A-Za-z0-9]+)_(.+)$")

        for key, value in os.environ.items():
            match = pattern.match(key)
            if match:
                tenant_id = match.group(1).lower()
                field = match.group(2).lower()
                tenant_vars.setdefault(tenant_id, {})[field] = value

        for tenant_id, fields in tenant_vars.items():
            fields["tenant_id"] = tenant_id
            try:
                self._tenants[tenant_id] = TenantConfig(**fields)
            except Exception as exc:
                logger.warning("tenant_load_failed", tenant_id=tenant_id, error=str(exc))

        logger.info("tenants_loaded", count=len(self._tenants), source="env")

    def get(self, tenant_id: str) -> TenantConfig | None:
        """Get a tenant configuration by ID."""
        return self._tenants.get(tenant_id)

    def get_current(self) -> TenantConfig | None:
        """Get the configuration for the current tenant."""
        return self.get(get_current_tenant())

    def list_tenants(self) -> list[str]:
        """List all registered tenant IDs."""
        return list(self._tenants.keys())

    def register(self, config: TenantConfig) -> None:
        """Register a tenant configuration programmatically."""
        self._tenants[config.tenant_id] = config


# Module-level singleton
_registry: TenantRegistry | None = None


def get_tenant_registry() -> TenantRegistry:
    """Get the global tenant registry singleton."""
    global _registry
    if _registry is None:
        _registry = TenantRegistry()
    return _registry
