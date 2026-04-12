from __future__ import annotations

import logging
import hashlib
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .acl import AccessControlService
from .approvals import ApprovalService
from .audit import AuditService
from .bridge import XiaozhiOfficialBridge
from .config_import import import_config, load_payload
from .connector_manager import ConnectorManager
from .domain import AuthConfig, DownstreamServer, RiskLevel, ToolAcl, ToolCallContext, TransportType, UpstreamEndpoint, User, UserRole
from .mcp_hub import McpHub
from .schemas import ApprovalDecision, BootstrapStatus, LoginRequest, LoginResponse, RegisterRequest, ServerIn, UpstreamIn, public_dict
from .security import create_token, decode_token, verify_password
from .settings import settings
from .store import InMemoryStore

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

REQUESTS = Counter("xiaozhi_mcp_hub_requests_total", "API requests", ["path"])
MCP_CALLS = Counter("xiaozhi_mcp_hub_mcp_calls_total", "MCP calls", ["method", "status"])
MCP_LATENCY = Histogram("xiaozhi_mcp_hub_mcp_latency_seconds", "MCP call latency")

if settings.store_backend == "memory":
    store = InMemoryStore()
else:
    from .postgres_store import PostgresStore

    store = PostgresStore(settings.database_url)
connectors = ConnectorManager(store)
acl_service = AccessControlService(store)
approval_service = ApprovalService(store)
audit_service = AuditService(store)
hub = McpHub(store, connectors, acl_service, approval_service, audit_service)
bridges: dict[str, XiaozhiOfficialBridge] = {}


def _stable_upstream_id(channel: str, endpoint: str) -> str:
    digest = hashlib.sha1(endpoint.encode("utf-8")).hexdigest()[:10]
    safe_channel = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in channel.lower()).strip("-_") or "upstream"
    return f"{safe_channel}-{digest}"


def normalize_upstream_channel(value: Any) -> str:
    channel = str(value or "xiaozhi_official").strip().lower().replace("-", "_").replace(" ", "_")
    if channel in {"xiaozhi", "xiaozhi_official", "小智", "小智官方"}:
        return "xiaozhi_official"
    return channel or "xiaozhi_official"


def build_upstream(payload: UpstreamIn) -> UpstreamEndpoint:
    data = payload.model_dump()
    channel = normalize_upstream_channel(data.pop("channel") or data.get("type") or "xiaozhi_official")
    endpoint = str(data["endpoint"])
    upstream_id = str(data.pop("id") or _stable_upstream_id(channel, endpoint))
    data["type"] = channel
    data["tenant_id"] = "default"
    return UpstreamEndpoint(id=upstream_id, **data)


async def sync_bridges() -> None:
    upstreams = {upstream.id: upstream for upstream in await store.list_upstreams()}
    for bridge_id in list(bridges):
        if bridge_id not in upstreams or not upstreams[bridge_id].enabled:
            await bridges[bridge_id].stop()
            del bridges[bridge_id]
    for upstream in upstreams.values():
        if not upstream.enabled:
            continue
        existing = bridges.get(upstream.id)
        if existing:
            if existing.upstream.endpoint == upstream.endpoint and existing.upstream.type == upstream.type:
                continue
            await existing.stop()
        bridge = XiaozhiOfficialBridge(upstream, hub)
        bridges[upstream.id] = bridge
        await bridge.start()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if hasattr(store, "connect"):
        await store.connect()
    if settings.auto_create_initial_admin:
        await store.seed_admin(settings.initial_admin_email, settings.initial_admin_password)
    await connectors.reload_all()
    await sync_bridges()
    yield
    for bridge in list(bridges.values()):
        await bridge.stop()
    if hasattr(store, "close"):
        await store.close()


