from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response

from ...domain import ToolCallContext, User
from ..deps import hub, require_operator
from ..observability import MCP_CALLS, MCP_LATENCY

router = APIRouter(tags=["mcp"])


@router.post("/mcp")
async def mcp_endpoint(payload: dict[str, Any] | list[dict[str, Any]], user: Annotated[User, Depends(require_operator)]):
    context = ToolCallContext(tenant_id=user.tenant_id, actor_id=user.id, actor_role=user.role)
    with MCP_LATENCY.time():
        response = await hub.handle(payload, context)
    if isinstance(payload, dict):
        MCP_CALLS.labels(method=str(payload.get("method") or "batch"), status="ok").inc()
    else:
        MCP_CALLS.labels(method="batch", status="ok").inc()
    return response or Response(status_code=202)

