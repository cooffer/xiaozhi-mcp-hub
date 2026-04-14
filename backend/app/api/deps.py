"""API 依赖和服务容器。

这里集中创建 store、连接器、ACL、审批、审计和 MCP Hub，所有 router 通过
依赖函数访问同一份运行态。这样 `main.py` 可以保持很薄，测试也仍然可以从
`app.main` 引用 `store` 清理内存状态。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from ..acl import AccessControlService
from ..approvals import ApprovalService
from ..audit import AuditService
from ..connector_manager import ConnectorManager
from ..domain import User, UserRole
from ..mcp_hub import McpHub
from ..schemas import LoginResponse, public_dict
from ..security import create_token, decode_token
from ..settings import settings
from ..store import InMemoryStore
from ..services.upstreams import UpstreamBridgeManager


def _build_store() -> InMemoryStore:
    if settings.store_backend == "memory":
        return InMemoryStore()
    from ..postgres_store import PostgresStore

    return PostgresStore(settings.database_url)


store = _build_store()
connectors = ConnectorManager(store)
acl_service = AccessControlService(store)
approval_service = ApprovalService(store)
audit_service = AuditService(store)
hub = McpHub(store, connectors, acl_service, approval_service, audit_service)
bridge_manager = UpstreamBridgeManager(store, hub)


async def current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    """从 Bearer token 解析当前后台用户。"""

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token, settings.jwt_secret)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
    user = await store.get_user(str(payload.get("sub")))
    if user is None or not user.active:
        raise HTTPException(status_code=401, detail="invalid user")
    return user


async def require_operator(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role not in {UserRole.ADMIN, UserRole.OPERATOR}:
        raise HTTPException(status_code=403, detail="operator role required")
    return user


async def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="admin role required")
    return user


def login_response(user: User) -> LoginResponse:
    """生成登录响应，并确保 password_hash 不进入 API 响应。"""

    token = create_token({"sub": user.id, "role": user.role.value, "tenant_id": user.tenant_id}, settings.jwt_secret)
    user_data = public_dict(user)
    user_data.pop("password_hash", None)
    return LoginResponse(access_token=token, user=user_data)

