from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import asyncpg

from .domain import (
    ApprovalRequest,
    ApprovalStatus,
    AuditLog,
    AuthConfig,
    ConfigVersion,
    DownstreamServer,
    RiskLevel,
    ServerStatus,
    ToolAcl,
    ToolRecord,
    TransportType,
    UpstreamEndpoint,
    User,
    UserRole,
    utcnow,
)
from .security import hash_password


def _dsn(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


def _json(value: Any) -> str:
    def default(item: Any) -> Any:
        if isinstance(item, Enum):
            return item.value
        if isinstance(item, datetime):
            return item.isoformat()
        return str(item)

    return json.dumps(value, default=default)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return json.loads(value)
    return list(value)


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


class PostgresStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None
        self.secrets = dict(os.environ)

    async def connect(self) -> None:
        if self.pool is not None:
            return
        self.pool = await asyncpg.create_pool(_dsn(self.database_url), min_size=1, max_size=10)
        schema = Path(__file__).with_name("storage_schema.sql").read_text(encoding="utf-8")
        async with self.pool.acquire() as conn:
            await conn.execute(schema)
            await conn.execute("INSERT INTO tenants(id, name) VALUES('default', 'Default') ON CONFLICT (id) DO NOTHING")

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    def _pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("PostgresStore is not connected")
        return self.pool

    async def seed_admin(self, email: str, password: str) -> None:
        async with self._pool().acquire() as conn:
            exists = await conn.fetchval("SELECT id FROM users WHERE lower(email)=lower($1)", email)
            if exists:
                return
            await conn.execute(
                "INSERT INTO users(id, email, password_hash, role, tenant_id, active) VALUES($1,$2,$3,$4,$5,true)",
                uuid4().hex,
                email.lower(),
                hash_password(password),
                UserRole.ADMIN.value,
                "default",
            )

    async def has_admin_user(self) -> bool:
        async with self._pool().acquire() as conn:
            return bool(await conn.fetchval("SELECT EXISTS(SELECT 1 FROM users WHERE role=$1 AND active=true)", UserRole.ADMIN.value))

    async def create_user(self, email: str, password: str, role: UserRole = UserRole.VIEWER, tenant_id: str = "default") -> User:
        normalized_email = email.strip().lower()
        async with self._pool().acquire() as conn:
            exists = await conn.fetchval("SELECT id FROM users WHERE lower(email)=lower($1)", normalized_email)
            if exists:
                raise ValueError("email already exists")
            user = User(
                id=uuid4().hex,
                email=normalized_email,
                password_hash=hash_password(password),
                role=role,
                tenant_id=tenant_id,
            )
            await conn.execute(
                "INSERT INTO users(id, email, password_hash, role, tenant_id, active) VALUES($1,$2,$3,$4,$5,true)",
                user.id,
                user.email,
                user.password_hash,
                user.role.value,
                user.tenant_id,
            )
            return user

    async def create_first_admin(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        async with self._pool().acquire() as conn:
            async with conn.transaction():
                await conn.execute("LOCK TABLE users IN EXCLUSIVE MODE")
                has_admin = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM users WHERE role=$1 AND active=true)", UserRole.ADMIN.value)
                if has_admin:
                    raise PermissionError("admin already exists")
                exists = await conn.fetchval("SELECT id FROM users WHERE lower(email)=lower($1)", normalized_email)
                if exists:
                    raise ValueError("email already exists")
                user = User(
                    id=uuid4().hex,
                    email=normalized_email,
                    password_hash=hash_password(password),
                    role=UserRole.ADMIN,
                )
                await conn.execute(
                    "INSERT INTO users(id, email, password_hash, role, tenant_id, active) VALUES($1,$2,$3,$4,$5,true)",
                    user.id,
                    user.email,
                    user.password_hash,
                    user.role.value,
                    user.tenant_id,
                )
                return user

    def _user(self, row: asyncpg.Record | None) -> User | None:
        if row is None:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=UserRole(row["role"]),
            tenant_id=row["tenant_id"],
            active=row["active"],
            created_at=row["created_at"],
        )

    async def get_user_by_email(self, email: str) -> User | None:
        async with self._pool().acquire() as conn:
            return self._user(await conn.fetchrow("SELECT * FROM users WHERE lower(email)=lower($1)", email))

    async def get_user(self, user_id: str) -> User | None:
        async with self._pool().acquire() as conn:
            return self._user(await conn.fetchrow("SELECT * FROM users WHERE id=$1", user_id))

    async def upsert_upstream(self, upstream: UpstreamEndpoint) -> UpstreamEndpoint:
        upstream.updated_at = utcnow()
        async with self._pool().acquire() as conn:
            await conn.execute(
                """
                INSERT INTO upstreams(id,type,endpoint,tenant_id,enabled,envelope_mode,created_at,updated_at)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8)
                ON CONFLICT(id) DO UPDATE SET type=$2, endpoint=$3, tenant_id=$4, enabled=$5, envelope_mode=$6, updated_at=$8
                """,
                upstream.id,
                upstream.type,
                upstream.endpoint,
                upstream.tenant_id,
                upstream.enabled,
                upstream.envelope_mode,
                upstream.created_at,
                upstream.updated_at,
            )
        return upstream

    def _upstream(self, row: asyncpg.Record) -> UpstreamEndpoint:
        return UpstreamEndpoint(
            id=row["id"],
            type=row["type"],
            endpoint=row["endpoint"],
            tenant_id=row["tenant_id"],
            enabled=row["enabled"],
            envelope_mode=row["envelope_mode"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def list_upstreams(self) -> list[UpstreamEndpoint]:
        async with self._pool().acquire() as conn:
            return [self._upstream(row) for row in await conn.fetch("SELECT * FROM upstreams ORDER BY id")]

    async def upsert_server(self, server: DownstreamServer) -> DownstreamServer:
        server.updated_at = utcnow()
        async with self._pool().acquire() as conn:
            await conn.execute(
                """
                INSERT INTO downstream_servers(id,transport,namespace,tenant_id,endpoint,command,args,env,auth,enabled,timeout_ms,tags,status,latency_ms,failure_count,circuit_open_until,created_at,updated_at)
                VALUES($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9::jsonb,$10,$11,$12::jsonb,$13,$14,$15,$16,$17,$18)
                ON CONFLICT(id) DO UPDATE SET transport=$2, namespace=$3, tenant_id=$4, endpoint=$5, command=$6, args=$7::jsonb, env=$8::jsonb, auth=$9::jsonb, enabled=$10, timeout_ms=$11, tags=$12::jsonb, status=$13, latency_ms=$14, failure_count=$15, circuit_open_until=$16, updated_at=$18
                """,
                server.id,
                server.transport.value,
                server.namespace,
                server.tenant_id,
                server.endpoint,
                server.command,
                _json(server.args),
                _json(server.env),
                _json(asdict(server.auth)),
                server.enabled,
                server.timeout_ms,
                _json(server.tags),
                server.status.value,
                server.latency_ms,
                server.failure_count,
                server.circuit_open_until,
                server.created_at,
                server.updated_at,
            )
        return server

    def _server(self, row: asyncpg.Record) -> DownstreamServer:
        auth = AuthConfig(**_as_dict(row["auth"]))
        return DownstreamServer(
            id=row["id"],
            transport=TransportType(row["transport"]),
            namespace=row["namespace"],
            tenant_id=row["tenant_id"],
            endpoint=row["endpoint"],
            command=row["command"],
            args=[str(item) for item in _as_list(row["args"])],
            env={str(k): str(v) for k, v in _as_dict(row["env"]).items()},
            auth=auth,
            enabled=row["enabled"],
            timeout_ms=row["timeout_ms"],
            tags=[str(item) for item in _as_list(row["tags"])],
            status=ServerStatus(row["status"]),
            latency_ms=row["latency_ms"],
            failure_count=row["failure_count"],
            circuit_open_until=row["circuit_open_until"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_server(self, server_id: str) -> DownstreamServer | None:
        async with self._pool().acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM downstream_servers WHERE id=$1", server_id)
            return self._server(row) if row else None

    async def list_servers(self) -> list[DownstreamServer]:
        async with self._pool().acquire() as conn:
            return [self._server(row) for row in await conn.fetch("SELECT * FROM downstream_servers ORDER BY id")]

    async def replace_tools_for_server(self, server_id: str, tools: list[ToolRecord]) -> None:
        async with self._pool().acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM tools WHERE server_id=$1", server_id)
                for tool in tools:
                    await self._upsert_tool(conn, tool)

    async def _upsert_tool(self, conn: asyncpg.Connection, tool: ToolRecord) -> None:
        tool.updated_at = utcnow()
        await conn.execute(
            """
            INSERT INTO tools(tool_id,display_name,server_id,origin_tool_name,description,input_schema,annotations,enabled,risk_level,tenant_id,device_scope,tags,created_at,updated_at)
            VALUES($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8,$9,$10,$11::jsonb,$12::jsonb,$13,$14)
            ON CONFLICT(tool_id) DO UPDATE SET display_name=$2, server_id=$3, origin_tool_name=$4, description=$5, input_schema=$6::jsonb, annotations=$7::jsonb, enabled=$8, risk_level=$9, tenant_id=$10, device_scope=$11::jsonb, tags=$12::jsonb, updated_at=$14
            """,
            tool.tool_id,
            tool.display_name,
            tool.server_id,
            tool.origin_tool_name,
            tool.description,
            _json(tool.input_schema),
            _json(tool.annotations),
            tool.enabled,
            tool.risk_level.value,
            tool.tenant_id,
            _json(tool.device_scope),
            _json(tool.tags),
            tool.created_at,
            tool.updated_at,
        )

    async def upsert_tool(self, tool: ToolRecord) -> ToolRecord:
        async with self._pool().acquire() as conn:
            await self._upsert_tool(conn, tool)
        return tool

    def _tool(self, row: asyncpg.Record) -> ToolRecord:
        return ToolRecord(
            tool_id=row["tool_id"],
            display_name=row["display_name"],
            server_id=row["server_id"],
            origin_tool_name=row["origin_tool_name"],
            description=row["description"],
            input_schema=_as_dict(row["input_schema"]),
            annotations=_as_dict(row["annotations"]),
            enabled=row["enabled"],
            risk_level=RiskLevel(row["risk_level"]),
            tenant_id=row["tenant_id"],
            device_scope=[str(item) for item in _as_list(row["device_scope"])],
            tags=[str(item) for item in _as_list(row["tags"])],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_tool(self, tool_id: str) -> ToolRecord | None:
        async with self._pool().acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tools WHERE tool_id=$1", tool_id)
            return self._tool(row) if row else None

    async def list_tools(self, tenant_id: str | None = None, enabled: bool | None = None) -> list[ToolRecord]:
        query = "SELECT * FROM tools WHERE ($1::text IS NULL OR tenant_id=$1) AND ($2::boolean IS NULL OR enabled=$2) ORDER BY tool_id"
        async with self._pool().acquire() as conn:
            return [self._tool(row) for row in await conn.fetch(query, tenant_id, enabled)]

    async def upsert_acl(self, acl: ToolAcl) -> ToolAcl:
        async with self._pool().acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tool_acl(id,tool_id,tenant_id,roles,upstream_ids,device_scope,enabled)
                VALUES($1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7)
                ON CONFLICT(id) DO UPDATE SET tool_id=$2, tenant_id=$3, roles=$4::jsonb, upstream_ids=$5::jsonb, device_scope=$6::jsonb, enabled=$7
                """,
                acl.id,
                acl.tool_id,
                acl.tenant_id,
                _json([role.value for role in acl.roles]),
                _json(acl.upstream_ids),
                _json(acl.device_scope),
                acl.enabled,
            )
        return acl

    def _acl(self, row: asyncpg.Record) -> ToolAcl:
        return ToolAcl(
            id=row["id"],
            tool_id=row["tool_id"],
            tenant_id=row["tenant_id"],
            roles=[UserRole(role) for role in _as_list(row["roles"])],
            upstream_ids=[str(item) for item in _as_list(row["upstream_ids"])],
            device_scope=[str(item) for item in _as_list(row["device_scope"])],
            enabled=row["enabled"],
        )

    async def list_acl_for_tool(self, tool_id: str) -> list[ToolAcl]:
        async with self._pool().acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tool_acl WHERE tool_id=$1 AND enabled=true", tool_id)
            return [self._acl(row) for row in rows]

    async def list_acl(self) -> list[ToolAcl]:
        async with self._pool().acquire() as conn:
            return [self._acl(row) for row in await conn.fetch("SELECT * FROM tool_acl ORDER BY id")]

    async def create_approval(self, approval: ApprovalRequest) -> ApprovalRequest:
        async with self._pool().acquire() as conn:
            await conn.execute(
                """
                INSERT INTO approvals(id,tool_id,arguments,status,tenant_id,trace_id,requested_by,decided_by,reason,result,created_at,decided_at,expires_at)
                VALUES($1,$2,$3::jsonb,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12,$13)
                """,
                approval.id,
                approval.tool_id,
                _json(approval.arguments),
                approval.status.value,
                approval.tenant_id,
                approval.trace_id,
                approval.requested_by,
                approval.decided_by,
                approval.reason,
                _json(approval.result) if approval.result is not None else None,
                approval.created_at,
                approval.decided_at,
                approval.expires_at,
            )
        return approval

    def _approval(self, row: asyncpg.Record | None) -> ApprovalRequest | None:
        if row is None:
            return None
        return ApprovalRequest(
            id=row["id"],
            tool_id=row["tool_id"],
            arguments=_as_dict(row["arguments"]),
            status=ApprovalStatus(row["status"]),
            tenant_id=row["tenant_id"],
            trace_id=row["trace_id"],
            requested_by=row["requested_by"],
            decided_by=row["decided_by"],
            reason=row["reason"],
            result=_as_dict(row["result"]) if row["result"] is not None else None,
            created_at=row["created_at"],
            decided_at=row["decided_at"],
            expires_at=row["expires_at"],
        )

    async def get_approval(self, approval_id: str) -> ApprovalRequest | None:
        async with self._pool().acquire() as conn:
            return self._approval(await conn.fetchrow("SELECT * FROM approvals WHERE id=$1", approval_id))

    async def update_approval(self, approval: ApprovalRequest) -> ApprovalRequest:
        async with self._pool().acquire() as conn:
            await conn.execute(
                "UPDATE approvals SET status=$2, decided_by=$3, reason=$4, result=$5::jsonb, decided_at=$6 WHERE id=$1",
                approval.id,
                approval.status.value,
                approval.decided_by,
                approval.reason,
                _json(approval.result) if approval.result is not None else None,
                approval.decided_at,
            )
        return approval

    async def list_approvals(self, status: str | None = None) -> list[ApprovalRequest]:
        async with self._pool().acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM approvals WHERE ($1::text IS NULL OR status=$1) ORDER BY created_at DESC",
                status,
            )
            return [item for item in (self._approval(row) for row in rows) if item is not None]

    async def add_audit(self, audit: AuditLog) -> None:
        async with self._pool().acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_logs(id,trace_id,action,tenant_id,actor_id,tool_id,server_id,status,latency_ms,error,metadata,created_at)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12)
                """,
                audit.id,
                audit.trace_id,
                audit.action,
                audit.tenant_id,
                audit.actor_id,
                audit.tool_id,
                audit.server_id,
                audit.status,
                audit.latency_ms,
                audit.error,
                _json(audit.metadata),
                audit.created_at,
            )

    async def list_audit(self, limit: int = 100) -> list[AuditLog]:
        async with self._pool().acquire() as conn:
            rows = await conn.fetch("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT $1", limit)
            return [
                AuditLog(
                    id=row["id"],
                    trace_id=row["trace_id"],
                    action=row["action"],
                    tenant_id=row["tenant_id"],
                    actor_id=row["actor_id"],
                    tool_id=row["tool_id"],
                    server_id=row["server_id"],
                    status=row["status"],
                    latency_ms=row["latency_ms"],
                    error=row["error"],
                    metadata=_as_dict(row["metadata"]),
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def add_config_version(self, payload: dict[str, Any], created_by: str | None = None) -> ConfigVersion:
        async with self._pool().acquire() as conn:
            version = int(await conn.fetchval("SELECT COALESCE(MAX(version), 0) + 1 FROM config_versions"))
            item = ConfigVersion(id=uuid4().hex, version=version, payload=payload, created_by=created_by)
            await conn.execute(
                "INSERT INTO config_versions(id,version,payload,created_by,created_at) VALUES($1,$2,$3::jsonb,$4,$5)",
                item.id,
                item.version,
                _json(item.payload),
                item.created_by,
                item.created_at,
            )
            return item

    async def list_config_versions(self) -> list[ConfigVersion]:
        async with self._pool().acquire() as conn:
            rows = await conn.fetch("SELECT * FROM config_versions ORDER BY version DESC")
            return [
                ConfigVersion(
                    id=row["id"],
                    version=row["version"],
                    payload=_as_dict(row["payload"]),
                    created_by=row["created_by"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def export_config(self) -> dict[str, Any]:
        return {
            "upstreams": [asdict(item) for item in await self.list_upstreams()],
            "servers": [asdict(item) for item in await self.list_servers()],
        }
