from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from ...domain import User
from ...schemas import ApprovalDecision, public_dict
from ..deps import approval_service, current_user, require_operator, store

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
async def list_approvals(_: Annotated[User, Depends(current_user)], status: str | None = None):
    return [public_dict(item) for item in await store.list_approvals(status=status)]


@router.post("/{approval_id}/approve")
async def approve(approval_id: str, user: Annotated[User, Depends(require_operator)]):
    return public_dict(await approval_service.approve(approval_id, actor_id=user.id))


@router.post("/{approval_id}/reject")
async def reject(approval_id: str, payload: ApprovalDecision, user: Annotated[User, Depends(require_operator)]):
    return public_dict(await approval_service.reject(approval_id, actor_id=user.id, reason=payload.reason))

