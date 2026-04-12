from __future__ import annotations

import json
import sys
import time
from typing import Any


TOOLS = [
    {
        "name": "echo",
        "description": "Echo a short message back to the caller.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo."},
            },
            "required": ["message"],
        },
        "annotations": {"risk_level": "low", "tags": ["demo", "text"]},
    },
    {
        "name": "add",
        "description": "Add two numbers and return the result.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        },
        "annotations": {"risk_level": "low", "tags": ["demo", "math"]},
    },
    {
        "name": "get_server_status",
        "description": "Return a lightweight status payload for this demo MCP server.",
        "inputSchema": {"type": "object", "properties": {}},
        "annotations": {"risk_level": "low", "tags": ["demo", "status"]},
    },
]


def result_text(text: str, structured: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}], "isError": False}
    if structured is not None:
        result["structuredContent"] = structured
    return result


def handle(method: str, params: dict[str, Any]) -> dict[str, Any] | None:
    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion") or "2025-11-25",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "xiaozhi-hub-demo-downstream", "version": "0.1.0"},
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name == "echo":
            message = str(arguments.get("message", ""))
            return result_text(message, {"message": message})
        if name == "add":
            a = float(arguments.get("a", 0))
            b = float(arguments.get("b", 0))
            total = a + b
            return result_text(f"{a} + {b} = {total}", {"result": total})
        if name == "get_server_status":
            payload = {"status": "ok", "server": "demo", "time": int(time.time())}
            return result_text(json.dumps(payload, separators=(",", ":")), payload)
        raise ValueError(f"Unknown tool: {name}")
    raise ValueError(f"Unsupported method: {method}")


def write_response(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            request_id = request.get("id")
            result = handle(str(request.get("method") or ""), request.get("params") or {})
            if request_id is not None and result is not None:
                write_response({"jsonrpc": "2.0", "id": request_id, "result": result})
        except Exception as exc:
            request_id = request.get("id") if isinstance(locals().get("request"), dict) else None
            if request_id is not None:
                write_response({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}})
            else:
                print(f"demo server error: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
