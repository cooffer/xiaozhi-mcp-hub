# Xiaozhi MCP Hub

## 外部 MCP 如何暴露给小智

1. 在小智后台获取官方 MCP 接入点。
2. 登录本项目 WebUI，在“小智接入”页面选择渠道“小智官方”，粘贴接入点并启用。
3. 在“配置导入”页面导入下游 MCP 配置，或在“下游服务”页面手动新增服务。
4. Hub 会对启用的下游服务执行 `initialize`、`notifications/initialized`、`tools/list`，并把发现到的工具写入工具注册中心。
5. 小智官方通过上游连接调用 Hub 的 `tools/list` 时，会看到内置 `hub.status` 和所有已发现、已启用、通过 ACL 的工具。
6. 小智调用工具时使用统一 `tool_id`，Hub 再路由到对应下游 MCP Server 的原始工具名。

## 兼容哪些 MCP 服务

| 类型 | 兼容状态 | 配置方式 | 说明 |
| --- | --- | --- | --- |
| stdio | 支持 | `command` + `args` + `env` | 适合 Node/Python 本地 MCP Server，例如 filesystem、git、time、memory 类服务。 |
| Streamable HTTP | 支持基础 JSON-RPC POST + session | `transport: streamable_http` + `endpoint` | 支持 `Mcp-Session-Id`、Bearer/API key 引用和标准 tools 流程。 |
| legacy SSE | 兼容常见 POST JSON-RPC 路径 | `transport: sse` + `endpoint` | 旧服务如果只提供纯 SSE 事件流且没有 POST 调用端点，需要后续扩展。 |

首版兼容范围聚焦工具型 MCP Server：`initialize`、`notifications/initialized`、`tools/list`、`tools/call`。暂不承诺完整 `resources`、`prompts`、`sampling` 和 OAuth 授权向导。

## 配置导入格式

项目原生格式：

```yaml
servers:
  - id: local-demo
    transport: stdio
    command: python.exe
    args: ["../examples/downstream-mcp/demo_server.py"]
    namespace: demo
    enabled: true
```

兼容常见 `mcpServers` 格式：

```json
{
  "mcpServers": {
    "demo": {
      "command": "python",
      "args": ["../examples/downstream-mcp/demo_server.py"],
      "namespace": "demo"
    },
    "remote-tools": {
      "type": "streamable_http",
      "url": "https://example.com/mcp"
    }
  }
}
```

导入成功后返回服务数、自动发现到的工具数、错误明细和配置版本。只有成功发现并写入工具注册中心的工具，才会暴露给小智。

## 下游 MCP 示例

示例位于：

```text
examples/downstream-mcp/
```

包含：

- `demo_server.py`：无第三方依赖的 stdio MCP Server。
- `hub-config.yaml`：可直接导入本项目后台的示例配置。
- `mcpServers.json`：兼容常见 MCP 客户端的配置示例。

导入后会出现以下工具：

```text
demo.echo
demo.add
demo.get_server_status
```

专门为本项目开发下游 MCP 服务时，请注意：

- stdio 服务不要向 stdout 打印日志，stdout 只能输出 JSON-RPC。
- 每个工具都要提供清晰的 `description` 和 `inputSchema`。
- 返回结果使用 MCP `CallToolResult` 结构：`content`、可选 `structuredContent`、`isError`。
- 使用稳定 namespace，避免与其他服务工具名冲突。

面向 `xiaozhi-esp32` 官方 MCP 接入方式的生产级 MCP 聚合网关。

本项目把多个下游 MCP Server 聚合成一个统一的 MCP Hub，再通过小智官方 `MCP_ENDPOINT` 暴露给 `xiaozhi.me`。它的目标不是简单代理，而是提供工具注册、路由、权限、审批、审计、健康检查和可观测能力，让大量 MCP 服务可以安全、快速地接入小智生态。

## 项目结构

```text
.
├── backend/          FastAPI 后端、MCP Hub 核心、连接器、审批、审计、存储
├── frontend/         React + Vite 管理后台
├── deploy/           Prometheus 配置
├── examples/         可导入的 Hub 配置示例
├── docker-compose.yml
├── .env.example
└── README_CN.md
```

## 核心能力

- 上游适配：通过 WebSocket 接入小智官方 `MCP_ENDPOINT`，兼容 `mcp-calculator` 风格。
- MCP 生命周期：支持 `initialize`、`notifications/initialized`、`tools/list`、`tools/call`、`ping` 和 JSON-RPC batch。
- 下游连接器：支持 `stdio`、Streamable HTTP、兼容旧 SSE。
- 工具注册中心：统一生成 `tool_id`，处理重名冲突，保留原始工具名与下游 server 映射。
- 路由：首版实现精确路由，保留策略路由和编排扩展点。
- 安全：内置 RBAC、工具级 ACL、高危工具 WebUI 审批、secret 引用与脱敏。
- 治理：调用审计、trace id、限流、健康状态、错误记录、Prometheus metrics。
- 配置中心：支持 YAML/JSON 导入导出，配置版本记录，server 热重载。
- 部署：提供 Docker Compose，包含 `backend`、`frontend`、`postgres`、`redis`、`prometheus`、`grafana`。

## 快速启动

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

启动完整服务：

```powershell
docker compose up --build
```

默认访问地址：

- WebUI: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

首次部署时，如果数据库中没有管理员，打开 WebUI 后可以在登录页注册第一个账号。第一个注册用户会自动成为后台管理员，之后公开注册入口会关闭。

如果你希望开发环境自动创建管理员，可以显式开启：

```env
AUTO_CREATE_INITIAL_ADMIN=true
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=change-me
```

