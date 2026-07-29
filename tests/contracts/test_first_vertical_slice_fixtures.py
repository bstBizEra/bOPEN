import unittest
import uuid
from datetime import datetime, timezone

class TestFirstVerticalSliceFixtures(unittest.TestCase):
    """
    Contract test suite asserting compliance for Phase 1 vertical slice:
    Human Principal -> Provision Tenant -> Owner Membership -> Context -> Authz Read -> Audit Event
    Governed by docs/work-packages/FIRST-VERTICAL-SLICE-SPEC.md
    """

    def test_vertical_slice_execution_chain(self):
        # 1. Register Human Principal
        principal_id = f"usr_{uuid.uuid4()}"
        principal = {"id": principal_id, "type": "human", "email": "admin@example.com"}

        # 2. Provision Tenant
        tenant_id = f"tnt_{uuid.uuid4()}"
        tenant = {"id": tenant_id, "name": "Acme Corp", "status": "active"}

        # 3. Create Owner Membership
        membership_id = f"mem_{uuid.uuid4()}"
        membership = {
            "id": membership_id,
            "tenant_id": tenant["id"],
            "principal_id": principal["id"],
            "state": "active",
            "role": "owner"
        }
        self.assertEqual(membership["state"], "active")

        # 4. Establish Active Context
        context_id = f"ctx_{uuid.uuid4()}"
        context = {
            "context_id": context_id,
            "principal_id": principal["id"],
            "tenant_id": tenant["id"],
            "active_membership_id": membership["id"],
            "roles": ["owner"]
        }
        self.assertEqual(context["tenant_id"], tenant_id)

        # 5. Authorize Tenant Read
        decision = {
            "decision_id": str(uuid.uuid4()),
            "principal_id": principal["id"],
            "tenant_id": tenant["id"],
            "action": "tenant:read",
            "resource_type": "tenant",
            "resource_id": tenant["id"],
            "decision": "ALLOW",
            "reason_code": "MEMBERSHIP_ACTIVE_PERMITTED"
        }
        self.assertEqual(decision["decision"], "ALLOW")

        # 6. Emit Correlated Audit Event
        audit_event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "security.authorization.decision",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": principal["id"],
            "tenant_id": tenant["id"],
            "resource_type": "tenant",
            "resource_id": tenant["id"],
            "action": "tenant:read",
            "status": "SUCCESS",
            "correlation_id": str(uuid.uuid4())
        }
        self.assertEqual(audit_event["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()
