from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any
from uuid import uuid4

from .domain import ApprovalRequest, ApprovalStatus, RiskLevel, ToolCallContext, ToolRecord, utcnow
from .store import InMemoryStore


class ApprovalRequired(Exception):
    def __init__(self, approval: ApprovalRequest) -> None:
        self.approval = approval
        super().__init__(approval.id)


class ApprovalRejected(Exception):
    pass


class ApprovalService:
    def __init__(self, store: InMemoryStore, wait_seconds: int = 90) -> None:
        self.store = store
        self.wait_seconds = wait_seconds
        self._waiters: dict[str, asyncio.Future[ApprovalRequest]] = {}

    def requires_approval(self, tool: ToolRecord) -> bool:
        return tool.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}

    async def request_and_wait(
        self,
        tool: ToolRecord,
        arguments: dict[str, Any],
        context: ToolCallContext,
    ) -> ApprovalRequest:
        approval = ApprovalRequest(
            id=uuid4().hex,
            tool_id=tool.tool_id,
            arguments=arguments,
            tenant_id=context.tenant_id,
            trace_id=context.trace_id,
            requested_by=context.actor_id,
            expires_at=utcnow() + timedelta(seconds=self.wait_seconds),
        )
        await self.store.create_approval(approval)
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ApprovalRequest] = loop.create_future()
        self._waiters[approval.id] = future
        try:
            return await asyncio.wait_for(future, timeout=self.wait_seconds)
        except asyncio.TimeoutError as exc:
            approval.status = ApprovalStatus.EXPIRED
            approval.decided_at = utcnow()
            await self.store.update_approval(approval)
            raise ApprovalRequired(approval) from exc
        finally:
            self._waiters.pop(approval.id, None)

    async def approve(self, approval_id: str, actor_id: str | None = None) -> ApprovalRequest:
        approval = await self.store.get_approval(approval_id)
        if approval is None:
            raise KeyError("approval not found")
        if approval.status != ApprovalStatus.PENDING:
            return approval
        approval.status = ApprovalStatus.APPROVED
        approval.decided_by = actor_id
        approval.decided_at = utcnow()
        await self.store.update_approval(approval)
        waiter = self._waiters.get(approval_id)
        if waiter and not waiter.done():
            waiter.set_result(approval)
        return approval

    async def reject(self, approval_id: str, actor_id: str | None = None, reason: str | None = None) -> ApprovalRequest:
        approval = await self.store.get_approval(approval_id)
        if approval is None:
            raise KeyError("approval not found")
        if approval.status != ApprovalStatus.PENDING:
            return approval
        approval.status = ApprovalStatus.REJECTED
        approval.decided_by = actor_id
        approval.reason = reason
        approval.decided_at = utcnow()
        await self.store.update_approval(approval)
        waiter = self._waiters.get(approval_id)
        if waiter and not waiter.done():
            waiter.set_result(approval)
        return approval

    async def assert_approved_or_raise(
        self,
        tool: ToolRecord,
        arguments: dict[str, Any],
        context: ToolCallContext,
    ) -> None:
        if not self.requires_approval(tool):
            return
        approval = await self.request_and_wait(tool, arguments, context)
        if approval.status != ApprovalStatus.APPROVED:
            raise ApprovalRejected(approval.reason or approval.status.value)

