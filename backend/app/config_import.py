"""配置导入兼容层。

支持项目原生 `servers:` 格式，也兼容常见 MCP 客户端使用的 `mcpServers`
对象格式。导入完成后会尝试自动发现启用服务的工具；单个服务失败不会中断
整个导入，而是写入 errors 返回给 WebUI。
"""

from __future__ import annotations

import json
import os
import hashlib
from typing import Any

import yaml

from .connector_manager import ConnectorManager
from .domain import AuthConfig, DownstreamServer, TransportType, UpstreamEndpoint
from .store import InMemoryStore


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    safe_prefix = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in prefix.lower()).strip("-_") or "item"
    return f"{safe_prefix}-{digest}"


def expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    return value


def load_payload(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    if text.startswith("{"):
        return json.loads(text)
    return yaml.safe_load(text) or {}


def _normalize_transport(value: Any) -> str:
    transport = str(value or "stdio").lower().replace("-", "_")
    if transport in {"http", "streamablehttp", "streamable-http"}:
        return "streamable_http"
    if transport in {"sse", "legacy_sse", "legacy-sse"}:
        return "sse"
    return transport


def _normalize_channel(value: Any) -> str:
    channel = str(value or "xiaozhi_official").strip().lower().replace("-", "_").replace(" ", "_")
    if channel in {"xiaozhi", "xiaozhi_official", "小智", "小智官方"}:
        return "xiaozhi_official"
    return channel or "xiaozhi_official"


def _native_servers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in payload.get("servers") or []]


def _mcp_servers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    servers = payload.get("mcpServers") or payload.get("mcp_servers") or {}
    if not isinstance(servers, dict):
        return []
    normalized: list[dict[str, Any]] = []
    for server_id, item in servers.items():
        if not isinstance(item, dict):
            continue
        transport = _normalize_transport(item.get("transport") or item.get("type") or ("streamable_http" if item.get("url") else "stdio"))
        normalized.append(
            {
                "id": str(item.get("id") or server_id),
                "transport": transport,
                "endpoint": item.get("endpoint") or item.get("url"),
                "command": item.get("command"),
                "args": item.get("args") or [],
                "env": item.get("env") or {},
                "namespace": item.get("namespace") or server_id,
                "tenant_id": item.get("tenant_id") or "default",
                "enabled": item.get("enabled", True),
                "timeout_ms": item.get("timeout_ms") or item.get("timeout") or 30_000,
                "tags": item.get("tags") or [],
                "auth": item.get("auth") or {},
            }
        )
    return normalized


async def import_config(payload: dict[str, Any], store: InMemoryStore, connectors: ConnectorManager, created_by: str | None = None) -> dict[str, Any]:
    """导入配置并尽力发现工具。

    这里故意不让某个 server 的发现失败回滚其他 server，因为批量导入时常见
    情况是本地 stdio、远程 HTTP 混合，其中部分服务暂时不可用也应该保留配置。
    """

    payload = expand_env(payload)
    upstream_count = 0
    server_count = 0
    tool_count = 0
    errors: dict[str, str] = {}
    imported_servers: list[DownstreamServer] = []

    for item in payload.get("upstreams") or []:
        channel = _normalize_channel(item.get("channel") or item.get("type") or "xiaozhi_official")
        endpoint = str(item["endpoint"])
        upstream = UpstreamEndpoint(
            id=str(item.get("id") or _stable_id(channel, endpoint)),
            type=channel,
            endpoint=endpoint,
            tenant_id=str(item.get("tenant_id") or "default"),
            enabled=bool(item.get("enabled", True)),
            envelope_mode=str(item.get("envelope_mode") or "raw"),
        )
        await store.upsert_upstream(upstream)
        upstream_count += 1

    for item in [*_native_servers(payload), *_mcp_servers(payload)]:
        auth_payload = item.get("auth") or {}
        auth = AuthConfig(
            type=str(auth_payload.get("type") or "none"),
            token_ref=auth_payload.get("token_ref"),
            api_key_ref=auth_payload.get("api_key_ref"),
            username_ref=auth_payload.get("username_ref"),
            password_ref=auth_payload.get("password_ref"),
            header_name=auth_payload.get("header_name"),
        )
        transport = _normalize_transport(item.get("transport") or item.get("type") or "stdio")
        server = DownstreamServer(
            id=str(item["id"]),
            transport=TransportType(transport),
            endpoint=item.get("endpoint") or item.get("url"),
            command=item.get("command"),
            args=[str(arg) for arg in item.get("args") or []],
            env={str(k): str(v) for k, v in (item.get("env") or {}).items()},
            namespace=str(item.get("namespace") or item["id"]),
            tenant_id=str(item.get("tenant_id") or "default"),
            enabled=bool(item.get("enabled", True)),
            timeout_ms=int(item.get("timeout_ms") or 30_000),
            tags=[str(tag) for tag in item.get("tags") or []],
            auth=auth,
        )
        await store.upsert_server(server)
        await connectors.reload_server(server)
        imported_servers.append(server)
        server_count += 1

    for server in imported_servers:
        if not server.enabled:
            continue
        try:
            discovered = await connectors.discover_server(server)
            tool_count += len(discovered)
        except Exception as exc:
            errors[server.id] = str(exc)

    version = await store.add_config_version(payload, created_by=created_by)
    return {"upstreams": upstream_count, "servers": server_count, "tools": tool_count, "errors": errors, "version": version.version}
