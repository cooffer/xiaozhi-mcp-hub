from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ...domain import User
from ..deps import current_user, store

router = APIRouter(tags=["metrics"])
raw_metrics_router = APIRouter(tags=["metrics"])


@router.get("/health")
async def health():
    return {"status": "ok"}


async def build_metrics_summary() -> dict[str, int]:
    servers = await store.list_servers()
    tools = await store.list_tools()
    approvals = await store.list_approvals(status="pending")
    return {
        "servers": len(servers),
        "tools": len(tools),
        "pending_approvals": len(approvals),
        "healthy_servers": len([server for server in servers if server.status.value == "healthy"]),
    }


@router.get("/metrics/summary")
async def metrics_summary(_: Annotated[User, Depends(current_user)]):
    return await build_metrics_summary()


@router.get("/dashboard/summary")
async def dashboard_summary(_: Annotated[User, Depends(current_user)]):
    return await build_metrics_summary()


@raw_metrics_router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

