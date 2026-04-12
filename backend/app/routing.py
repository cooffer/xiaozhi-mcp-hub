from __future__ import annotations

from dataclasses import dataclass, field

from .domain import DownstreamServer, ServerStatus, ToolRecord


@dataclass(slots=True)
class RoutePolicy:
    mode: str = "exact"
    prefer_local: bool = False
    prefer_low_latency: bool = False
    tenant_only: bool = True
    healthy_only: bool = True
    tags: list[str] = field(default_factory=list)


class RouteNotFound(Exception):
    pass


class Router:
    def route(
        self,
        tool: ToolRecord,
        servers: list[DownstreamServer],
        policy: RoutePolicy | None = None,
    ) -> DownstreamServer:
        policy = policy or RoutePolicy()
        candidates = [server for server in servers if server.id == tool.server_id and server.enabled]
        if policy.tenant_only:
            candidates = [server for server in candidates if server.tenant_id == tool.tenant_id]
        if policy.healthy_only:
            candidates = [server for server in candidates if server.status in {ServerStatus.HEALTHY, ServerStatus.UNKNOWN}]
        if policy.tags:
            candidates = [server for server in candidates if set(policy.tags).issubset(set(server.tags))]
        if not candidates:
            raise RouteNotFound(f"no route for tool {tool.tool_id}")
        if policy.prefer_local:
            candidates.sort(key=lambda server: 0 if server.transport.value == "stdio" else 1)
        if policy.prefer_low_latency:
            candidates.sort(key=lambda server: server.latency_ms if server.latency_ms is not None else float("inf"))
        return candidates[0]

