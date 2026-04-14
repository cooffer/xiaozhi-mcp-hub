"""下游 MCP 连接器管理。

ConnectorManager 维护 server 配置和运行中 connector 的映射，负责工具发现、
健康检查和调用失败后的降级/熔断状态。具体传输协议细节留给 stdio/http/sse
connector，自身只关心统一接口。
"""

from __future__ import annotations

import time
from typing import Any

from .connectors.base import BaseConnector, ConnectorResponse
from .connectors.http import StreamableHttpConnector
from .connectors.sse import LegacySseConnector
from .connectors.stdio import StdioConnector
from .domain import DownstreamServer, ServerStatus, TransportType
from .registry import build_tool_records, reconcile_conflicts
from .store import InMemoryStore


class ConnectorManager:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store
        self._connectors: dict[str, BaseConnector] = {}

    def _build_connector(self, server: DownstreamServer) -> BaseConnector:
        if server.transport == TransportType.STDIO:
            return StdioConnector(server)
        if server.transport == TransportType.SSE:
            return LegacySseConnector(server, self.store.secrets)
        return StreamableHttpConnector(server, self.store.secrets)

    async def reload_server(self, server: DownstreamServer) -> None:
        old = self._connectors.pop(server.id, None)
        if old:
            await old.close()
        if server.enabled:
            self._connectors[server.id] = self._build_connector(server)

    async def reload_all(self) -> None:
        for connector in list(self._connectors.values()):
            await connector.close()
        self._connectors.clear()
        for server in await self.store.list_servers():
            if server.enabled:
                self._connectors[server.id] = self._build_connector(server)

    async def discover_server(self, server: DownstreamServer) -> list[dict[str, Any]]:
        """发现某个下游服务的工具并刷新注册中心。"""

        connector = self._connectors.get(server.id)
        if connector is None:
            connector = self._build_connector(server)
            self._connectors[server.id] = connector
        start = time.monotonic()
        try:
            raw_tools = await connector.list_tools()
        except Exception:
            server.status = ServerStatus.DOWN
            server.failure_count += 1
            await self.store.upsert_server(server)
            raise
        server.status = ServerStatus.HEALTHY
        server.latency_ms = (time.monotonic() - start) * 1000
        server.failure_count = 0
        await self.store.upsert_server(server)
        existing = await self.store.list_tools(tenant_id=server.tenant_id)
        records = reconcile_conflicts(existing, build_tool_records(server, raw_tools))
        await self.store.replace_tools_for_server(server.id, records)
        return raw_tools

    async def discover_all(self) -> dict[str, str]:
        results: dict[str, str] = {}
        for server in await self.store.list_servers():
            if not server.enabled:
                continue
            try:
                await self.discover_server(server)
                results[server.id] = "ok"
            except Exception as exc:
                server.status = ServerStatus.DOWN
                server.failure_count += 1
                await self.store.upsert_server(server)
                results[server.id] = str(exc)
        return results

    async def health_all(self) -> dict[str, str]:
        results: dict[str, str] = {}
        for server in await self.store.list_servers():
            connector = self._connectors.get(server.id)
            if connector is None and server.enabled:
                connector = self._build_connector(server)
                self._connectors[server.id] = connector
            if connector is None:
                results[server.id] = "disabled"
                continue
            health = await connector.health()
            server.status = health.status
            server.latency_ms = health.latency_ms
            await self.store.upsert_server(server)
            results[server.id] = health.status.value
        return results

    async def call_tool(self, server: DownstreamServer, origin_tool_name: str, arguments: dict[str, Any]) -> ConnectorResponse:
        """调用原始下游工具名。

        上游看到的是统一 tool_id，下游 connector 只接收 origin_tool_name。
        这里是防止“统一命名规则”泄漏到下游协议层的边界。
        """

        connector = self._connectors.get(server.id)
        if connector is None:
            connector = self._build_connector(server)
            self._connectors[server.id] = connector
        try:
            return await connector.call_tool(origin_tool_name, arguments)
        except Exception:
            server.failure_count += 1
            if server.failure_count >= 3:
                server.status = ServerStatus.CIRCUIT_OPEN
            else:
                server.status = ServerStatus.DEGRADED
            await self.store.upsert_server(server)
            raise
