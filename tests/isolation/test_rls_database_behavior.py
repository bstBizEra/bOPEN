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
    # Migration 001 and 003 family — tenant_id is UUID with a foreign key.
    "memberships",
    "tenant_resources",
    "active_contexts",
    "audit_events",
    # Migration 002 family — tenant_id is VARCHAR(64) with no foreign key. Added 2026-07-30.
    # These five had row-level security enabled and forced since 002 and had never been
    # executed against by any test: the earlier tuple listed only the 001/003 family, so a
    # whole family of tenant-scoped tables sat outside the isolation suite while the phase
    # that created them was recorded as complete.
    "tenant_entitlement_plans",
    "tenant_entitlement_overrides",
    "usage_meter_balances",
    "quota_reservations",
    "usage_outbox",
    # Migrations 003, 005 and 006. Added 2026-07-30 by
    # `test_every_table_in_the_schema_is_classified_and_protected`, on the first run of that
    # test — it enumerates the live schema rather than this tuple, so it reported these four
    # as tables no assertion in this file had ever named. All four already had row security
    # enabled, forced and policied, so unlike the registry tables below they were never a
    # disclosure. They were simply outside the suite, which is the same condition `tenants`
    # and `principals` were in and is only harmless until it isn't.
    "lifecycle_events",
    "rate_limit_counters",
    "rate_limit_policies",
    "tenant_feature_toggles",
    # Migration 010 — MILE-4.1 party foundation. Tenant-scoped business entities (person /
    # organization) and their relationships, isolated by RLS from their first migration.
    "parties",
    "party_relationships",
    # Migration 012 — MILE-4.2 Money & Currency. A tenant's exchange rates, isolated by RLS.
    "exchange_rates",
    # Migration 013 — MILE-4.2 Workflow State Engine. Definitions, instances and append-only
    # history, all tenant-scoped by RLS.
    "workflow_definitions",
    "workflow_instances",
    "workflow_history",
)

# Registry tables define or precede the tenant boundary, so they carry no `tenant_id` and the
# usual policy is inexpressible on them. Migration 001 created both with no row security at
# all, and six migrations passed without anyone noticing, because every test in this file
# asserted against a table that already had a policy. Security review measured the result on
# 2026-07-30: a session scoped to one tenant read 7631 rows from `tenants` and 6657 principal
# email addresses, while correctly reading exactly 1 row from `tenant_resources`. Closed by
# migration 007.
REGISTRY_TABLES = (
    "tenants",
    "principals",
)

# Not tenant business data — properties of the database itself, structurally protected (ENABLE +
# FORCE row security). `schema_migrations` is readable only outside a tenant scope. `placement_
# identity` (migration 015) is a dedicated database's single-row declaration of the tenant it serves;
# it carries a tenant-matching policy (read by verify_connection_serves under the served tenant's
# scope) so the declaration is invisible to any other tenant's scope. It is classified here rather
# than as tenant-scoped because it is a singleton database property, not per-tenant business data.
INFRASTRUCTURE_TABLES = (
    "schema_migrations",
    "placement_identity",
)

