# Xiaozhi MCP Hub

Production-oriented MCP aggregation gateway for xiaozhi-esp32 official MCP endpoints.

This repository is a Python + React monorepo:

- `backend/`: FastAPI service, MCP hub core, upstream bridge, downstream connector management, registry, ACL, approvals and audit.
- `frontend/`: React + Vite management UI.
- `deploy/`: Prometheus configuration.
- `examples/`: importable upstream/downstream configuration examples.

## Quick Start

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Default local endpoints:

- WebUI: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Metrics: `http://localhost:8000/metrics`
- Grafana: `http://localhost:3000`

On a fresh database, open the WebUI and register the first account. That first registered user becomes the administrator, and public registration closes automatically. For local automation, set `AUTO_CREATE_INITIAL_ADMIN=true` to create the initial administrator from `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD`.

## Local Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\uvicorn app.main:app --reload
```

The backend-local `backend/.env.example` defaults to `STORE_BACKEND=memory`.
Use `DATABASE_URL=postgresql+asyncpg://xiaozhi:xiaozhi@localhost:5432/xiaozhi_mcp_hub`
if you want local uvicorn to use a local Postgres instance. The repository-root
`.env` is intended for Docker Compose, where the `postgres` hostname exists.

For local frontend development, `npm run dev` serves `http://localhost:5173`
and proxies `/api/*` to `http://127.0.0.1:8000`, so keep the backend running.

## Config Import

See `examples/hub-config.yaml`.

## How Downstream MCP Servers Reach Xiaozhi

1. Copy the official MCP access point from the Xiaozhi console.
2. In the WebUI, open `Xiaozhi` and save the access point with channel `Xiaozhi Official`.
3. Import downstream MCP servers or add them manually.
4. The hub initializes each enabled downstream server, sends `notifications/initialized`, calls `tools/list`, and stores the discovered tools in the registry.
5. Xiaozhi calls the hub over the upstream WebSocket. The hub returns `hub.status` plus all enabled discovered tools from `tools/list`.
6. Xiaozhi calls a unified `tool_id`; the hub routes it back to the original downstream server and tool name.

## MCP Compatibility

| Transport | Status | Notes |
| --- | --- | --- |
| stdio | Supported | Works with common Node/Python tool servers such as filesystem, git, time and memory servers. |
| Streamable HTTP | Supported for JSON-RPC POST + session | Supports `Mcp-Session-Id`, bearer refs and API key refs. |
| legacy SSE | Compatibility path | Works with old services that still expose a POST JSON-RPC endpoint next to SSE. Pure SSE-only loops need future expansion. |

The first version focuses on tool servers: `initialize`, `notifications/initialized`, `tools/list`, and `tools/call`. Resources, prompts, sampling and full OAuth authorization flows are future work.

Common `mcpServers` configs are accepted:

```json
{
  "mcpServers": {
    "demo": {
      "command": "python.exe",
      "args": ["../examples/downstream-mcp/demo_server.py"],
      "namespace": "demo"
    }
  }
}
```

Import returns discovered tool counts and per-server errors:

```json
{
  "upstreams": 0,
  "servers": 1,
  "tools": 3,
  "errors": {},
  "version": 1
}
```

## Demo Downstream Server

See `examples/downstream-mcp/` for a dependency-free stdio MCP server and import configs. After import and discovery it exposes:

- `demo.echo`
- `demo.add`
- `demo.get_server_status`

The hub exposes a unified tool name (`tool_id`) to xiaozhi. By default:

```text
{namespace}.{origin_tool_name}
```

Conflicts are resolved by appending `__{server_id}`.

## Security Defaults

- No upstream token is ever forwarded to downstream servers.
- High and critical risk tools require WebUI approval.
- Credentials are referenced through secret refs and masked in API responses.
- Every MCP call gets a trace id and an audit record.
