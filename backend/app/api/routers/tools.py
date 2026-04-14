from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from ...domain import RiskLevel, ToolAcl, User, UserRole
from ...schemas import public_dict
from ..deps import current_user, require_admin, require_operator, store

router = APIRouter(tags=["tools"])


@router.get("/tools")
async def list_tools(_: Annotated[User, Depends(current_user)]):
    return [public_dict(item) for item in await store.list_tools()]


@router.patch("/tools/{tool_id}")
async def update_tool(tool_id: str, payload: dict[str, Any], _: Annotated[User, Depends(require_operator)]):
    tool = await store.get_tool(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="tool not found")
    for field in ["display_name", "description", "enabled", "risk_level", "device_scope", "tags"]:
        if field in payload:
            value = payload[field]
            if field == "risk_level":
                value = RiskLevel(value)
            setattr(tool, field, value)
    await store.upsert_tool(tool)
    return public_dict(tool)


@router.get("/routes")
async def routes(_: Annotated[User, Depends(current_user)]):
    tools = await store.list_tools()
    servers = {server.id: server for server in await store.list_servers()}
    return [
        {
            "tool_id": tool.tool_id,
            "server_id": tool.server_id,
            "origin_tool_name": tool.origin_tool_name,
            "server_status": servers.get(tool.server_id).status.value if servers.get(tool.server_id) else "missing",
        }
        for tool in tools
    ]


@router.get("/acl")
async def list_acl(_: Annotated[User, Depends(current_user)]):
    if hasattr(store, "list_acl"):
        return [public_dict(item) for item in await store.list_acl()]
    return [public_dict(item) for item in store.acl.values()]


@router.post("/acl")
async def upsert_acl(payload: dict[str, Any], _: Annotated[User, Depends(require_admin)]):
    acl = ToolAcl(
        id=str(payload.get("id") or f"acl-{payload['tool_id']}"),
        tool_id=str(payload["tool_id"]),
        tenant_id=str(payload.get("tenant_id") or "default"),
        roles=[UserRole(role) for role in payload.get("roles", ["admin", "operator"])],
        upstream_ids=[str(item) for item in payload.get("upstream_ids", [])],
        device_scope=[str(item) for item in payload.get("device_scope", [])],
        enabled=bool(payload.get("enabled", True)),
    )
    await store.upsert_acl(acl)
    return public_dict(acl)

