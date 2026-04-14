from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ...domain import User
from ...schemas import public_dict
from ..deps import current_user, store

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
async def list_audit_logs(
    _: Annotated[User, Depends(current_user)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """返回最近的审计日志。

    前端审计页使用 `/api/v1/audit-logs?limit=50` 拉取紧凑列表；这里复用
    Store 的 `list_audit`，不改变数据库 schema，也不暴露任何下游凭据。
    """

    return [public_dict(item) for item in await store.list_audit(limit=limit)]
