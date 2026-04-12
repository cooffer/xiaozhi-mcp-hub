import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.acl import AccessControlService
from app.approvals import ApprovalService
from app.audit import AuditService
from app.connectors.base import ConnectorResponse
from app.domain import DownstreamServer, ToolRecord, TransportType
from app.mcp_hub import McpHub
from app.store import InMemoryStore


class FakeConnectors:
    async def call_tool(self, server, origin_tool_name, arguments):
        return ConnectorResponse(content=[{"type": "text", "text": f"{origin_tool_name}:{arguments['value']}"}])


class McpHubTests(unittest.IsolatedAsyncioTestCase):
    async def test_lists_and_calls_registered_tool(self):
        store = InMemoryStore()
        await store.upsert_server(DownstreamServer(id="calc", transport=TransportType.STDIO, namespace="calc"))
        await store.upsert_tool(ToolRecord(tool_id="calc.add", display_name="Add", server_id="calc", origin_tool_name="add"))
        hub = McpHub(
            store,
            FakeConnectors(),
            AccessControlService(store),
            ApprovalService(store, wait_seconds=1),
            AuditService(store),
        )

        listed = await hub.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        called = await hub.handle(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "calc.add", "arguments": {"value": 3}}}
        )

        self.assertEqual(listed["result"]["tools"][0]["name"], "hub.status")
        self.assertEqual(listed["result"]["tools"][1]["name"], "calc.add")
        self.assertEqual(called["result"]["content"][0]["text"], "add:3")

    async def test_builtin_status_tool_is_available_without_downstream_tools(self):
        store = InMemoryStore()
        hub = McpHub(
            store,
            FakeConnectors(),
            AccessControlService(store),
            ApprovalService(store, wait_seconds=1),
            AuditService(store),
        )

        listed = await hub.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        called = await hub.handle(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "hub.status", "arguments": {}}}
        )

        self.assertEqual(listed["result"]["tools"][0]["name"], "hub.status")
        self.assertIn("Xiaozhi MCP Hub is connected", called["result"]["content"][0]["text"])
        self.assertFalse(called["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
