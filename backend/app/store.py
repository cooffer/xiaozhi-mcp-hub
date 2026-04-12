from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import timedelta
from typing import Any
from uuid import uuid4

from .domain import (
    ApprovalRequest,
    AuditLog,
    ConfigVersion,
    DownstreamServer,
    ToolAcl,
    ToolRecord,
    UpstreamEndpoint,
    User,
    UserRole,
    utcnow,
)
from .security import hash_password


class InMemoryStore:
    """Async repository used by the API and tests.

    The shape mirrors the Postgres entities so replacing this with an async SQL
    repository does not change the service layer.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.upstreams: dict[str, UpstreamEndpoint] = {}
        self.servers: dict[str, DownstreamServer] = {}
        self.tools: dict[str, ToolRecord] = {}
        self.users: dict[str, User] = {}
        self.acl: dict[str, ToolAcl] = {}
        self.approvals: dict[str, ApprovalRequest] = {}
        self.audit_logs: list[AuditLog] = []
        self.config_versions: list[ConfigVersion] = []
        self.secrets: dict[str, str] = {}

    async def seed_admin(self, email: str, password: str) -> None:
        async with self._lock:
            if any(user.email.lower() == email.lower() for user in self.users.values()):
                return
            user = User(
                id=uuid4().hex,
                email=email.lower(),
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
            )
            self.users[user.id] = user

    async def has_admin_user(self) -> bool:
        async with self._lock:
            return any(user.role == UserRole.ADMIN and user.active for user in self.users.values())

    async def create_user(self, email: str, password: str, role: UserRole = UserRole.VIEWER, tenant_id: str = "default") -> User:
        normalized_email = email.strip().lower()
        async with self._lock:
            if any(user.email.lower() == normalized_email for user in self.users.values()):
                raise ValueError("email already exists")
            user = User(
                id=uuid4().hex,
                email=normalized_email,
                password_hash=hash_password(password),
                role=role,
                tenant_id=tenant_id,
            )
            self.users[user.id] = user
            return user

    async def create_first_admin(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        async with self._lock:
            if any(user.role == UserRole.ADMIN and user.active for user in self.users.values()):
                raise PermissionError("admin already exists")
            if any(user.email.lower() == normalized_email for user in self.users.values()):
                raise ValueError("email already exists")
            user = User(
                id=uuid4().hex,
                email=normalized_email,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
            )
            self.users[user.id] = user
            return user

    async def get_user_by_email(self, email: str) -> User | None:
        async with self._lock:
            return next((user for user in self.users.values() if user.email.lower() == email.lower()), None)

    async def get_user(self, user_id: str) -> User | None:
        async with self._lock:
            return self.users.get(user_id)

    async def upsert_upstream(self, upstream: UpstreamEndpoint) -> UpstreamEndpoint:
        async with self._lock:
            upstream.updated_at = utcnow()
            self.upstreams[upstream.id] = upstream
            return upstream

    async def list_upstreams(self) -> list[UpstreamEndpoint]:
        async with self._lock:
            return sorted(self.upstreams.values(), key=lambda item: item.id)

    async def upsert_server(self, server: DownstreamServer) -> DownstreamServer:
        async with self._lock:
            server.updated_at = utcnow()
            self.servers[server.id] = server
            return server

    async def get_server(self, server_id: str) -> DownstreamServer | None:
        async with self._lock:
            return self.servers.get(server_id)

    async def list_servers(self) -> list[DownstreamServer]:
        async with self._lock:
            return sorted(self.servers.values(), key=lambda item: item.id)

    async def replace_tools_for_server(self, server_id: str, tools: list[ToolRecord]) -> None:
        async with self._lock:
            for tool_id in [tid for tid, tool in self.tools.items() if tool.server_id == server_id]:
                del self.tools[tool_id]
            for tool in tools:
                tool.updated_at = utcnow()
                self.tools[tool.tool_id] = tool

    async def upsert_tool(self, tool: ToolRecord) -> ToolRecord:
        async with self._lock:
            tool.updated_at = utcnow()
            self.tools[tool.tool_id] = tool
            return tool

    async def get_tool(self, tool_id: str) -> ToolRecord | None:
        async with self._lock:
            return self.tools.get(tool_id)

    async def list_tools(self, tenant_id: str | None = None, enabled: bool | None = None) -> list[ToolRecord]:
        async with self._lock:
            tools = list(self.tools.values())
            if tenant_id is not None:
                tools = [tool for tool in tools if tool.tenant_id == tenant_id]
            if enabled is not None:
                tools = [tool for tool in tools if tool.enabled is enabled]
            return sorted(tools, key=lambda item: item.tool_id)

    async def upsert_acl(self, acl: ToolAcl) -> ToolAcl:
        async with self._lock:
            self.acl[acl.id] = acl
            return acl

    async def list_acl_for_tool(self, tool_id: str) -> list[ToolAcl]:
        async with self._lock:
            return [item for item in self.acl.values() if item.tool_id == tool_id and item.enabled]

    async def create_approval(self, approval: ApprovalRequest) -> ApprovalRequest:
        async with self._lock:
            if approval.expires_at is None:
                approval.expires_at = utcnow() + timedelta(seconds=90)
            self.approvals[approval.id] = approval
            return approval

    async def get_approval(self, approval_id: str) -> ApprovalRequest | None:
        async with self._lock:
            return self.approvals.get(approval_id)

    async def update_approval(self, approval: ApprovalRequest) -> ApprovalRequest:
        async with self._lock:
            self.approvals[approval.id] = approval
            return approval

    async def list_approvals(self, status: str | None = None) -> list[ApprovalRequest]:
        async with self._lock:
            items = list(self.approvals.values())
            if status:
                items = [item for item in items if item.status.value == status]
            return sorted(items, key=lambda item: item.created_at, reverse=True)

    async def add_audit(self, audit: AuditLog) -> None:
        async with self._lock:
            self.audit_logs.append(audit)
            self.audit_logs = self.audit_logs[-10_000:]

    async def list_audit(self, limit: int = 100) -> list[AuditLog]:
        async with self._lock:
            return list(reversed(self.audit_logs[-limit:]))

    async def add_config_version(self, payload: dict[str, Any], created_by: str | None = None) -> ConfigVersion:
        async with self._lock:
            version = ConfigVersion(
                id=uuid4().hex,
                version=len(self.config_versions) + 1,
                payload=payload,
                created_by=created_by,
            )
            self.config_versions.append(version)
            return version

    async def list_config_versions(self) -> list[ConfigVersion]:
        async with self._lock:
            return list(reversed(self.config_versions))

    async def export_config(self) -> dict[str, Any]:
        async with self._lock:
            return {
                "upstreams": [asdict(item) for item in self.upstreams.values()],
                "servers": [asdict(item) for item in self.servers.values()],
            }
