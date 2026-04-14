from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from ...domain import User
from ...schemas import UpstreamIn, public_dict
from ...services.upstreams import build_upstream
from ..deps import bridge_manager, current_user, require_admin, store

router = APIRouter(prefix="/upstreams", tags=["upstreams"])


@router.get("")
async def list_upstreams(_: Annotated[User, Depends(current_user)]):
    items = []
    for upstream in await store.list_upstreams():
        data = public_dict(upstream)
        data["channel"] = upstream.type
        items.append(data)
    return items


@router.post("")
async def upsert_upstream(payload: UpstreamIn, _: Annotated[User, Depends(require_admin)]):
    upstream = build_upstream(payload)
    await store.upsert_upstream(upstream)
    await bridge_manager.sync()
    data = public_dict(upstream)
    data["channel"] = upstream.type
    return data

