# Architecture

## Overview

The Enterprise MCP Server follows a layered architecture that separates concerns cleanly:

```
Claude (MCP Client)
        │
        │  stdio / SSE
        ▼
┌─────────────────────────────────────────┐
│           MCP Server (server.py)         │
│  list_tools() ──► Tool Registry          │
│  call_tool()  ──► Tool Registry          │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │   Tool Layer    │
        │  jira_tools.py  │
        │  github_tools.py│
        │  confluence_tools│
        │  slack_tools.py │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │ Connector Layer  │
        │  JiraConnector   │
        │  GitHubConnector │
        │  ConfluenceConn. │
        │  SlackConnector  │
        └────────┬────────┘
                 │  HTTPS (httpx async)
        ┌────────┴────────┐
        │ External APIs    │
        │  Jira Cloud v3   │
        │  GitHub REST v3  │
        │  Confluence v2   │
        │  Slack Web API   │
        └─────────────────┘
```

## Layers

### 1. MCP Server (`server.py`)
The entry point. Implements the MCP protocol over stdio using the `mcp` Python SDK. Handles `list_tools` and `call_tool` requests, delegates to the Tool Registry, and manages connector initialization on first use.

### 2. Tool Registry (`tools/registry.py`)
A simple in-memory dictionary mapping tool names → async handler functions. Tools are registered at startup by each `register_*_tools()` function. The registry decouples the MCP protocol layer from business logic.

### 3. Tool Layer (`tools/*.py`)
Each file registers 6–8 MCP `Tool` objects with full JSON Schema `inputSchema` definitions and creates handler closures that wrap the connector methods. Handlers catch all exceptions and return structured JSON error objects — the agent is never left without a response.

### 4. Connector Layer (`connectors/*.py`)
Thin, focused HTTP clients built on `httpx.AsyncClient`. Each connector:
- Lazily initializes its client on first call
- Applies `tenacity` retry logic (3 attempts, exponential backoff 1–10s) to every method
- Calls `_raise_for_status()` with descriptive error context

## Design Decisions

### Why async/await?
MCP servers are I/O bound. Async lets a single process handle multiple simultaneous tool calls efficiently without threading complexity.

### Why tenacity for retries?
The enterprise APIs all have transient failure modes (rate limiting, network blips). `tenacity` provides declarative retry policies without boilerplate, and `reraise=True` ensures callers see the final exception if all retries fail.

### Why httpx over requests?
`httpx` provides a native async API with connection pooling, timeout support, and an interface identical to `requests` for synchronous code. This makes the codebase easy to read for Python engineers familiar with either library.

### Why not use the official Jira/GitHub Python SDKs?
Official client libraries add dependency weight and often lag behind API updates. Direct HTTP calls with `httpx` give full control over request/response handling, and the API surfaces we use (REST) are stable.

### Why lazy connector initialization?
The MCP server must start quickly. Connectors are initialized on the first tool call rather than at startup, which also means the server gracefully handles missing credentials for unused connectors.

### Error handling philosophy
**Connectors raise exceptions.** Tool handlers catch them and return `{"error": "..."}` JSON. This means:
- The MCP client always receives a valid response
- Errors are surfaced to the agent as tool results (not protocol-level errors)
- Claude can reason about failures and try alternative approaches
