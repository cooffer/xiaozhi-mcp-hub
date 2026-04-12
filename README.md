<p align="center">
  <img src="./logo.png" width="120" alt="Xiaozhi MCP Hub logo" />
</p>

# Xiaozhi MCP Hub

**Language:** English | [简体中文](./README_CN.md)

Xiaozhi MCP Hub is an MCP aggregation gateway for the official Xiaozhi MCP access point. It connects to Xiaozhi as one upstream MCP server, discovers tools from many downstream MCP servers, normalizes their schemas, and exposes them back to Xiaozhi as a single governed tool registry.

The goal is simple: connect existing MCP tools to Xiaozhi quickly, while still keeping the operational controls a real deployment needs.

## What It Does

- Connects to the official Xiaozhi MCP endpoint from the WebUI.
- Aggregates downstream MCP servers through `stdio`, Streamable HTTP, and legacy SSE-compatible endpoints.
- Discovers downstream tools with `initialize`, `notifications/initialized`, `tools/list`, and routes `tools/call` back to the original server.
- Exposes a built-in `hub.status` tool so the Xiaozhi console can verify that the hub is online.
- Provides a React management UI for first-admin setup, Xiaozhi access points, downstream services, tool registry, config import, approvals, and audit logs.
- Adds production-oriented controls: RBAC, tool ACL, high-risk approvals, trace IDs, audit logs, health status, and Prometheus metrics.

## Architecture

```text
Xiaozhi official MCP endpoint
        |
        | WebSocket MCP bridge
        v
Xiaozhi MCP Hub
        |
        | tool registry + ACL + approval + audit
        v
Downstream MCP servers
  - stdio
  - Streamable HTTP
  - legacy SSE-compatible HTTP
```

Tool names exposed to Xiaozhi use a stable `tool_id`:

```text
{namespace}.{origin_tool_name}
```

If two servers expose the same tool ID, the hub appends the server ID:

```text
home.turn_on_light__ha-prod
```

## Quick Start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Default endpoints:

- WebUI: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Prometheus metrics: `http://localhost:8000/metrics`
- Grafana: `http://localhost:3000`

On a fresh database, open the WebUI and register the first account. The first registered user becomes the administrator, and public registration closes automatically.

## Connect Xiaozhi

1. Open the Xiaozhi console and copy the official MCP access point.
2. Open the Hub WebUI.
3. Go to `Xiaozhi`.
4. Select channel `Xiaozhi Official`.
5. Paste the access point and enable it.

Xiaozhi access points are configured only from the WebUI or config import.

## Add Downstream MCP Servers

You can add downstream servers from the WebUI or import YAML/JSON config.

Native config:

```yaml
servers:
  - id: local-demo
    transport: stdio
    command: python.exe
    args: ["../examples/downstream-mcp/demo_server.py"]
    namespace: demo
    enabled: true
```

Common `mcpServers` config:

```json
{
  "mcpServers": {
    "demo": {
      "command": "python.exe",
      "args": ["../examples/downstream-mcp/demo_server.py"],
      "namespace": "demo"
    },
    "remote-tools": {
      "type": "streamable_http",
      "url": "https://example.com/mcp"
    }
  }
}
```

After import, enabled servers are discovered automatically. A tool is exposed to Xiaozhi only after discovery succeeds and the tool is written to the registry.

## Compatibility

| Transport | Status | Notes |
| --- | --- | --- |
| `stdio` | Supported | Works with common Node.js and Python MCP tool servers. |
| `streamable_http` | Supported | JSON-RPC POST, session header, bearer ref, and API key ref are supported. |
| `sse` | Compatible path | Supports common legacy services that still provide a JSON-RPC POST endpoint. |

The current version focuses on tool servers:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`

Resources, prompts, sampling, and full OAuth authorization flows are planned as future extensions.

## Demo Downstream Server

A dependency-free stdio MCP server is included in:

```text
examples/downstream-mcp/
```

It exposes:

- `demo.echo`
- `demo.add`
- `demo.get_server_status`

Import `examples/downstream-mcp/hub-config.yaml` from the WebUI to try it.

When developing your own downstream MCP server for this hub:

- Write only JSON-RPC protocol messages to `stdout`.
- Send logs to `stderr`.
- Provide clear `description` and `inputSchema` values for every tool.
- Return MCP `CallToolResult` shape: `content`, optional `structuredContent`, and `isError`.
- Use a stable namespace to avoid tool conflicts.

## Local Development

Backend:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env
.\venv\Scripts\uvicorn app.main:app --reload
```

`backend/.env.example` uses `STORE_BACKEND=memory` by default so local backend startup does not require Postgres.

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `http://127.0.0.1:8000`.

## Tests

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests
```

Frontend:

```powershell
cd frontend
npm run build
```

## Security Defaults

- The upstream Xiaozhi token is never forwarded to downstream servers.
- High and critical risk tools require WebUI approval.
- Credentials are referenced through secret refs and masked in API responses.
- Every MCP call gets a trace ID and an audit record.
- Built-in roles: `admin`, `operator`, and `viewer`.

## Project Structure

```text
backend/              FastAPI backend and MCP hub core
frontend/             React + Vite management UI
examples/             Importable configs and demo downstream MCP server
deploy/               Prometheus configuration
docker-compose.yml    Local production-like stack
```

## Related Projects

- xiaozhi-esp32: https://github.com/78/xiaozhi-esp32
- mcp-calculator: https://github.com/78/mcp-calculator
- Model Context Protocol: https://modelcontextprotocol.io/specification
