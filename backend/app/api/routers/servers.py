from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...domain import AuthConfig, DownstreamServer, TransportType, User
from ...schemas import ServerIn, public_dict
from ..deps import connectors, current_user, require_admin, require_operator, store

router = APIRouter(prefix="/servers", tags=["servers"])


def _normalize_transport(value: str) -> str:
    transport = value.lower().replace("-", "_")
    if transport in {"http", "streamablehttp", "streamable_http"}:
        return "streamable_http"
    if transport in {"legacy_sse", "sse"}:
        return "sse"
    return transport


@router.get("")
async def list_servers(_: Annotated[User, Depends(current_user)]):
    return [public_dict(item) for item in await store.list_servers()]


@router.post("")
async def upsert_server(payload: ServerIn, _: Annotated[User, Depends(require_admin)]):
    auth = AuthConfig(**payload.auth) if payload.auth else AuthConfig()
    data = payload.model_dump(exclude={"auth"})
    transport = _normalize_transport(data.pop("transport"))
    server = DownstreamServer(**data, transport=TransportType(transport), auth=auth)
    await store.upsert_server(server)
    await connectors.reload_server(server)
    return public_dict(server)


@router.post("/{server_id}/discover")
async def discover_server(server_id: str, _: Annotated[User, Depends(require_operator)]):
    server = await store.get_server(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="server not found")
    try:
        raw_tools = await connectors.discover_server(server)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"failed to discover server {server_id}: {exc}") from exc
    return {"server_id": server_id, "tools": len(raw_tools)}

