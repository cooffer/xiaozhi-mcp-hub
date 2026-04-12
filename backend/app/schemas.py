from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def public_dict(item: Any) -> dict[str, Any]:
    if is_dataclass(item):
        data = asdict(item)
    elif isinstance(item, dict):
        data = dict(item)
    else:
        data = item.model_dump()
    return _jsonable(data)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any] | None = None


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class BootstrapStatus(BaseModel):
    registration_open: bool


class UpstreamIn(BaseModel):
    id: str | None = None
    channel: str | None = None
    type: str = "xiaozhi_official"
    endpoint: str
    tenant_id: str = "default"
    enabled: bool = True
    envelope_mode: str = "raw"


class ServerIn(BaseModel):
    id: str
    transport: str
    namespace: str
    tenant_id: str = "default"
    endpoint: str | None = None
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    auth: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    timeout_ms: int = 30_000
    tags: list[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    reason: str | None = None
