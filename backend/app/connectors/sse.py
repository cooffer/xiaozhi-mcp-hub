from __future__ import annotations

from ..domain import DownstreamServer
from .http import StreamableHttpConnector


class LegacySseConnector(StreamableHttpConnector):
    """Compatibility path for old HTTP+SSE MCP servers.

    Many old deployments expose a proxy endpoint that still accepts JSON-RPC
    POSTs next to SSE events. For servers requiring a full SSE read loop, this
    class is the isolated place to extend without touching hub routing.
    """

    def __init__(self, server: DownstreamServer, secrets: dict[str, str] | None = None) -> None:
        super().__init__(server, secrets)
