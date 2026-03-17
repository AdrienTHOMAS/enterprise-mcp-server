# ---- Builder stage -------------------------------------------------------- #
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip install --no-cache-dir --prefix=/install dist/*.whl

# ---- Runtime stage -------------------------------------------------------- #
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Enterprise MCP Server" \
      org.opencontainers.image.description="Production-grade MCP server for Claude — 38 tools across Jira, GitHub, Confluence, Slack, PagerDuty, Datadog" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.source="https://github.com/AdrienTHOMAS/enterprise-mcp-server"

# Create non-root user
RUN groupadd --gid 1000 mcp && \
    useradd --uid 1000 --gid mcp --shell /bin/bash --create-home mcp

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create directories for logs and config
RUN mkdir -p /app/logs /app/config && \
    chown -R mcp:mcp /app

WORKDIR /app

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health/live')" || exit 1

# Expose health and webhook ports
EXPOSE 8080 8081

# Default entrypoint runs the MCP server
ENTRYPOINT ["enterprise-mcp"]
