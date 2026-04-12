from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..domain import DownstreamServer, ServerStatus


@dataclass(slots=True)
class ConnectorResponse:
    content: list[dict[str, Any]] = field(default_factory=list)
    structured_content: dict[str, Any] | None = None
    is_error: bool = False
    raw: dict[str, Any] | None = None

    def to_mcp_result(self) -> dict[str, Any]:
        result: dict[str, Any] = {"content": self.content, "isError": self.is_error}
        if self.structured_content is not None:
            result["structuredContent"] = self.structured_content
        return result


@dataclass(slots=True)
class HealthResult:
    status: ServerStatus
    latency_ms: float | None = None
    error: str | None = None


class BaseConnector(Protocol):
    server: DownstreamServer

    async def initialize(self) -> None:
        ...

    async def list_tools(self) -> list[dict[str, Any]]:
        ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ConnectorResponse:
        ...

    async def health(self) -> HealthResult:
        ...

    async def close(self) -> None:
        ...

