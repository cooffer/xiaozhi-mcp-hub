from __future__ import annotations

from .domain import ToolCallContext, ToolRecord, UserRole
from .store import InMemoryStore


class AccessControlService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    async def can_list_tool(self, tool: ToolRecord, context: ToolCallContext) -> bool:
        if not tool.enabled or tool.tenant_id != context.tenant_id:
            return False
        if context.actor_role == UserRole.ADMIN:
            return True
        return await self.can_call_tool(tool, context)

    async def can_call_tool(self, tool: ToolRecord, context: ToolCallContext) -> bool:
        if not tool.enabled or tool.tenant_id != context.tenant_id:
            return False
        if context.actor_role == UserRole.ADMIN:
            return True
        if tool.device_scope and context.device_id not in tool.device_scope:
            return False

        rules = await self.store.list_acl_for_tool(tool.tool_id)
        if not rules:
            return context.actor_role == UserRole.OPERATOR

        for rule in rules:
            if rule.tenant_id != context.tenant_id:
                continue
            if context.actor_role not in rule.roles:
                continue
            if rule.upstream_ids and context.upstream_id not in rule.upstream_ids:
                continue
            if rule.device_scope and context.device_id not in rule.device_scope:
                continue
            return True
        return False

