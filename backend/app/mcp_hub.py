from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING
from typing import Any

from .acl import AccessControlService
from .approvals import ApprovalRejected, ApprovalRequired, ApprovalService
from .audit import AuditService
from .domain import ToolCallContext, UserRole
from .limiter import SlidingWindowLimiter
from .registry import to_mcp_tool
from .routing import RouteNotFound, RoutePolicy, Router
from .store import InMemoryStore

if TYPE_CHECKING:
    from .connector_manager import ConnectorManager

HUB_STATUS_TOOL_NAME = "hub.status"

HUB_STATUS_TOOL = {
    "name": HUB_STATUS_TOOL_NAME,
    "description": "Return Xiaozhi MCP Hub connection and registry status. This built-in read-only tool is always available so Xiaozhi can verify that the MCP hub is connected.",
    "inputSchema": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "annotations": {
        "displayName": "Hub Status",
        "riskLevel": "low",
        "serverId": "builtin",
        "originToolName": HUB_STATUS_TOOL_NAME,
        "tags": ["builtin", "status", "xiaozhi"],
    },
}


class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, data: Any | None = None) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class McpHub:
    def __init__(
        self,
        store: InMemoryStore,
        connectors: "ConnectorManager",
        acl: AccessControlService,
        approvals: ApprovalService,
        audit: AuditService,
        limiter: SlidingWindowLimiter | None = None,
    ) -> None:
        self.store = store
        self.connectors = connectors
        self.acl = acl
        self.approvals = approvals
        self.audit = audit
        self.router = Router()
        self.limiter = limiter or SlidingWindowLimiter()

    async def handle(self, message: dict[str, Any] | list[dict[str, Any]], context: ToolCallContext | None = None) -> dict[str, Any] | list[dict[str, Any]] | None:
        context = context or ToolCallContext()
        if isinstance(message, list):
            responses = [await self._handle_one(item, context) for item in message]
            return [item for item in responses if item is not None]
        return await self._handle_one(message, context)

    async def _handle_one(self, message: dict[str, Any], context: ToolCallContext) -> dict[str, Any] | None:
        request_id = message.get("id")
        try:
            if message.get("jsonrpc") != "2.0":
                raise JsonRpcError(-32600, "Invalid JSON-RPC version")
            method = message.get("method")
            if not method:
                return None
            result = await self._dispatch(method, message.get("params") or {}, context)
            if request_id is None:
                return None
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except JsonRpcError as exc:
            if request_id is None:
                return None
            error: dict[str, Any] = {"code": exc.code, "message": exc.message}
            if exc.data is not None:
                error["data"] = exc.data
            return {"jsonrpc": "2.0", "id": request_id, "error": error}
        except Exception as exc:
            if request_id is None:
                return None
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": str(exc)}}

    async def _dispatch(self, method: str, params: dict[str, Any], context: ToolCallContext) -> dict[str, Any]:
        if method == "initialize":
            protocol_version = params.get("protocolVersion") or params.get("protocol_version") or "2025-11-25"
            return {
                "protocolVersion": protocol_version if protocol_version in {"2025-11-25", "2024-11-05"} else "2024-11-05",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "xiaozhi-mcp-hub", "version": "0.1.0"},
            }
        if method == "notifications/initialized":
            return {}
        if method == "ping":
            return {}
        if method == "tools/list":
            return await self.list_tools(params, context)
        if method == "tools/call":
            return await self.call_tool(params, context)
        raise JsonRpcError(-32601, f"Method not found: {method}")

    async def list_tools(self, params: dict[str, Any], context: ToolCallContext) -> dict[str, Any]:
        cursor = str(params.get("cursor") or "")
        page_size = int(params.get("limit") or 50)
        all_tools = await self.store.list_tools(tenant_id=context.tenant_id, enabled=True)
        visible = [tool for tool in all_tools if tool.tool_id != HUB_STATUS_TOOL_NAME and await self.acl.can_list_tool(tool, context)]
        start = int(cursor) if cursor.isdigit() else 0
        exposed_tools = [HUB_STATUS_TOOL, *[to_mcp_tool(tool) for tool in visible]]
        page = exposed_tools[start : start + page_size]
        result: dict[str, Any] = {"tools": page}
        if start + page_size < len(exposed_tools):
            result["nextCursor"] = str(start + page_size)
        return result

    async def call_tool(self, params: dict[str, Any], context: ToolCallContext) -> dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str):
            raise JsonRpcError(-32602, "tools/call missing name")
        if not isinstance(arguments, dict):
            raise JsonRpcError(-32602, "tools/call arguments must be an object")
        if not self.limiter.allow(f"{context.tenant_id}:{name}"):
            raise JsonRpcError(-32029, "rate limit exceeded")

        start = time.monotonic()
        if name == HUB_STATUS_TOOL_NAME:
            result = await self._hub_status(context)
            latency = (time.monotonic() - start) * 1000
            await self.audit.record(context, "tools/call", status="ok", tool_id=name, server_id="builtin", latency_ms=latency)
            return result

        tool = await self.store.get_tool(name)
        if tool is None:
            raise JsonRpcError(-32601, f"Unknown tool: {name}")
        if not await self.acl.can_call_tool(tool, context):
            await self.audit.record(context, "tools/call", status="denied", tool_id=name)
            raise JsonRpcError(-32003, "permission denied")
        try:
            await self.approvals.assert_approved_or_raise(tool, arguments, context)
            servers = await self.store.list_servers()
            server = self.router.route(tool, servers, RoutePolicy())
            response = await self.connectors.call_tool(server, tool.origin_tool_name, arguments)
            latency = (time.monotonic() - start) * 1000
            await self.audit.record(context, "tools/call", status="ok", tool_id=name, server_id=server.id, latency_ms=latency)
            return response.to_mcp_result()
        except ApprovalRequired as exc:
            await self.audit.record(context, "tools/call", status="approval_pending", tool_id=name, metadata={"approval_id": exc.approval.id})
            raise JsonRpcError(-32010, "approval_pending", {"approval_id": exc.approval.id})
        except ApprovalRejected as exc:
            await self.audit.record(context, "tools/call", status="approval_rejected", tool_id=name, error=str(exc))
            raise JsonRpcError(-32011, "approval_rejected")
        except RouteNotFound as exc:
            await self.audit.record(context, "tools/call", status="route_not_found", tool_id=name, error=str(exc))
            raise JsonRpcError(-32004, str(exc)) from exc
        except Exception as exc:
            await self.audit.record(context, "tools/call", status="error", tool_id=name, error=str(exc))
            raise

    async def _hub_status(self, context: ToolCallContext) -> dict[str, Any]:
        servers = await self.store.list_servers()
        tools = await self.store.list_tools(tenant_id=context.tenant_id, enabled=True)
        upstreams = await self.store.list_upstreams()
        payload = {
            "status": "ok",
            "hub": "xiaozhi-mcp-hub",
            "tenant_id": context.tenant_id,
            "upstream_id": context.upstream_id,
            "upstreams": len([item for item in upstreams if item.tenant_id == context.tenant_id and item.enabled]),
            "servers": len([item for item in servers if item.tenant_id == context.tenant_id]),
            "healthy_servers": len([item for item in servers if item.tenant_id == context.tenant_id and item.status.value == "healthy"]),
            "tools": len(tools),
        }
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Xiaozhi MCP Hub is connected. "
                        f"Tenant: {payload['tenant_id']}. "
                        f"Upstreams: {payload['upstreams']}. "
                        f"Servers: {payload['servers']}. "
                        f"Tools: {payload['tools']}."
                    ),
                },
                {"type": "text", "text": json.dumps(payload, ensure_ascii=False, separators=(",", ":"))},
            ],
            "isError": False,
        }


def system_context(tenant_id: str = "default") -> ToolCallContext:
    return ToolCallContext(tenant_id=tenant_id, actor_role=UserRole.OPERATOR, actor_id="system")