app = FastAPI(title="Xiaozhi MCP Hub", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    REQUESTS.labels(path=request.url.path).inc()
    return await call_next(request)


async def current_user(authorization: Annotated[str | None, Header()] = None) -> User:
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
    token = create_token({"sub": user.id, "role": user.role.value, "tenant_id": user.tenant_id}, settings.jwt_secret)
    user_data = public_dict(user)
    user_data.pop("password_hash", None)
    return LoginResponse(access_token=token, user=user_data)


@app.get("/api/v1/auth/bootstrap-status", response_model=BootstrapStatus)
async def bootstrap_status() -> BootstrapStatus:
    return BootstrapStatus(registration_open=not await store.has_admin_user())


@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    user = await store.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return login_response(user)


@app.post("/api/v1/auth/register", response_model=LoginResponse)
async def register(payload: RegisterRequest) -> LoginResponse:
    try:
        user = await store.create_first_admin(payload.email, payload.password)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="registration is closed") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="email already exists") from exc
    return login_response(user)


@app.get("/api/v1/auth/me")
async def me(user: Annotated[User, Depends(current_user)]):
    data = public_dict(user)
    data.pop("password_hash", None)
    return data


@app.post("/api/v1/auth/logout")
async def logout(_: Annotated[User, Depends(current_user)]):
    return {"ok": True}


@app.get("/api/v1/upstreams")
async def list_upstreams(_: Annotated[User, Depends(current_user)]):
    items = []
    for upstream in await store.list_upstreams():
        data = public_dict(upstream)
        data["channel"] = upstream.type
        items.append(data)
    return items


@app.post("/api/v1/upstreams")
async def upsert_upstream(payload: UpstreamIn, _: Annotated[User, Depends(require_admin)]):
    upstream = build_upstream(payload)
    await store.upsert_upstream(upstream)
    await sync_bridges()
    data = public_dict(upstream)
    data["channel"] = upstream.type
    return data


@app.get("/api/v1/servers")
async def list_servers(_: Annotated[User, Depends(current_user)]):
    return [public_dict(item) for item in await store.list_servers()]


@app.post("/api/v1/servers")
async def upsert_server(payload: ServerIn, _: Annotated[User, Depends(require_admin)]):
    auth = AuthConfig(**payload.auth) if payload.auth else AuthConfig()
    data = payload.model_dump(exclude={"auth"})
    transport = data.pop("transport")
    if transport in {"http", "streamablehttp", "streamable-http"}:
        transport = "streamable_http"
    if transport in {"legacy_sse", "legacy-sse"}:
        transport = "sse"
    server = DownstreamServer(**data, transport=TransportType(transport), auth=auth)
    await store.upsert_server(server)
    await connectors.reload_server(server)
    return public_dict(server)


@app.post("/api/v1/servers/{server_id}/discover")
async def discover_server(server_id: str, _: Annotated[User, Depends(require_operator)]):
    server = await store.get_server(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="server not found")
    try:
        raw_tools = await connectors.discover_server(server)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"failed to discover server {server_id}: {exc}") from exc
    return {"server_id": server_id, "tools": len(raw_tools)}


@app.get("/api/v1/tools")
async def list_tools(_: Annotated[User, Depends(current_user)]):
    return [public_dict(item) for item in await store.list_tools()]


@app.patch("/api/v1/tools/{tool_id}")
async def update_tool(tool_id: str, payload: dict[str, Any], _: Annotated[User, Depends(require_operator)]):
    tool = await store.get_tool(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="tool not found")
    for field in ["display_name", "description", "enabled", "risk_level", "device_scope", "tags"]:
        if field in payload:
            value = payload[field]
            if field == "risk_level":
                value = RiskLevel(value)
            setattr(tool, field, value)
    await store.upsert_tool(tool)
    return public_dict(tool)


