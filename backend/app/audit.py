from __future__ import annotations

from typing import Any
from uuid import uuid4

from .domain import AuditLog, ToolCallContext
from .store import InMemoryStore


class AuditService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    async def record(
        self,
        context: ToolCallContext,
        action: str,
        status: str = "ok",
        tool_id: str | None = None,
        server_id: str | None = None,
        latency_ms: float | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.store.add_audit(
            AuditLog(
                id=uuid4().hex,
                trace_id=context.trace_id,
                action=action,
                tenant_id=context.tenant_id,
                actor_id=context.actor_id,
                tool_id=tool_id,
                server_id=server_id,
                status=status,
                latency_ms=latency_ms,
                error=error,
                metadata=metadata or {},
            )
        )