# The 002 family stores tenant_id as text rather than UUID, so a repository writing to them
# needs the identifier as a string in canonical lowercase form.
TEXT_TENANT_TABLES = (
    "tenant_entitlement_plans",
    "tenant_entitlement_overrides",
    "usage_meter_balances",
    "quota_reservations",
    "usage_outbox",
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

    def test_the_append_only_guarantee_survives_its_documented_carve_outs(self):
        """
        `audit_events` is called append-only because it has SELECT and INSERT policies and no
        UPDATE or DELETE policy. That is true and `test_audit_events_cannot_be_modified_or_deleted`
        above asserts it — for the one path everybody tests.

        PostgreSQL documents three ways past a policy, and only that path was covered. The other
        two are asserted here:

          TRUNCATE   is not reachable by the application role, which holds no TRUNCATE privilege.
                     RLS is not what stops it, so the grant has to be asserted rather than assumed.
          FK actions are performed by the system and are not subject to row security.

        The second one was live. `audit_events.context_id` referenced `active_contexts`
        ON DELETE SET NULL, and `active_contexts` carried a FOR ALL policy, which grants DELETE.
        So a tenant could null the context binding on its own audit records from an ordinary
        session, using only the application role, with no write to `audit_events` at all —
        reproduced on 2026-07-30 and closed by migration 009.
        """
        import psycopg

        context_id = str(uuid.uuid4())
        membership_id = str(uuid.uuid4())
        correlation = f"carve-{uuid.uuid4().hex[:10]}"

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO memberships (id, tenant_id, principal_id, state, role) "
                "VALUES (%s, %s, %s, 'active', 'owner')",
                (membership_id, self.tenant_a, self.principal_a),
            )
            cur.execute(
                "INSERT INTO active_contexts (id, tenant_id, principal_id, membership_id, "
                " correlation_id, expires_at) "
                "VALUES (%s, %s, %s, %s, %s, now() + interval '5 min')",
                (context_id, self.tenant_a, self.principal_a, membership_id, correlation),
            )
            cur.execute(
                "INSERT INTO audit_events (tenant_id, principal_id, context_id, correlation_id, "
                " event_type, action, resource_type, decision, reason_code) "
                "VALUES (%s, %s, %s, %s, 'authorization', 'delete', 'tenant_resource', "
                "        'allow', 'ALLOW_OWNER')",
                (self.tenant_a, self.principal_a, context_id, correlation),
            )

        # Carve-out 1: TRUNCATE. Closed by privilege, not by policy.
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute("TRUNCATE audit_events")

        # Carve-out 2: a referential action reaching an audit row.
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("DELETE FROM active_contexts WHERE id = %s", (context_id,))
            self.assertEqual(
                cur.rowcount, 0,
                "a tenant deleted a context row; migration 009 removed the DELETE policy "
                "precisely because nothing needs it and it reached the audit trail",
            )

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "SELECT context_id FROM audit_events WHERE correlation_id = %s", (correlation,)
            )
            self.assertEqual(
                str(cur.fetchone()[0]), context_id,
                "the context binding was erased from an audit record without any write to the "
                "audit table",
            )

    def test_an_audit_record_outlives_the_context_it_names(self):
        """
        The reason migration 009 dropped the foreign key rather than only the DELETE policy.

        A context lives five minutes. Something must eventually reap expired ones, and under
        ON DELETE SET NULL that job would strip `context_id` from every audit row referencing
        what it reaped — no attack, just housekeeping destroying evidence while passing every
        test. So the audit row keeps the identifier and carries no referential action.

        The reaper is simulated here with an administrative delete, because no such job exists
        yet; the point is that the trail is already safe for one to be written.

        This is deliberately the opposite of F10's reasoning, which prices the absence of a
        foreign key at 6,537 orphaned metering rows. A metering row's tenant names a live
        relationship and an orphan there is a defect. An audit row's context names something that
        happened, and the referent is expected to disappear.
        """
        import os
        import re

        import psycopg

        admin_url = os.environ.get("BOPEN_ADMIN_DATABASE_URL", "").strip()
        if not admin_url:
            self.skipTest("BOPEN_ADMIN_DATABASE_URL is not set; cannot simulate a reaper")
        target = re.sub(r"/[^/?]+(\?|$)", r"/bopen_dev\1", admin_url)

        context_id = str(uuid.uuid4())
        membership_id = str(uuid.uuid4())
        correlation = f"reap-{uuid.uuid4().hex[:10]}"

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO memberships (id, tenant_id, principal_id, state, role) "
                "VALUES (%s, %s, %s, 'active', 'owner')",
                (membership_id, self.tenant_a, self.principal_a),
            )
            cur.execute(
                "INSERT INTO active_contexts (id, tenant_id, principal_id, membership_id, "
                " correlation_id, expires_at) "
                "VALUES (%s, %s, %s, %s, %s, now() + interval '5 min')",
                (context_id, self.tenant_a, self.principal_a, membership_id, correlation),
            )
            cur.execute(
                "INSERT INTO audit_events (tenant_id, principal_id, context_id, correlation_id, "
                " event_type, action, resource_type, decision, reason_code) "
                "VALUES (%s, %s, %s, %s, 'authorization', 'read', 'tenant_resource', "
                "        'allow', 'ALLOW_OWNER')",
                (self.tenant_a, self.principal_a, context_id, correlation),
            )

        with psycopg.connect(target, autocommit=True) as conn:
            with conn.cursor() as cur:
                # `chk_context_window` forbids inserting an already-expired context, so the
                # reaper is simulated by deleting the row rather than by ageing it. The point
                # under test is the deletion, not the criterion a real reaper would use.
                cur.execute("DELETE FROM active_contexts WHERE id = %s", (context_id,))
                self.assertEqual(cur.rowcount, 1, "the simulated reaper deleted nothing")

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "SELECT context_id FROM audit_events WHERE correlation_id = %s", (correlation,)
            )
            self.assertEqual(
                str(cur.fetchone()[0]), context_id,
                "reaping an expired context erased its identifier from the audit trail",
            )

    def test_a_context_is_retired_by_revocation_and_not_by_deletion(self):
        """
        Removing DELETE must not have removed the operation the code actually performs.
        `repositories.py` revokes by UPDATE on `revoked_at`; that path has to keep working, or
        this migration traded an evidence defect for an outage.
        """
        context_id = str(uuid.uuid4())
        membership_id = str(uuid.uuid4())

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO memberships (id, tenant_id, principal_id, state, role) "
                "VALUES (%s, %s, %s, 'active', 'owner')",
                (membership_id, self.tenant_a, self.principal_a),
            )
            cur.execute(
                "INSERT INTO active_contexts (id, tenant_id, principal_id, membership_id, "
                " correlation_id, expires_at) "
                "VALUES (%s, %s, %s, %s, 'corr-revoke', now() + interval '5 min')",
                (context_id, self.tenant_a, self.principal_a, membership_id),
            )
            cur.execute(
                "UPDATE active_contexts SET revoked_at = now() WHERE id = %s", (context_id,)
            )
            self.assertEqual(cur.rowcount, 1, "revocation by UPDATE stopped working")

            cur.execute("SELECT revoked_at FROM active_contexts WHERE id = %s", (context_id,))
            self.assertIsNotNone(cur.fetchone()[0])

    def test_a_tenant_cannot_move_a_context_to_another_tenant(self):
        """
        A tenant cannot move its context row to another tenant.

        This asserts the behaviour, not the syntax that produces it. An earlier version of this
        docstring credited the explicit WITH CHECK on the UPDATE policy; that is wrong, and
        mutation testing showed it — removing WITH CHECK leaves this test green, because
        PostgreSQL supplies an identical one when it is omitted. The guarantee comes from the
        policy existing at all. Both clauses are still written out in migration 009 so that a
        future edit to the read-side expression cannot silently change the write-side.
        """
        context_id = str(uuid.uuid4())
        membership_id = str(uuid.uuid4())

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO memberships (id, tenant_id, principal_id, state, role) "
                "VALUES (%s, %s, %s, 'active', 'owner')",
                (membership_id, self.tenant_a, self.principal_a),
            )
            cur.execute(
                "INSERT INTO active_contexts (id, tenant_id, principal_id, membership_id, "
                " correlation_id, expires_at) "
                "VALUES (%s, %s, %s, %s, 'corr-move', now() + interval '5 min')",
                (context_id, self.tenant_a, self.principal_a, membership_id),
            )

        import psycopg

        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "UPDATE active_contexts SET tenant_id = %s WHERE id = %s",
                    (self.tenant_b, context_id),
                )

    # -- Session nesting: the leak a security review found --------------------------

    def test_a_session_cannot_be_nested_inside_one_scoped_to_another_tenant(self):
        """Regression for a complete isolation bypass, found 2026-07-30 and reproduced.

        `set_config(..., is_local => true)` is discarded when its transaction ends. But
        psycopg's `conn.transaction()`, entered on a connection already inside a transaction,
        emits a SAVEPOINT — and PostgreSQL reverts `SET LOCAL` on savepoint ROLLBACK but **not**
        on savepoint RELEASE.

        So a nested session that exited *cleanly* left the inner tenant in force. Measured before
        the guard: an outer block scoped to B read zero rows, a nested block for A exited
        normally, and the same outer block then read A's row and wrote a row owned by A. Row-level
        security was fully enabled the whole time; it was simply being told the wrong tenant.

        The inner-raises path was always correct, because savepoint rollback does revert the
        setting. Only the clean exit leaked, which is exactly why no existing test caught it —
        every test that nested sessions either did not nest across tenants or raised.
        """
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as _cur:
            with self.assertRaises(self.db.TenantScopeReentryError) as caught:
                with self.db.tenant_session(self.tenant_b, connection=self.conn):
                    pass

        self.assertIn(self.tenant_b, str(caught.exception))
        self.assertIn(self.tenant_a, str(caught.exception))

    def test_re_entry_with_the_same_tenant_is_permitted(self):
        """Composing several same-tenant statements on one connection is the reason
        `connection=` exists, and it cannot produce a scope mismatch. Refusing it would push
        callers toward opening extra connections, which is a worse outcome than the bug."""
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as outer:
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as inner:
                inner.execute("SELECT count(*) FROM tenant_resources")
                self.assertGreaterEqual(inner.fetchone()[0], 1)

            outer.execute("SELECT NULLIF(current_setting('app.current_tenant_id', true), '')")
            self.assertEqual(outer.fetchone()[0], self.tenant_a, "the outer scope was altered")

    def test_a_system_session_cannot_be_nested_inside_a_tenant_session(self):
        """This direction fails closed rather than open — the setting is cleared, so the
        enclosing block sees nothing and reads it as 'this tenant has no data'.

        It is refused anyway. A correctness bug that presents as missing data is the failure
        mode migration 004 was written to remove, and a rule with an exception is a rule
        somebody has to remember.
        """
        with self.db.tenant_session(self.tenant_a, connection=self.conn):
            with self.assertRaises(self.db.TenantScopeReentryError):
                with self.db.system_session(connection=self.conn):
                    pass

    def test_a_tenant_session_cannot_be_nested_inside_a_system_session(self):
        """This direction fails open: the tenant would stay in force and the enclosing block
        would read that tenant's rows while believing it was unscoped."""
        with self.db.system_session(connection=self.conn):
            with self.assertRaises(self.db.TenantScopeReentryError):
                with self.db.tenant_session(self.tenant_a, connection=self.conn):
                    pass

    # -- Tenant identity agreement across the two policy families ------------------

    def test_both_policy_families_agree_on_tenant_identity_regardless_of_case(self):
        """Regression for the defect migration 004 closes. Fails if 004 is rolled back.

        Migration 002 compared tenant identity as case-sensitive TEXT while 001 and 003 compared
        it as UUID, which normalises case. Migration 003's shape constraint used `~*`, so
        mixed-case UUID text was admissible in the first place.

        Measured before 004, with one identifier stored uppercase: the lowercase context saw 0
        rows in the 002 family and 1 row in the 003 family, in the same session, with no error.
        The same tenant could not see its own entitlements while seeing its own resources.

        That mattered more than a missing row: `FeatureRolloutEvaluator.is_feature_enabled`
        returns True when it finds no toggle, so a tenant whose toggle rows were invisible was
        granted every feature. A silent read-path isolation defect became an entitlement
        fail-open.
        """
        lower = self.tenant_a.lower()
        upper = self.tenant_a.upper()
        self.assertNotEqual(lower, upper, "fixture identifier has no letters to change case on")

        with self.db.tenant_session(lower, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO tenant_entitlement_plans (tenant_id, plan_id) VALUES (%s, %s)",
                (lower, "plan_free"),
            )

        with self.db.tenant_session(lower, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM tenant_entitlement_plans")
            seen_lower = cur.fetchone()[0]

        with self.db.tenant_session(upper, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM tenant_entitlement_plans")
            seen_upper = cur.fetchone()[0]

        self.assertEqual(seen_lower, 1, "the tenant cannot see its own entitlement row")
        self.assertEqual(
            seen_upper,
            seen_lower,
            "the two policy families disagree on tenant identity: the same tenant sees a "
            "different number of rows depending only on the case of its identifier",
        )

    def test_a_non_canonical_tenant_identifier_cannot_be_stored(self):
        """Migration 004 §3 tightened the shape constraint from `~*` to `~`.

        Case normalisation at write time is defence in depth rather than the primary control —
        the policies no longer care about case. It keeps the column canonical so the eventual
        conversion to a real UUID column is a pure cast with no data cleanup.
        """
        import psycopg

        with self.assertRaises(psycopg.errors.CheckViolation):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO tenant_entitlement_plans (tenant_id, plan_id) VALUES (%s, %s)",
                    (self.tenant_a.upper(), "plan_free"),
                )

    def test_the_002_family_refuses_a_cross_tenant_write(self):
        """Migration 002 omitted WITH CHECK and relied on PostgreSQL defaulting it to USING.

        That default holds, but it is implicit: an edit to the read-side expression alone would
        silently remove the write-side constraint. Migration 004 states both clauses explicitly
        on all five policies, and this probe is what would notice if either were lost.
        """
        import psycopg

        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO tenant_entitlement_plans (tenant_id, plan_id) VALUES (%s, %s)",
                    (self.tenant_b, "plan_free"),
                )

    def test_the_002_family_is_scoped_on_read(self):
        """Tenant A must not read tenant B's entitlement rows.

        These tables carried policies from migration 002 onward and no test had ever executed
        one of them.
        """
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO tenant_entitlement_plans (tenant_id, plan_id) VALUES (%s, %s)",
                (self.tenant_a, "plan_free"),
            )
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO tenant_entitlement_plans (tenant_id, plan_id) VALUES (%s, %s)",
                (self.tenant_b, "plan_pro"),
            )

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT tenant_id FROM tenant_entitlement_plans")
            visible = {row[0] for row in cur.fetchall()}

        self.assertIn(self.tenant_a, visible)
        self.assertNotIn(
            self.tenant_b, visible, "tenant A read tenant B's entitlement plan"
        )

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


