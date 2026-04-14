"""Streamable HTTP 下游 MCP connector。

当前实现聚焦工具型 MCP Server：通过 JSON-RPC POST 完成 initialize、initialized
通知、tools/list 和 tools/call。若服务返回 `Mcp-Session-Id`，后续请求会带上
该 session header。
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from .base import ConnectorResponse, HealthResult
from ..domain import DownstreamServer, ServerStatus


class StreamableHttpConnector:
    def __init__(self, server: DownstreamServer, secrets: dict[str, str] | None = None) -> None:
        self.server = server
        self.secrets = secrets or {}
        self._client = httpx.AsyncClient(timeout=server.timeout_ms / 1000)
        self._session_id: str | None = None
        self._request_id = 0
        self._initialized = False

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        auth = self.server.auth
        if auth.type == "bearer" and auth.token_ref:
            token = self.secrets.get(auth.token_ref)
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth.type == "api_key" and auth.api_key_ref:
            value = self.secrets.get(auth.api_key_ref)
            if value:
                headers[auth.header_name or "X-API-Key"] = value
        return headers

    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.server.endpoint:
            raise RuntimeError(f"server {self.server.id} missing endpoint")
        self._request_id += 1
        payload = {"jsonrpc": "2.0", "id": self._request_id, "method": method}
        if params is not None:
            payload["params"] = params
        response = await self._client.post(self.server.endpoint, json=payload, headers=self._headers())
        response.raise_for_status()
        session_id = response.headers.get("mcp-session-id")
        if session_id:
            self._session_id = session_id
        data = response.json()
        if "error" in data:
            raise RuntimeError(data["error"].get("message") or data["error"])
        return data.get("result") or {}

    async def _send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        if not self.server.endpoint:
            raise RuntimeError(f"server {self.server.id} missing endpoint")
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        response = await self._client.post(self.server.endpoint, json=payload, headers=self._headers())
        response.raise_for_status()
        session_id = response.headers.get("mcp-session-id")
        if session_id:
            self._session_id = session_id

    async def initialize(self) -> None:
        if self._initialized:
            return
        await self._send_request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "xiaozhi-mcp-hub", "version": "0.1.0"}})
        await self._send_notification("notifications/initialized")
        self._initialized = True

    async def list_tools(self) -> list[dict[str, Any]]:
        await self.initialize()
        result = await self._send_request("tools/list", {"cursor": ""})
        return list(result.get("tools") or [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ConnectorResponse:
        await self.initialize()
        result = await self._send_request("tools/call", {"name": name, "arguments": arguments})
        return ConnectorResponse(
            content=list(result.get("content") or []),
            structured_content=result.get("structuredContent") or result.get("structured_content"),
            is_error=bool(result.get("isError", False)),
            raw=result,
        )

    async def health(self) -> HealthResult:
        start = time.monotonic()
        try:
            await self.initialize()
            latency = (time.monotonic() - start) * 1000
            return HealthResult(status=ServerStatus.HEALTHY, latency_ms=latency)
        except Exception as exc:
            return HealthResult(status=ServerStatus.DOWN, error=str(exc))

    async def close(self) -> None:
        await self._client.aclose()
        self._initialized = False
