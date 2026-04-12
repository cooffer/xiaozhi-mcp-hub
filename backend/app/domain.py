from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TransportType(str, Enum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable_http"
    SSE = "sse"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServerStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    CIRCUIT_OPEN = "circuit_open"


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(slots=True)
class AuthConfig:
    type: str = "none"
    token_ref: str | None = None
    api_key_ref: str | None = None
    username_ref: str | None = None
    password_ref: str | None = None
    header_name: str | None = None


@dataclass(slots=True)
class UpstreamEndpoint:
    id: str
    type: str
    endpoint: str
    tenant_id: str = "default"
    enabled: bool = True
    envelope_mode: str = "raw"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class DownstreamServer:
    id: str
    transport: TransportType
    namespace: str
    tenant_id: str = "default"
    endpoint: str | None = None
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    auth: AuthConfig = field(default_factory=AuthConfig)
    enabled: bool = True
    timeout_ms: int = 30_000
    tags: list[str] = field(default_factory=list)
    status: ServerStatus = ServerStatus.UNKNOWN
    latency_ms: float | None = None
    failure_count: int = 0
    circuit_open_until: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ToolRecord:
    tool_id: str
    display_name: str
    server_id: str
    origin_tool_name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    annotations: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    tenant_id: str = "default"
    device_scope: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class User:
    id: str
    email: str
    password_hash: str
    role: UserRole = UserRole.VIEWER
    tenant_id: str = "default"
    active: bool = True
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ToolAcl:
    id: str
    tool_id: str
    tenant_id: str = "default"
    roles: list[UserRole] = field(default_factory=lambda: [UserRole.ADMIN, UserRole.OPERATOR])
    upstream_ids: list[str] = field(default_factory=list)
    device_scope: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass(slots=True)
class ToolCallContext:
    tenant_id: str = "default"
    upstream_id: str | None = None
    device_id: str | None = None
    actor_role: UserRole = UserRole.OPERATOR
    actor_id: str | None = None
    trace_id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(slots=True)
class ApprovalRequest:
    id: str
    tool_id: str
    arguments: dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    tenant_id: str = "default"
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    requested_by: str | None = None
    decided_by: str | None = None
    reason: str | None = None
    result: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=utcnow)
    decided_at: datetime | None = None
    expires_at: datetime | None = None


@dataclass(slots=True)
class AuditLog:
    id: str
    trace_id: str
    action: str
    tenant_id: str = "default"
    actor_id: str | None = None
    tool_id: str | None = None
    server_id: str | None = None
    status: str = "ok"
    latency_ms: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ConfigVersion:
    id: str
    version: int
    payload: dict[str, Any]
    created_by: str | None = None
    created_at: datetime = field(default_factory=utcnow)
