"""工具注册中心规则。

注册中心把下游 MCP server 的原始 tool 转换为 Hub 对上游暴露的统一工具目录：

- 默认 tool_id 为 `{namespace}.{origin_tool_name}`。
- 同名冲突时追加 `__{server_id}`。
- 统一兼容 `inputSchema`、`input_schema` 和缺失 annotations 的旧结构。
- 风险等级优先读取 annotations，缺失时按工具名和描述做保守推断。
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .domain import DownstreamServer, RiskLevel, ToolRecord

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9_.-]+")


def normalize_tool_name(name: str) -> str:
    normalized = _SAFE_NAME.sub("_", name.strip())
    normalized = normalized.strip("._-")
    return normalized or "unnamed_tool"


def infer_risk_level(tool: dict[str, Any]) -> RiskLevel:
    annotations = tool.get("annotations") or {}
    explicit = annotations.get("risk_level") or annotations.get("riskLevel")
    if explicit in {item.value for item in RiskLevel}:
        return RiskLevel(explicit)

    text = " ".join(
        str(part).lower()
        for part in [
            tool.get("name", ""),
            tool.get("description", ""),
            " ".join(map(str, annotations.values())),
        ]
    )
    critical_markers = ["payment", "pay", "unlock", "open door", "delete", "rm ", "format", "shutdown"]
    high_markers = ["email", "send", "write", "modify", "power", "batch", "file"]
    if any(marker in text for marker in critical_markers):
        return RiskLevel.CRITICAL
    if any(marker in text for marker in high_markers):
        return RiskLevel.HIGH
    return RiskLevel.LOW


def normalize_input_schema(tool: dict[str, Any]) -> dict[str, Any]:
    schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}}
    if "type" not in schema:
        return {"type": "object", **schema}
    return schema


def make_display_name(origin_name: str) -> str:
    tail = origin_name.split(".")[-1]
    return tail.replace("_", " ").replace("-", " ").title()


def build_tool_records(server: DownstreamServer, raw_tools: list[dict[str, Any]]) -> list[ToolRecord]:
    base_ids = [
        f"{normalize_tool_name(server.namespace)}.{normalize_tool_name(str(tool.get('name') or 'unnamed_tool'))}"
        for tool in raw_tools
    ]
    counts = Counter(base_ids)
    seen: Counter[str] = Counter()
    records: list[ToolRecord] = []

    for raw_tool, base_tool_id in zip(raw_tools, base_ids):
        seen[base_tool_id] += 1
        origin_name = normalize_tool_name(str(raw_tool.get("name") or "unnamed_tool"))
        tool_id = base_tool_id
        if counts[base_tool_id] > 1:
            suffix = normalize_tool_name(server.id)
            if seen[base_tool_id] > 1:
                suffix = f"{suffix}_{seen[base_tool_id]}"
            tool_id = f"{base_tool_id}__{suffix}"
        annotations = raw_tool.get("annotations") or {}
        if not isinstance(annotations, dict):
            annotations = {}
        tags = raw_tool.get("tags") or annotations.get("tags") or server.tags
        if not isinstance(tags, list):
            tags = [str(tags)]
        records.append(
            ToolRecord(
                tool_id=tool_id,
                display_name=str(raw_tool.get("display_name") or raw_tool.get("title") or make_display_name(origin_name)),
                server_id=server.id,
                origin_tool_name=origin_name,
                description=str(raw_tool.get("description") or ""),
                input_schema=normalize_input_schema(raw_tool),
                annotations=annotations,
                enabled=bool(raw_tool.get("enabled", True)),
                risk_level=infer_risk_level(raw_tool),
                tenant_id=server.tenant_id,
                device_scope=list(raw_tool.get("device_scope") or raw_tool.get("deviceScope") or []),
                tags=[str(tag) for tag in tags],
            )
        )
    return records


def reconcile_conflicts(existing: list[ToolRecord], incoming: list[ToolRecord]) -> list[ToolRecord]:
    occupied = {tool.tool_id for tool in existing if tool.server_id not in {item.server_id for item in incoming}}
    reconciled: list[ToolRecord] = []
    for tool in incoming:
        original = tool.tool_id
        if tool.tool_id in occupied:
            tool.tool_id = f"{tool.tool_id}__{normalize_tool_name(tool.server_id)}"
        counter = 2
        while tool.tool_id in occupied:
            tool.tool_id = f"{original}__{normalize_tool_name(tool.server_id)}_{counter}"
            counter += 1
        occupied.add(tool.tool_id)
        reconciled.append(tool)
    return reconciled


def to_mcp_tool(tool: ToolRecord) -> dict[str, Any]:
    return {
        "name": tool.tool_id,
        "description": tool.description,
        "inputSchema": tool.input_schema,
        "annotations": {
            **tool.annotations,
            "displayName": tool.display_name,
            "riskLevel": tool.risk_level.value,
            "serverId": tool.server_id,
            "originToolName": tool.origin_tool_name,
            "tags": tool.tags,
        },
    }
