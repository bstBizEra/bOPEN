"""
Tenant isolation conformance executed against PostgreSQL.

Work package: BOPEN-P35-001 (WP-P35-01, deliverable D-04)
Governing artifacts: BOPEN-TENANT-001, AGENTS.md section 8 and section 14
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R4 (adversarial), R5 (fails loudly)

Every assertion here executes a real SQL statement against a real PostgreSQL instance with
the migrations in `infrastructure/database/` applied. Nothing in this file simulates a
policy, and no assertion would still pass if the policies were dropped. That is the
property that makes it admissible evidence for the isolation invariant, and it is the
property that `tests/isolation/test_tenant_isolation.py` lacks.

Running this suite:
    python tools/db_bootstrap.py --apply
    export BOPEN_DATABASE_URL="postgresql://bopen_app:<password>@127.0.0.1:5432/bopen_dev"
    python tools/run_tests.py

If BOPEN_DATABASE_URL is unset these tests FAIL. They do not skip. A skipped isolation
test and a passing isolation test look identical in a summary line, and that
indistinguishability is precisely how a kernel reaches three completed phases with its
primary security property never once executed.
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))

TENANT_SCOPED_TABLES = (
    "memberships",
    "tenant_resources",
    "active_contexts",
    "audit_events",
)


def _unavailable_reason() -> str | None:
    """Return why the suite cannot execute, or None when it can."""
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return (
            "psycopg is not installed. Run: python -m pip install -r requirements.txt"
        )
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return (
            "BOPEN_DATABASE_URL is not set. Provision a verification database with "
            "`python tools/db_bootstrap.py --apply` and export the URL it prints."
        )
    return None


class TestDatabaseAvailability(unittest.TestCase):
    """Guard test — fails loudly when isolation cannot be verified at all.

    BOPEN-GOV-EBIV-001 R5. This test exists so that an unconfigured environment produces a
    red suite rather than a green one with three silently skipped checks.
    """

    def test_isolation_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(
            reason,
            msg=(
                "Tenant isolation cannot be verified in this environment, so no admissible "
                f"evidence exists for it.\n\n{reason}\n\n"
                "This failure is intentional. Under BOPEN-GOV-EBIV-001 R5 a check that "
                "cannot run reports failure; it never reports success."
            ),
        )


@unittest.skipIf(
    _unavailable_reason() is not None,
    "database unavailable — reported as a failure by TestDatabaseAvailability",
)
class TestRowLevelSecurityBehavior(unittest.TestCase):
    """Adversarial probes against the live isolation policies."""

    @classmethod
    def setUpClass(cls):
        from platform_kernel import db

        cls.db = db

    def setUp(self):
        """Seed a fresh pair of tenants for each test on its own connection.

        Each test gets its own tenant and principal identifiers rather than sharing
        class-level ones, and its own connection rather than nesting transactions inside a
        shared outer one. The nested-transaction approach failed for a reason worth
        recording: when an assertion fired inside the outer context, cleanup raised
        `Explicit rollback() forbidden within a Transaction context` and every subsequent
        test errored with that instead of its own message. A suite whose real failure is
        buried under harness noise violates the same legibility rule (EBIV R5) that this
        file exists to enforce.

        Rows are therefore left committed in the verification database. That is acceptable
        because the instance is disposable and every identifier is unique per test, and it
        avoids a cleanup path that would need DELETE on the append-only audit table — which
        would mean weakening the very policy under test.
        """
        self.conn = self.db.connect(autocommit=True)
        self.tenant_a = str(uuid.uuid4())
        self.tenant_b = str(uuid.uuid4())
        self.principal_a = str(uuid.uuid4())
        self.principal_b = str(uuid.uuid4())

        with self.db.system_session(connection=self.conn) as cur:
            for tenant_id, name in (
                (self.tenant_a, "Tenant A"),
                (self.tenant_b, "Tenant B"),
            ):
                cur.execute(
                    "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                    (tenant_id, name),
                )
            for principal_id, email in (
                (self.principal_a, f"a-{self.principal_a[:8]}@example.invalid"),
                (self.principal_b, f"b-{self.principal_b[:8]}@example.invalid"),
            ):
                cur.execute(
                    "INSERT INTO principals (id, type, email) VALUES (%s, 'human', %s)",
                    (principal_id, email),
                )

        for tenant_id in (self.tenant_a, self.tenant_b):
            with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO tenant_resources (tenant_id, resource_name, payload) "
                    "VALUES (%s, %s, %s)",
                    (tenant_id, f"resource-of-{tenant_id[:8]}", "{}"),
                )

    def tearDown(self):
        self.conn.close()

    # -- A-01 ---------------------------------------------------------------------

    def test_tenant_cannot_read_another_tenants_rows(self):
        """A-01. Would fail if `tenant_isolation_resources` were dropped."""
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT tenant_id FROM tenant_resources")
            visible = {str(row[0]) for row in cur.fetchall()}

        self.assertIn(self.tenant_a, visible)
        self.assertNotIn(
            self.tenant_b,
            visible,
            "tenant A read a row belonging to tenant B; the isolation policy is not in "
            "force for this role",
        )

    def test_the_other_direction_also_holds(self):
        """A-01, reversed. Isolation that only works one way is not isolation."""
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT tenant_id FROM tenant_resources")
            visible = {str(row[0]) for row in cur.fetchall()}

        self.assertIn(self.tenant_b, visible)
        self.assertNotIn(self.tenant_a, visible)

    # -- A-02 ---------------------------------------------------------------------

    def test_unset_context_reads_nothing(self):
        """A-02. Deny-by-default: an absent tenant must not mean unrestricted access."""
        with self.db.system_session(connection=self.conn) as cur:
            for table in ("tenant_resources", "memberships"):
                cur.execute(f"SELECT count(*) FROM {table}")
                count = cur.fetchone()[0]
                self.assertEqual(
                    count,
                    0,
                    f"{table} returned {count} rows with no tenant context set; an unset "
                    f"context must read as no access",
                )

    def test_unknown_tenant_reads_nothing(self):
        """A-02. A syntactically valid but unknown tenant sees an empty database."""
        stranger = str(uuid.uuid4())
        with self.db.tenant_session(stranger, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM tenant_resources")
            self.assertEqual(cur.fetchone()[0], 0)

    # -- A-03 ---------------------------------------------------------------------

    def test_cross_tenant_insert_is_refused(self):
        """A-03. The write side is checked, not only the read side.

        A policy with only a USING clause hides other tenants' rows but can still permit
        writing a row stamped with another tenant's identifier. The WITH CHECK clause in
        migration 003 is what refuses it, and this probe is what proves the clause is live.
        """
        import psycopg

        # A WITH CHECK violation surfaces as InsufficientPrivilege (SQLSTATE 42501), not
        # CheckViolation (23514). The distinction is worth asserting precisely: 23514 would
        # mean an ordinary CHECK constraint refused the row, which is a different guarantee
        # and would leave the isolation policy untested. Catching a broad DatabaseError here
        # would let a typo in the statement pass as if isolation had held.
        with self.assertRaises(
            psycopg.errors.InsufficientPrivilege,
            msg="tenant A was allowed to insert a row owned by tenant B",
        ) as caught:
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO active_contexts "
                    "(tenant_id, principal_id, membership_id, correlation_id, expires_at) "
                    "VALUES (%s, %s, %s, %s, now() + interval '1 hour')",
                    (self.tenant_b, self.principal_b, str(uuid.uuid4()), "corr-probe"),
                )

        self.assertIn(
            "row-level security",
            str(caught.exception).lower(),
            "the write was refused, but not by the row-level security policy",
        )

    def test_cross_tenant_update_cannot_reach_foreign_rows(self):
        """A-03. UPDATE is constrained by the same visibility rule as SELECT."""
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "UPDATE tenant_resources SET resource_name = 'hijacked' "
                "WHERE tenant_id = %s",
                (self.tenant_b,),
            )
            self.assertEqual(
                cur.rowcount,
                0,
                "tenant A updated rows owned by tenant B",
            )

    # -- A-04 ---------------------------------------------------------------------

    def test_force_row_level_security_is_set_on_every_tenant_scoped_table(self):
        """A-04. ENABLE alone leaves the table owner unconstrained.

        Kernel services commonly connect as the table owner outside production. Without
        FORCE, every probe above would pass for a non-owner role and silently fail to
        protect the role actually in use.
        """
        with self.db.system_session(connection=self.conn) as cur:
            for table in TENANT_SCOPED_TABLES:
                enabled, forced = self.db.rls_is_active(cur, table)
                self.assertTrue(enabled, f"{table} does not have row level security enabled")
                self.assertTrue(forced, f"{table} does not FORCE row level security")

    # -- Append-only audit --------------------------------------------------------

    def test_audit_events_cannot_be_modified_or_deleted(self):
        """Audit is append-only by policy, not by convention.

        `audit_events` has SELECT and INSERT policies and deliberately no UPDATE or DELETE
        policy, so those commands can never reach an existing row.
        """
        membership_id = str(uuid.uuid4())
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO memberships (id, tenant_id, principal_id, state, role) "
                "VALUES (%s, %s, %s, 'active', 'owner')",
                (membership_id, self.tenant_a, self.principal_a),
            )
            cur.execute(
                "INSERT INTO audit_events "
                "(tenant_id, principal_id, correlation_id, event_type, action, "
                " resource_type, decision, reason_code) "
                "VALUES (%s, %s, 'corr-audit', 'authorization', 'read', "
                "        'tenant_resource', 'allow', 'ALLOW_OWNER')",
                (self.tenant_a, self.principal_a),
            )

            cur.execute("SELECT count(*) FROM audit_events")
            self.assertEqual(cur.fetchone()[0], 1)

            cur.execute("UPDATE audit_events SET action = 'tampered'")
            self.assertEqual(cur.rowcount, 0, "an audit record was modified")

            cur.execute("DELETE FROM audit_events")
            self.assertEqual(cur.rowcount, 0, "an audit record was deleted")

    # -- Database-enforced domain constraints -------------------------------------

    def test_context_window_must_be_ordered(self):
        """Migration 003 makes an already-expired context unrepresentable."""
        import psycopg

        membership_id = str(uuid.uuid4())
        with self.assertRaises(psycopg.errors.CheckViolation):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO memberships (id, tenant_id, principal_id, state, role) "
                    "VALUES (%s, %s, %s, 'active', 'owner')",
                    (membership_id, self.tenant_a, self.principal_a),
                )
                cur.execute(
                    "INSERT INTO active_contexts "
                    "(tenant_id, principal_id, membership_id, correlation_id, "
                    " established_at, expires_at) "
                    "VALUES (%s, %s, %s, 'corr-expired', now(), now() - interval '1 hour')",
                    (self.tenant_a, self.principal_a, membership_id),
                )

    def test_quota_reservation_rejects_non_positive_quantity(self):
        """The independent review recorded that the application accepted this. The
        database now refuses it regardless of which service writes the row."""
        import psycopg

        with self.assertRaises(psycopg.errors.CheckViolation):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO quota_reservations "
                    "(reservation_id, tenant_id, capability_id, reserved_quantity, "
                    " expires_at, status, correlation_id) "
                    "VALUES (%s, %s, 'cap_probe', 0, now() + interval '1 hour', "
                    "        'pending', 'corr-quota')",
                    (str(uuid.uuid4()), self.tenant_a),
                )

    def test_quota_reservation_rejects_expired_window(self):
        """Finding F-2: an already-expired reservation was accepted and could be
        committed. It is now rejected at write time."""
        import psycopg

        with self.assertRaises(psycopg.errors.CheckViolation):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO quota_reservations "
                    "(reservation_id, tenant_id, capability_id, reserved_quantity, "
                    " expires_at, status, correlation_id) "
                    "VALUES (%s, %s, 'cap_probe', 5, now() - interval '1 hour', "
                    "        'pending', 'corr-quota')",
                    (str(uuid.uuid4()), self.tenant_a),
                )

    def test_usage_cannot_exceed_entitled_quota(self):
        """Finding F-2: quota is now a database invariant, not an application check."""
        import psycopg

        with self.assertRaises(psycopg.errors.CheckViolation):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO usage_meter_balances "
                    "(balance_id, tenant_id, capability_id, used_quantity, quota_limit, "
                    " window_start, window_end) "
                    "VALUES (%s, %s, 'cap_probe', 101, 100, now(), "
                    "        now() + interval '30 days')",
                    (str(uuid.uuid4()), self.tenant_a),
                )


if __name__ == "__main__":
    unittest.main()
