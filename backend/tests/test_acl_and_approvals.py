import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.acl import AccessControlService
from app.approvals import ApprovalService
from app.domain import ApprovalStatus, RiskLevel, ToolCallContext, ToolRecord, UserRole
from app.store import InMemoryStore


class AclAndApprovalTests(unittest.IsolatedAsyncioTestCase):
    async def test_operator_can_call_enabled_tool_by_default(self):
        store = InMemoryStore()
        acl = AccessControlService(store)
        tool = ToolRecord(tool_id="home.status", display_name="Status", server_id="ha", origin_tool_name="status")
        context = ToolCallContext(actor_role=UserRole.OPERATOR)

        self.assertTrue(await acl.can_call_tool(tool, context))

    async def test_viewer_cannot_call_without_acl(self):
        store = InMemoryStore()
        acl = AccessControlService(store)
        tool = ToolRecord(tool_id="home.status", display_name="Status", server_id="ha", origin_tool_name="status")
        context = ToolCallContext(actor_role=UserRole.VIEWER)

        self.assertFalse(await acl.can_call_tool(tool, context))

    async def test_approval_can_be_resolved_by_admin(self):
        store = InMemoryStore()
        approvals = ApprovalService(store, wait_seconds=2)
        tool = ToolRecord(
            tool_id="home.unlock",
            display_name="Unlock",
            server_id="ha",
            origin_tool_name="unlock",
            risk_level=RiskLevel.HIGH,
        )
        context = ToolCallContext(actor_role=UserRole.OPERATOR)

        waiter = asyncio.create_task(approvals.request_and_wait(tool, {"door": "front"}, context))
        await asyncio.sleep(0)
        pending = await store.list_approvals(status="pending")
        await approvals.approve(pending[0].id, actor_id="admin")
        result = await waiter

        self.assertEqual(result.status, ApprovalStatus.APPROVED)


if __name__ == "__main__":
    unittest.main()

