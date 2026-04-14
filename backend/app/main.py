from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.deps import bridge_manager, connectors, store
from .api.observability import REQUESTS
from .api.routers import approvals, audit, auth, config, mcp, metrics, servers, tools, upstreams
from .settings import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期。

    启动时连接持久化存储、重建下游连接器缓存，并按数据库里的小智接入点配置
    启动 bridge。关闭时先停止 bridge 后台任务，再关闭存储连接。
    """

    if hasattr(store, "connect"):
        await store.connect()
    if settings.auto_create_initial_admin:
        await store.seed_admin(settings.initial_admin_email, settings.initial_admin_password)
    await connectors.reload_all()
    await bridge_manager.sync()
    yield
    await bridge_manager.stop_all()
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


for router in [
    auth.router,
    upstreams.router,
    servers.router,
    tools.router,
    approvals.router,
    audit.router,
    config.router,
    metrics.router,
    mcp.router,
]:
    app.include_router(router, prefix="/api/v1")

app.include_router(metrics.raw_metrics_router)