@app.get("/api/v1/routes")
async def routes(_: Annotated[User, Depends(current_user)]):
    tools = await store.list_tools()
    servers = {server.id: server for server in await store.list_servers()}
    return [
        {
            "tool_id": tool.tool_id,
            "server_id": tool.server_id,
            "origin_tool_name": tool.origin_tool_name,
            "server_status": servers.get(tool.server_id).status.value if servers.get(tool.server_id) else "missing",
        }
        for tool in tools
    ]


@app.get("/api/v1/acl")
async def list_acl(_: Annotated[User, Depends(current_user)]):
    if hasattr(store, "list_acl"):
        return [public_dict(item) for item in await store.list_acl()]
    return [public_dict(item) for item in store.acl.values()]


@app.post("/api/v1/acl")
async def upsert_acl(payload: dict[str, Any], _: Annotated[User, Depends(require_admin)]):
    acl = ToolAcl(
        id=str(payload.get("id") or f"acl-{payload['tool_id']}"),
        tool_id=str(payload["tool_id"]),
        tenant_id=str(payload.get("tenant_id") or "default"),
        roles=[UserRole(role) for role in payload.get("roles", ["admin", "operator"])],
        upstream_ids=[str(item) for item in payload.get("upstream_ids", [])],
        device_scope=[str(item) for item in payload.get("device_scope", [])],
        enabled=bool(payload.get("enabled", True)),
    )
    await store.upsert_acl(acl)
    return public_dict(acl)


@app.get("/api/v1/approvals")
async def list_approvals(_: Annotated[User, Depends(current_user)], status: str | None = None):
    return [public_dict(item) for item in await store.list_approvals(status=status)]


@app.post("/api/v1/approvals/{approval_id}/approve")
async def approve(approval_id: str, user: Annotated[User, Depends(require_operator)]):
    return public_dict(await approval_service.approve(approval_id, actor_id=user.id))


@app.post("/api/v1/approvals/{approval_id}/reject")
async def reject(approval_id: str, payload: ApprovalDecision, user: Annotated[User, Depends(require_operator)]):
    return public_dict(await approval_service.reject(approval_id, actor_id=user.id, reason=payload.reason))


@app.get("/api/v1/audit-logs")
async def audit_logs(_: Annotated[User, Depends(current_user)], limit: int = 100):
    return [public_dict(item) for item in await store.list_audit(limit=limit)]


@app.post("/api/v1/config/import")
async def config_import(
    user: Annotated[User, Depends(require_admin)],
    file: UploadFile | None = File(default=None),
    raw: str | None = Form(default=None),
):
    if file is not None:
        text = (await file.read()).decode("utf-8")
    else:
        text = raw or ""
    payload = load_payload(text)
    result = await import_config(payload, store, connectors, created_by=user.id)
    await sync_bridges()
    return result


@app.get("/api/v1/config/export")
async def config_export(_: Annotated[User, Depends(current_user)]):
    return await store.export_config()


@app.get("/api/v1/config/versions")
async def config_versions(_: Annotated[User, Depends(current_user)]):
    return [public_dict(item) for item in await store.list_config_versions()]


@app.get("/api/v1/health")
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


@app.get("/api/v1/metrics/summary")
async def metrics_summary(_: Annotated[User, Depends(current_user)]):
    return await build_metrics_summary()


@app.get("/api/v1/dashboard/summary")
async def dashboard_summary(_: Annotated[User, Depends(current_user)]):
    return await build_metrics_summary()


@app.post("/api/v1/mcp")
async def mcp_endpoint(payload: dict[str, Any] | list[dict[str, Any]], user: Annotated[User, Depends(require_operator)]):
    context = ToolCallContext(tenant_id=user.tenant_id, actor_id=user.id, actor_role=user.role)
    with MCP_LATENCY.time():
        response = await hub.handle(payload, context)
    if isinstance(payload, dict):
        MCP_CALLS.labels(method=str(payload.get("method") or "batch"), status="ok").inc()
    else:
        MCP_CALLS.labels(method="batch", status="ok").inc()
    return response or Response(status_code=202)


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
