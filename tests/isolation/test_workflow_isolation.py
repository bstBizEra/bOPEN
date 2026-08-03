"""MILE-4.2 workflow state engine — tenant isolation, integrity and append-only history, executed
against PostgreSQL.

Governed by DEC-P4-ENTRY §8, BOPEN-TENANT-001, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed SQL), R4 (adversarial negative probes), R5 (loud).

Every assertion runs real SQL against the live database with migration 013 applied. None would still
pass if the workflow isolation policies, the composite foreign key, or the append-only history
discipline were dropped: a definition/instance in one tenant is unreadable in another, an instance
of another tenant's definition is refused by the database, and a recorded transition cannot be
updated or deleted through any tenant session.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))


def _unavailable_reason() -> str | None:
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return "psycopg is not installed. Run: python -m pip install -r requirements.txt"
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set. Provision with `python tools/db_bootstrap.py --apply`."
    return None


class TestWorkflowEvidenceCanBeProduced(unittest.TestCase):
    """EBIV R5 — a check that cannot run reports failure, never silent success."""

    def test_workflow_isolation_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(reason, msg=f"Workflow isolation cannot be verified: {reason}")


@unittest.skipIf(_unavailable_reason() is not None, "database unavailable — reported by the guard test")
class TestWorkflowIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from platform_kernel import db
        from platform_kernel import workflow_repositories as workflow_repo

        cls.db = db
        cls.workflow_repo = workflow_repo

    def setUp(self):
        import psycopg

        self.psycopg = psycopg
        self.conn = self.db.connect(autocommit=True)
        self.tenant_a = str(uuid.uuid4())
        self.tenant_b = str(uuid.uuid4())
        with self.db.system_session(connection=self.conn) as cur:
            for tenant_id, name in ((self.tenant_a, "Tenant A"), (self.tenant_b, "Tenant B")):
                cur.execute(
                    "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                    (tenant_id, name),
                )

    def tearDown(self):
        self.conn.close()

    def _make_definition(self, tenant_id: str) -> str:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO workflow_definitions "
                "(tenant_id, name, initial_state, states, transitions) "
                "VALUES (%s, 'Approval', 'draft', %s::jsonb, %s::jsonb) RETURNING id",
                (
                    tenant_id,
                    json.dumps(["draft", "submitted", "approved"]),
                    json.dumps([["draft", "submitted"], ["submitted", "approved"]]),
                ),
            )
            return str(cur.fetchone()[0])

    def _make_instance(self, tenant_id: str, definition_id: str) -> str:
        with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO workflow_instances "
                "(tenant_id, definition_id, current_state, subject_ref) "
                "VALUES (%s, %s, 'draft', 'doc-1') RETURNING id",
                (tenant_id, definition_id),
            )
            return str(cur.fetchone()[0])

    # -- isolation ---------------------------------------------------------------------

    def test_a_definition_created_in_one_tenant_is_invisible_to_another(self):
        """INV-WF-TENANT-ISOLATION-01. Fails if tenant_isolation_workflow_definitions is dropped."""
        self._make_definition(self.tenant_a)
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM workflow_definitions")
            visible_to_b = cur.fetchone()[0]
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM workflow_definitions")
            visible_to_a = cur.fetchone()[0]
        self.assertEqual(visible_to_a, 1, "tenant A cannot see its own definition")
        self.assertEqual(visible_to_b, 0, "tenant B read tenant A's definition; isolation is off")

    def test_an_instance_created_in_one_tenant_is_invisible_to_another(self):
        """INV-WF-TENANT-ISOLATION-02. Fails if tenant_isolation_workflow_instances is dropped."""
        d = self._make_definition(self.tenant_a)
        self._make_instance(self.tenant_a, d)
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM workflow_instances")
            self.assertEqual(cur.fetchone()[0], 0, "tenant B read tenant A's instance")

    def test_a_cross_tenant_definition_insert_is_refused(self):
        """INV-WF-TENANT-WRITE-01. The WITH CHECK clause refuses writing another tenant's row."""
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO workflow_definitions "
                    "(tenant_id, name, initial_state, states, transitions) "
                    "VALUES (%s, 'X', 'draft', %s::jsonb, %s::jsonb)",
                    (self.tenant_a, json.dumps(["draft"]), json.dumps([])),
                )

    # -- integrity ---------------------------------------------------------------------

    def test_an_instance_of_another_tenants_definition_is_refused(self):
        """INV-WF-INSTANCE-DEF-SAME-TENANT-01. The composite FK to
        workflow_definitions(tenant_id, id) refuses an instance whose definition belongs to
        another tenant — even though the definition id is real."""
        d = self._make_definition(self.tenant_a)
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute(
                    "INSERT INTO workflow_instances "
                    "(tenant_id, definition_id, current_state, subject_ref) "
                    "VALUES (%s, %s, 'draft', 'smuggled')",
                    (self.tenant_b, d),
                )

    def test_recorded_history_cannot_be_updated_or_deleted(self):
        """INV-WF-HISTORY-APPEND-ONLY-01. workflow_history grants SELECT and INSERT only, so an
        UPDATE or DELETE reaches zero rows whatever SQL is issued — the same discipline as the
        audit trail. A transition, once recorded, is immutable."""
        d = self._make_definition(self.tenant_a)
        i = self._make_instance(self.tenant_a, d)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO workflow_history "
                "(tenant_id, instance_id, from_state, to_state) "
                "VALUES (%s, %s, 'draft', 'submitted')",
                (self.tenant_a, i),
            )
            cur.execute("UPDATE workflow_history SET to_state = 'tampered'")
            self.assertEqual(cur.rowcount, 0, "history row was updatable; it is not append-only")
            cur.execute("DELETE FROM workflow_history")
            self.assertEqual(cur.rowcount, 0, "history row was deletable; it is not append-only")
            cur.execute("SELECT to_state FROM workflow_history")
            self.assertEqual(cur.fetchone()[0], "submitted", "the recorded transition was altered")

    def test_recorded_history_survives_an_attempt_to_delete_its_instance(self):
        """INV-WF-HISTORY-APPEND-ONLY-02. The verifier's refutation of candidate a09022d: a direct
        DELETE on workflow_history reaches zero rows (no DELETE policy), but the instance foreign key
        was ON DELETE CASCADE, so deleting the parent instance erased the history through the
        referential path — which PostgreSQL performs with row security bypassed. Migration 014
        changed that key to ON DELETE RESTRICT. Deleting an instance that has recorded a transition
        is now refused, and the history is untouched. Fails if 014 is rolled back."""
        d = self._make_definition(self.tenant_a)
        i = self._make_instance(self.tenant_a, d)
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO workflow_history "
                "(tenant_id, instance_id, from_state, to_state) "
                "VALUES (%s, %s, 'draft', 'submitted')",
                (self.tenant_a, i),
            )
        # The cascade path the verifier exploited: deleting the parent instance must now be refused
        # by the RESTRICT, not silently cascade the history away.
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            with self.assertRaises(self.psycopg.errors.Error):
                cur.execute("DELETE FROM workflow_instances WHERE id = %s", (i,))
        # The history — and the instance — are still there.
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT to_state FROM workflow_history WHERE instance_id = %s", (i,))
            self.assertEqual(cur.fetchone()[0], "submitted", "the recorded transition was erased")

    # -- the state-machine invariant, through the repository ---------------------------

    def test_the_repository_refuses_a_disallowed_transition(self):
        """INV-WF-TRANSITION-ALLOWED-01. apply_transition refuses a move the definition does not
        list and leaves the instance where it was — this is what makes it a state machine."""
        repo = self.workflow_repo.WorkflowRepository()
        d = repo.create_definition(
            self.tenant_a,
            "Approval",
            "draft",
            ["draft", "submitted", "approved"],
            [["draft", "submitted"], ["submitted", "approved"]],
        )
        inst = repo.start_instance(self.tenant_a, d.id, "doc-1")
        # draft -> approved is not an edge.
        with self.assertRaises(self.workflow_repo.WorkflowTransitionError):
            repo.apply_transition(self.tenant_a, inst.id, "approved")
        # The instance did not move, and no history was written.
        self.assertEqual(repo.get_instance(self.tenant_a, inst.id).current_state, "draft")
        self.assertEqual(list(repo.list_history(self.tenant_a, inst.id)), [])
        # The allowed edge works and is recorded.
        moved = repo.apply_transition(self.tenant_a, inst.id, "submitted")
        self.assertEqual(moved.current_state, "submitted")
        self.assertEqual(len(list(repo.list_history(self.tenant_a, inst.id))), 1)


if __name__ == "__main__":
    unittest.main()
