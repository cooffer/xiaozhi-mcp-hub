"""观测指标的集中定义。

Prometheus Counter/Histogram 需要在进程内保持单例，否则测试或热重载时
容易因为重复注册同名 metric 出错。API 路由和中间件都从这里引用同一份指标。
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

REQUESTS = Counter("xiaozhi_mcp_hub_requests_total", "API requests", ["path"])
MCP_CALLS = Counter("xiaozhi_mcp_hub_mcp_calls_total", "MCP calls", ["method", "status"])
MCP_LATENCY = Histogram("xiaozhi_mcp_hub_mcp_latency_seconds", "MCP call latency")

