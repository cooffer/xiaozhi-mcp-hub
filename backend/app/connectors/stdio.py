"""stdio 下游 MCP connector。

stdio MCP Server 通过 stdin/stdout 传输 JSON-RPC，每条消息一行。协议要求
stdout 只能写 JSON-RPC，日志必须走 stderr。连接器在首次使用时启动子进程，
执行 `initialize -> notifications/initialized`，之后复用同一进程执行
`tools/list` 和 `tools/call`。
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from typing import Any

from .base import ConnectorResponse, HealthResult
from ..domain import DownstreamServer, ServerStatus


class StdioConnector:
    def __init__(self, server: DownstreamServer) -> None:
        self.server = server
        self._process: asyncio.subprocess.Process | subprocess.Popen[bytes] | None = None
        self._request_id = 0
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """启动进程并完成 MCP 初始化握手。"""

        if self._is_running() and self._initialized:
            return
        if not self.server.command:
            raise RuntimeError(f"server {self.server.id} missing command")
        if not self._is_running():
            self._initialized = False
            await self._spawn_process()
        await self._send_request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "xiaozhi-mcp-hub", "version": "0.1.0"}})
        await self._send_notification("notifications/initialized")
        self._initialized = True

    def _is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def _spawn_process(self) -> None:
        env = {**os.environ, **self.server.env} if self.server.env else None
        try:
            self._process = await asyncio.create_subprocess_exec(
                self.server.command,
                *self.server.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except (NotImplementedError, PermissionError):
            # Windows 上部分 ASGI 事件循环不支持 asyncio subprocess transport。
            # 某些本地沙箱还会拒绝 overlapped pipe 句柄，所以降级到 Popen。
            # 管道读写放到 worker thread，避免阻塞 FastAPI 主事件循环。
            self._process = subprocess.Popen(
                [self.server.command, *self.server.args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=env,
            )

    async def _send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        await self._write_line((json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8"))

    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        await self.initialize() if self._process is None else None
        if self._process is None:
            raise RuntimeError("stdio process is not available")
        async with self._lock:
            self._request_id += 1
            request_id = self._request_id
            payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
            if params is not None:
                payload["params"] = params
            await self._write_line((json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8"))
            timeout = self.server.timeout_ms / 1000
            while True:
                line = await self._read_line(timeout)
                if not line:
                    raise RuntimeError("stdio server closed stdout")
                response = json.loads(line.decode("utf-8"))
                if response.get("id") != request_id:
                    continue
                if "error" in response:
                    raise RuntimeError(response["error"].get("message") or response["error"])
                return response.get("result") or {}

    async def _write_line(self, data: bytes) -> None:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("stdio process is not available")
        if isinstance(self._process, asyncio.subprocess.Process):
            self._process.stdin.write(data)
            await self._process.stdin.drain()
            return

        def write_blocking() -> None:
            assert self._process is not None and self._process.stdin is not None
            self._process.stdin.write(data)
            self._process.stdin.flush()

        await asyncio.to_thread(write_blocking)

    async def _read_line(self, timeout: float) -> bytes:
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("stdio process is not available")
        if isinstance(self._process, asyncio.subprocess.Process):
            return await asyncio.wait_for(self._process.stdout.readline(), timeout=timeout)
        return await asyncio.wait_for(asyncio.to_thread(self._process.stdout.readline), timeout=timeout)

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
        process = self._process
        if process and process.returncode is None:
            process.terminate()
            try:
                if isinstance(process, asyncio.subprocess.Process):
                    await asyncio.wait_for(process.wait(), timeout=5)
                else:
                    await asyncio.to_thread(process.wait, 5)
            except (asyncio.TimeoutError, subprocess.TimeoutExpired):
                process.kill()
        self._process = None
        self._initialized = False