## 本地开发

后端：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\uvicorn app.main:app --reload
```

默认 `backend/.env.example` 使用 `STORE_BACKEND=memory`，适合本地快速启动，不依赖 Postgres。

如果你希望本地 venv 也使用 Postgres，请先启动一个本机可访问的 PostgreSQL，然后把 `backend/.env` 改成：

```env
STORE_BACKEND=postgres
DATABASE_URL=postgresql+asyncpg://xiaozhi:xiaozhi@localhost:5432/xiaozhi_mcp_hub
```

注意：根目录 `.env` 主要给 Docker Compose 使用，里面的数据库主机名通常是 `postgres`。这个主机名只在 Docker Compose 网络中有效，不能直接用于本机 PowerShell 启动的 `uvicorn`。

前端：

```powershell
cd frontend
npm install
npm run dev
```

本地开发时，前端 `http://localhost:5173` 会通过 Vite proxy 把 `/api/*` 转发到后端 `http://127.0.0.1:8000`。因此登录后台前需要确认后端 `uvicorn` 正在运行。

前端生产构建：

```powershell
cd frontend
npm run build
```

## 关键环境变量

```env
APP_ENV=development
BACKEND_PORT=8000
FRONTEND_PORT=5173

DATABASE_URL=postgresql+asyncpg://xiaozhi:xiaozhi@postgres:5432/xiaozhi_mcp_hub
REDIS_URL=redis://redis:6379/0

JWT_SECRET=change-me-in-production
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=change-me
AUTO_CREATE_INITIAL_ADMIN=false

STORE_BACKEND=postgres
```

说明：

- `STORE_BACKEND=postgres`：默认生产模式，使用 Postgres。
- `STORE_BACKEND=memory`：适合测试或临时调试，数据不会持久化。
- `JWT_SECRET`：生产环境必须修改。

## 配置导入

示例配置位于：

```text
examples/hub-config.yaml
```

示例：

```yaml
servers:
  - id: ha-prod
    transport: streamable_http
    endpoint: https://ha.example.com/mcp
    namespace: home
    auth:
      type: bearer
      token_ref: HA_TOKEN
    enabled: true
    timeout_ms: 30000

  - id: fs-local
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"]
    namespace: files
    enabled: true
```

通过 API 导入：

```http
POST /api/v1/config/import
```

也可以在 WebUI 中导入 YAML/JSON 配置。

## 工具命名规则

Hub 暴露给小智的工具名是统一 `tool_id`：

```text
{namespace}.{origin_tool_name}
```

例如：

```text
home.turn_on_light
files.read_file
```

如果多个下游 MCP Server 出现同名工具，会追加 server id：

```text
home.turn_on_light__ha-prod
```

调用时 Hub 会把统一 `tool_id` 映射回：

```text
server_id + origin_tool_name
```

## API 概览

所有管理 API 默认挂在 `/api/v1`：

- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`
- `GET /upstreams`
- `POST /upstreams`
- `GET /servers`
- `POST /servers`
- `POST /servers/{server_id}/discover`
- `GET /tools`
- `PATCH /tools/{tool_id}`
- `GET /routes`
- `GET /acl`
- `POST /acl`
- `GET /approvals`
- `POST /approvals/{approval_id}/approve`
- `POST /approvals/{approval_id}/reject`
- `GET /audit-logs`
- `POST /config/import`
- `GET /config/export`
- `GET /config/versions`
- `GET /health`
- `GET /metrics/summary`
- `POST /mcp`

MCP HTTP 调试入口：

```http
POST /api/v1/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

示例：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

## 安全默认值

- 不会把上游小智 token 透传给下游 MCP Server。
- 下游凭据通过 `token_ref`、`api_key_ref` 等 secret 引用获取，API 响应不展示明文 secret。
- `admin` 可以管理全部资源。
- `operator` 可以调用默认允许的工具和处理审批。
- `viewer` 默认只读，不能直接调用工具。
- `high` / `critical` 风险工具默认进入审批流。
- 每次 MCP 调用都会生成 `trace_id` 并写入审计日志。

## 高危工具审批

当工具风险等级为：

```text
high
critical
```

Hub 会创建审批单并等待 WebUI 管理员处理。

审批超时后，MCP 调用返回：

```json
{
  "code": -32010,
  "message": "approval_pending",
  "data": {
    "approval_id": "..."
  }
}
```

该设计避免高危操作在没有明确授权时自动执行。

## 测试

当前核心测试使用 Python 标准库 `unittest`：

```powershell
python -m unittest discover -s backend\tests
```

前端构建：

```powershell
cd frontend
npm run build
```

后端源码语法检查可用：

```powershell
python -c "import pathlib; files=list(pathlib.Path('backend/app').rglob('*.py')); [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in files]; print(f'compiled {len(files)} files in memory')"
```

## 当前实现边界

- 第一版只接小智官方 `MCP_ENDPOINT`，不直接接 ESP32 设备 WebSocket/MQTT 音频协议。
- 编排引擎当前保留扩展结构，首版重点是精确路由和治理闭环。
- Streamable HTTP 和 SSE connector 已隔离实现，复杂 SSE 事件读循环可在 `LegacySseConnector` 中继续增强。
- Postgres schema 已提供，核心测试默认使用内存仓库，方便快速验证业务逻辑。
- Redis 已纳入部署计划，当前限流和审批等待主要在进程内实现，后续可迁移到 Redis 以支持多副本。

## 相关项目

- xiaozhi-esp32: https://github.com/78/xiaozhi-esp32
- mcp-calculator: https://github.com/78/mcp-calculator
- MCP Specification: https://modelcontextprotocol.io/specification
