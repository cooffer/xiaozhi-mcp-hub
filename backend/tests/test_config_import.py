import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config_import import import_config
from app.registry import build_tool_records
from app.store import InMemoryStore


class FakeConnectors:
    def __init__(self, store):
        self.store = store
        self.reloaded = []

    async def reload_server(self, server):
        self.reloaded.append(server.id)

    async def discover_server(self, server):
        if server.id == "broken":
            raise RuntimeError("boom")
        raw_tools = [{"name": "echo", "description": "Echo", "inputSchema": {"type": "object", "properties": {}}}]
        await self.store.replace_tools_for_server(server.id, build_tool_records(server, raw_tools))
        return raw_tools


class ConfigImportTests(unittest.IsolatedAsyncioTestCase):
    async def test_imports_native_servers_and_discovers_tools(self):
        store = InMemoryStore()
        connectors = FakeConnectors(store)

        result = await import_config(
            {
                "servers": [
                    {
                        "id": "demo",
                        "transport": "stdio",
                        "command": "python",
                        "args": ["demo.py"],
                        "namespace": "demo",
                    }
                ]
            },
            store,
            connectors,
        )

        tools = await store.list_tools()
        self.assertEqual(result["servers"], 1)
        self.assertEqual(result["tools"], 1)
        self.assertEqual(tools[0].tool_id, "demo.echo")

    async def test_imports_common_mcp_servers_format(self):
        store = InMemoryStore()
        connectors = FakeConnectors(store)

        result = await import_config(
            {
                "mcpServers": {
                    "demo": {"command": "python", "args": ["demo.py"]},
                    "remote": {"type": "streamable_http", "url": "https://example.com/mcp"},
                }
            },
            store,
            connectors,
        )

        servers = await store.list_servers()
        self.assertEqual(result["servers"], 2)
        self.assertEqual(result["tools"], 2)
        self.assertEqual({server.id for server in servers}, {"demo", "remote"})
        self.assertEqual(next(server for server in servers if server.id == "remote").endpoint, "https://example.com/mcp")

    async def test_discovery_errors_do_not_abort_import(self):
        store = InMemoryStore()
        connectors = FakeConnectors(store)

        result = await import_config({"servers": [{"id": "broken", "transport": "stdio", "command": "python", "namespace": "broken"}]}, store, connectors)

        self.assertEqual(result["servers"], 1)
        self.assertEqual(result["tools"], 0)
        self.assertEqual(result["errors"], {"broken": "boom"})


if __name__ == "__main__":
    unittest.main()
