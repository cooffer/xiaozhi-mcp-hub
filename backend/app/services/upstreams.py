"""小智上游接入点管理。

上游接入点是 Hub 主动连接小智官方服务的 WebSocket MCP endpoint。
这个模块只处理 endpoint 配置到 bridge 运行态之间的映射：

- 将后台展示的“渠道”归一化为内部 type。
- 为没有显式 id 的 endpoint 生成稳定 id。
- 根据数据库中的启用状态启动、停止或重建 XiaozhiOfficialBridge。

注意：上游 token 或 endpoint 内的敏感参数只用于连接小智官方服务，不能透传
给任何下游 MCP Server，避免 MCP proxy 的 confused deputy 风险。
"""

from __future__ import annotations

import hashlib
from typing import Any

from ..bridge import XiaozhiOfficialBridge
from ..domain import UpstreamEndpoint
from ..mcp_hub import McpHub
from ..schemas import UpstreamIn
from ..store import InMemoryStore


def _stable_upstream_id(channel: str, endpoint: str) -> str:
    """根据渠道和 endpoint 生成稳定 id，避免同一接入点反复保存产生新记录。"""

    digest = hashlib.sha1(endpoint.encode("utf-8")).hexdigest()[:10]
    safe_channel = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in channel.lower()).strip("-_") or "upstream"
    return f"{safe_channel}-{digest}"


def normalize_upstream_channel(value: Any) -> str:
    """把 WebUI/导入配置里的渠道别名统一成内部类型。"""

    channel = str(value or "xiaozhi_official").strip().lower().replace("-", "_").replace(" ", "_")
    if channel in {"xiaozhi", "xiaozhi_official", "小智", "小智官方"}:
        return "xiaozhi_official"
    return channel or "xiaozhi_official"


def build_upstream(payload: UpstreamIn) -> UpstreamEndpoint:
    """把 API 输入转换为数据库领域对象。

    第一版后台不展示租户，所以这里固定使用 default tenant。后续如果小智官方
    payload 提供设备或租户上下文，再从 adapter 层映射到 tenant/device scope。
    """

    data = payload.model_dump()
    channel = normalize_upstream_channel(data.pop("channel") or data.get("type") or "xiaozhi_official")
    endpoint = str(data["endpoint"])
    upstream_id = str(data.pop("id") or _stable_upstream_id(channel, endpoint))
    data["type"] = channel
    data["tenant_id"] = "default"
    return UpstreamEndpoint(id=upstream_id, **data)


class UpstreamBridgeManager:
    """维护数据库配置和运行中 bridge 之间的一致性。"""

    def __init__(self, store: InMemoryStore, hub: McpHub) -> None:
        self.store = store
        self.hub = hub
        self.bridges: dict[str, XiaozhiOfficialBridge] = {}

    async def sync(self) -> None:
        """根据当前 upstream 配置增量启动、停止或重建 bridge。"""

        upstreams = {upstream.id: upstream for upstream in await self.store.list_upstreams()}
        for bridge_id in list(self.bridges):
            if bridge_id not in upstreams or not upstreams[bridge_id].enabled:
                await self.bridges[bridge_id].stop()
                del self.bridges[bridge_id]
        for upstream in upstreams.values():
            if not upstream.enabled:
                continue
            existing = self.bridges.get(upstream.id)
            if existing:
                if existing.upstream.endpoint == upstream.endpoint and existing.upstream.type == upstream.type:
                    continue
                await existing.stop()
            bridge = XiaozhiOfficialBridge(upstream, self.hub)
            self.bridges[upstream.id] = bridge
            await bridge.start()

    async def stop_all(self) -> None:
        """应用关闭时停止所有 WebSocket bridge 后台任务。"""

        for bridge in list(self.bridges.values()):
            await bridge.stop()
        self.bridges.clear()