class TestRegistryTableIsolation(unittest.TestCase):
    """
    The registry tables — the ones that had no policy at all until migration 007.

    `tenants` and `principals` carry no `tenant_id`, so `tenant_id = current_tenant` cannot be
    written for them. Migration 001 took inexpressible to mean inapplicable and left both
    world-readable to every tenant on the deployment. These probes are written against the
    measured disclosure rather than against the policy text.
    """

    @classmethod
    def setUpClass(cls):
        from platform_kernel import db

        cls.db = db

    def setUp(self):
        self.conn = self.db.connect(autocommit=True)
        self.tenant_a = str(uuid.uuid4())
        self.tenant_b = str(uuid.uuid4())
        self.principal_a = str(uuid.uuid4())
        self.principal_b = str(uuid.uuid4())

        with self.db.system_session(connection=self.conn) as cur:
            for tenant_id, name in ((self.tenant_a, "Registry A"), (self.tenant_b, "Registry B")):
                cur.execute(
                    "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                    (tenant_id, name),
                )
            for principal_id in (self.principal_a, self.principal_b):
                cur.execute(
                    "INSERT INTO principals (id, type, email) VALUES (%s, 'human', %s)",
                    (principal_id, f"reg-{principal_id[:8]}@example.com"),
                )
        # Each principal is a member of its own tenant only. The principals policy is defined
        # in terms of membership, so without this the table would read as empty for the wrong
        # reason and the probes below would pass vacuously.
        for tenant_id, principal_id in (
            (self.tenant_a, self.principal_a),
            (self.tenant_b, self.principal_b),
        ):
            with self.db.tenant_session(tenant_id, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO memberships (tenant_id, principal_id, state, role) "
                    "VALUES (%s, %s, 'active', 'owner')",
                    (tenant_id, principal_id),
                )

    def tearDown(self):
        self.conn.close()

    def test_a_tenant_cannot_enumerate_the_customer_list(self):
        """The disclosure as measured: 7631 tenant rows visible from inside one tenant."""
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT id FROM tenants")
            visible = {str(row[0]) for row in cur.fetchall()}

        self.assertEqual(
            visible, {self.tenant_a},
            "a tenant session read tenant rows other than its own; the deployment's customer "
            "list is readable by any tenant on it",
        )

    def test_a_tenant_cannot_read_another_tenants_people(self):
        """`principals.email` is the column this protects. It is every user's address."""
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT id FROM principals")
            visible = {str(row[0]) for row in cur.fetchall()}

        self.assertIn(self.principal_a, visible, "a tenant cannot see its own member")
        self.assertNotIn(
            self.principal_b, visible,
            "a tenant session read a principal belonging to another tenant",
        )

    def test_the_other_direction_also_holds(self):
        with self.db.tenant_session(self.tenant_b, connection=self.conn) as cur:
            cur.execute("SELECT id FROM tenants")
            self.assertEqual({str(r[0]) for r in cur.fetchall()}, {self.tenant_b})
            cur.execute("SELECT id FROM principals")
            self.assertNotIn(self.principal_a, {str(r[0]) for r in cur.fetchall()})

    def test_a_tenant_cannot_lift_its_own_suspension(self):
        """
        The reason reads and writes are separate policies rather than one `FOR ALL`.

        `FOR ALL` with a single `USING` reuses that expression as the `WITH CHECK`, so the
        read permission granted above would have carried UPDATE with it — on the table whose
        `status` column holds 'suspended' and 'terminated'.

        RLS denies this silently: the row falls outside the UPDATE policy's `USING`, so it is
        not visible to the statement and the result is zero rows affected rather than an
        error. The status assertion is therefore the real one; `rowcount` alone would also be
        satisfied by a statement that matched nothing for an unrelated reason.
        """
        with self.db.system_session(connection=self.conn) as cur:
            cur.execute("UPDATE tenants SET status = 'suspended' WHERE id = %s", (self.tenant_a,))

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("UPDATE tenants SET status = 'active' WHERE id = %s", (self.tenant_a,))
            self.assertEqual(cur.rowcount, 0)

        with self.db.system_session(connection=self.conn) as cur:
            cur.execute("SELECT status FROM tenants WHERE id = %s", (self.tenant_a,))
            self.assertEqual(
                cur.fetchone()[0], "suspended",
                "a tenant reactivated itself; suspension is not enforceable",
            )

    def test_a_tenant_cannot_rename_another_tenant(self):
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("UPDATE tenants SET name = 'seized' WHERE id = %s", (self.tenant_b,))
            self.assertEqual(cur.rowcount, 0)
        with self.db.system_session(connection=self.conn) as cur:
            cur.execute("SELECT name FROM tenants WHERE id = %s", (self.tenant_b,))
            self.assertEqual(cur.fetchone()[0], "Registry B")

    def test_a_tenant_cannot_insert_a_registry_row(self):
        """Provisioning is an unscoped operation. A tenant session must not be able to do it."""
        import psycopg

        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO principals (id, type, email) VALUES (%s, 'human', %s)",
                    (str(uuid.uuid4()), f"smuggled-{uuid.uuid4().hex[:8]}@example.com"),
                )

    def test_provisioning_through_an_unscoped_session_still_works(self):
        """
        The failure mode opposite to the one being fixed. A policy that closed the disclosure
        by also blocking tenant creation would take the kernel from leaking to unusable, and
        every probe above would still pass.
        """
        tenant_id = str(uuid.uuid4())
        with self.db.system_session(connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, 'Provisioned', 'active')",
                (tenant_id,),
            )
            cur.execute("SELECT name FROM tenants WHERE id = %s", (tenant_id,))
            self.assertEqual(cur.fetchone()[0], "Provisioned")

    def test_the_migration_ledger_is_not_readable_from_a_tenant_scope(self):
        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM schema_migrations")
            self.assertEqual(cur.fetchone()[0], 0)
        with self.db.system_session(connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM schema_migrations")
            self.assertGreater(cur.fetchone()[0], 0, "the ledger is unreadable to the kernel too")

    def test_referential_integrity_still_holds_against_rows_the_session_cannot_see(self):
        """
        PostgreSQL evaluates foreign-key checks with row security bypassed, deliberately, so
        that a policy cannot be used to corrupt data. This asserts that property directly,
        because migration 007 depends on it: `memberships.principal_id` references a table the
        session can now only partly read, and if the check were subject to the policy, valid
        writes would start failing as integrity violations.

        The same behaviour is a covert channel — the two outcomes below differ, so existence
        is observable without read access. That is a documented PostgreSQL limitation, it is
        recorded in migration 007, and it is asserted here so it stays a known property rather
        than becoming a surprise.
        """
        import psycopg

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute("SELECT count(*) FROM principals WHERE id = %s", (self.principal_b,))
            self.assertEqual(cur.fetchone()[0], 0, "precondition: B's principal must be hidden")

        with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
            cur.execute(
                "INSERT INTO memberships (tenant_id, principal_id, state, role) "
                "VALUES (%s, %s, 'active', 'member')",
                (self.tenant_a, self.principal_b),
            )
            self.assertEqual(cur.rowcount, 1)

        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            with self.db.tenant_session(self.tenant_a, connection=self.conn) as cur:
                cur.execute(
                    "INSERT INTO memberships (tenant_id, principal_id, state, role) "
                    "VALUES (%s, %s, 'active', 'member')",
                    (self.tenant_a, str(uuid.uuid4())),
                )

    def test_every_table_in_the_schema_is_classified_and_protected(self):
        """
        The structural check, and the one that matters most in this class.

        Every other probe here tests a policy that exists. What let `tenants` and `principals`
        sit open through six migrations was that no test asserted anything about a table with
        no policy — absence was invisible. This enumerates the live schema instead of a list,
        so a new table added without row security fails here rather than being discovered by
        the next security review.

        A table that belongs in none of the three classes is a failure too, not a pass: the
        point is that somebody has to decide which it is.
        """
        classified = set(TENANT_SCOPED_TABLES) | set(REGISTRY_TABLES) | set(INFRASTRUCTURE_TABLES)

        with self.db.system_session(connection=self.conn) as cur:
            cur.execute(
                "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity "
                "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = current_schema() AND c.relkind = 'r'"
            )
            live = {name: (enabled, forced) for name, enabled, forced in cur.fetchall()}

        unclassified = sorted(set(live) - classified)
        self.assertEqual(
            unclassified, [],
            f"tables exist that this suite has never classified: {unclassified}. Add each to "
            f"TENANT_SCOPED_TABLES, REGISTRY_TABLES or INFRASTRUCTURE_TABLES and give it a "
            f"policy. This assertion is what would have caught the 007 disclosure in 001.",
        )

        missing = sorted(t for t in classified if t in live and not all(live[t]))
        self.assertEqual(
            missing, [],
            f"tables without ENABLE and FORCE row level security: {missing}",
        )

        stale = sorted(classified - set(live))
        self.assertEqual(stale, [], f"this suite names tables that no longer exist: {stale}")


if __name__ == "__main__":
    unittest.main()
