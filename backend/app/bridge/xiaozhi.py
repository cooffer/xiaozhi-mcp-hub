from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import websockets

from ..domain import ToolCallContext, UpstreamEndpoint
from ..mcp_hub import McpHub

logger = logging.getLogger(__name__)


class XiaozhiOfficialBridge:
    """WebSocket client bridge compatible with mcp-calculator style endpoints."""

    def __init__(self, upstream: UpstreamEndpoint, hub: McpHub) -> None:
        self.upstream = upstream
        self.hub = hub
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._run(), name=f"xiaozhi-bridge:{self.upstream.id}")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        backoff = 1
        while not self._stop.is_set() and self.upstream.enabled:
            try:
                async with websockets.connect(self.upstream.endpoint) as websocket:
                    logger.info("connected to xiaozhi upstream %s", self.upstream.id)
                    backoff = 1
                    await self._serve(websocket)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("xiaozhi upstream %s disconnected: %s", self.upstream.id, exc)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def _serve(self, websocket: Any) -> None:
        async for frame in websocket:
            if isinstance(frame, bytes):
                frame = frame.decode("utf-8")
            inbound = json.loads(frame)
            request = self._unwrap(inbound)
            context = ToolCallContext(tenant_id=self.upstream.tenant_id, upstream_id=self.upstream.id)
            response = await self.hub.handle(request, context)
            if response is not None:
                await websocket.send(json.dumps(self._wrap(response), separators=(",", ":")))

    def _unwrap(self, inbound: Any) -> Any:
        if self.upstream.envelope_mode == "xiaozhi_json" and isinstance(inbound, dict) and inbound.get("type") == "mcp":
            return inbound.get("payload") or {}
        return inbound

    def _wrap(self, payload: Any) -> Any:
        if self.upstream.envelope_mode == "xiaozhi_json":
            return {"type": "mcp", "payload": payload}
        return payload
