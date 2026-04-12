import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain import DownstreamServer, TransportType
from app.registry import build_tool_records, normalize_input_schema


class RegistryTests(unittest.TestCase):
    def test_builds_namespaced_tool_ids_and_conflict_suffixes(self):
        server = DownstreamServer(id="ha-prod", transport=TransportType.STDIO, namespace="home")
        records = build_tool_records(
            server,
            [
                {"name": "turn_on_light", "description": "Turn on"},
                {"name": "turn_on_light", "description": "Turn on duplicate"},
            ],
        )

        self.assertEqual(records[0].tool_id, "home.turn_on_light__ha-prod")
        self.assertEqual(records[1].tool_id, "home.turn_on_light__ha-prod_2")
        self.assertEqual(records[0].origin_tool_name, "turn_on_light")

    def test_normalizes_legacy_input_schema(self):
        schema = normalize_input_schema({"input_schema": {"properties": {"x": {"type": "number"}}}})
        self.assertEqual(schema["type"], "object")
        self.assertIn("x", schema["properties"])


if __name__ == "__main__":
    unittest.main()

