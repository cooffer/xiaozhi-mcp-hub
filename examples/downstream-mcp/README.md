# Demo Downstream MCP Server

This folder contains a dependency-free stdio MCP server that can be used to test Xiaozhi MCP Hub.

## Run directly

From the `backend` directory:

```powershell
python.exe ..\examples\downstream-mcp\demo_server.py
```

The server reads JSON-RPC messages from stdin and writes JSON-RPC responses to stdout. Logs and diagnostics must go to stderr so stdout remains valid MCP protocol traffic.

## Import into the hub

In the WebUI, open `Config Import` and import:

```text
examples/downstream-mcp/hub-config.yaml
```

After import, the hub discovers these tools:

- `demo.echo`
- `demo.add`
- `demo.get_server_status`

## Development notes

- Keep tool names stable and simple.
- Provide a clear `description`; Xiaozhi uses it to understand when to call the tool.
- Always return MCP `CallToolResult` shape: `content`, optional `structuredContent`, and `isError`.
- Do not print logs to stdout for stdio servers.
- Use a namespace in hub config to avoid collisions with other MCP servers.
