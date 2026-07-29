import unittest
import uuid

class TestTenantIsolationPolicy(unittest.TestCase):
    """
    Automated negative unit test suite validating tenant isolation rules,
    context validation, and deny-by-default cross-tenant access.

    NOT ADMISSIBLE EVIDENCE FOR TENANT ISOLATION — recorded 2026-07-30.

    The fixture below is a Python list and the query function is a list comprehension. This
    suite therefore demonstrates that Python filtering works. It demonstrates nothing about
    the PostgreSQL Row-Level Security policies in `infrastructure/database/`, which govern
    the actual isolation invariant of BOPEN-TENANT-001.

    Under BOPEN-GOV-EBIV-001 R1 evidence for an infrastructure-enforced invariant must be
    produced by executing against that infrastructure. Admissible evidence for tenant
    isolation lives in `test_rls_database_behavior.py`.

    Retained rather than deleted, per AGENTS.md section 11: it is a valid unit test of the
    deny-by-default *shape* the application layer is expected to preserve, and removing it
    would erase the record of what was previously counted as isolation evidence. It is
    reclassified, not weakened.
    """

    def setUp(self):
        self.tenant_a_id = str(uuid.uuid4())
        self.tenant_b_id = str(uuid.uuid4())
        self.principal_id = str(uuid.uuid4())

        # Simulated in-memory database storage enforcing tenant_id filtering
        self.database = [
            {"id": "res-1", "tenant_id": self.tenant_a_id, "data": "Tenant A Confidential"},
            {"id": "res-2", "tenant_id": self.tenant_b_id, "data": "Tenant B Confidential"}
        ]

    def query_as_tenant(self, current_tenant_id: str):
        """Simulates executing a query under an active app.current_tenant_id RLS context"""
        if not current_tenant_id:
            return []  # Deny-by-default when no context set
        return [row for row in self.database if row["tenant_id"] == current_tenant_id]

    def test_tenant_a_cannot_see_tenant_b_data(self):
        """Negative Test: Tenant A querying data receives ONLY Tenant A rows"""
        results = self.query_as_tenant(self.tenant_a_id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["data"], "Tenant A Confidential")
        self.assertNotIn(self.tenant_b_id, [r["tenant_id"] for r in results])

    def test_empty_tenant_context_returns_nothing(self):
        """Negative Test: Querying with empty or missing tenant_id returns ZERO rows"""
        results = self.query_as_tenant("")
        self.assertEqual(len(results), 0)

    def test_tenant_b_isolation(self):
        """Negative Test: Tenant B querying receives ONLY Tenant B rows"""
        results = self.query_as_tenant(self.tenant_b_id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["data"], "Tenant B Confidential")

if __name__ == "__main__":
    unittest.main()
