#!/usr/bin/env python3
"""Migrate an existing shared-pool tenant into a dedicated database — WP-P35-06 trial→paid.

Governing artifacts: DEC-P35-TENANCY-MODEL §12; PLAN-P35-06-TRIAL-TO-PAID.

There is no ACID transaction across two databases, so the guarantee is by sequencing:

    freeze → prepare → copy → verify → cutover → cleanup

  - freeze   : mark the tenant `migrating` in the control registry; the kernel then refuses its
               requests (`api._load_validated_context`), so no write lands in the shared pool after
               the snapshot.
  - prepare  : stand up the dedicated database WITHOUT flipping the control registry (the tenant still
               serves from the shared pool).
  - copy     : binary COPY each tenant-scoped table's rows from the shared pool into the dedicated
               database, under the tenant's scope (row-level security yields exactly its rows). Binary
               COPY preserves every type — ids, timestamps, JSONB — exactly, so ids stay stable and
               intra-tenant references hold. Principals are NOT copied: they are global and stay in
               control.
  - verify   : per table, the dedicated row count for the tenant equals the shared count.
  - cutover  : ONE row update in the control database (atomic there) flips `placement_kind` to
               `dedicated`, sets `placement_ref`, and clears `migrating`. Before it, reads resolve to
               the shared pool; after, to the dedicated database. No split-brain instant.
  - cleanup  : delete the tenant's now-stale rows from the shared pool. Uses the superuser, because
               the append-only tables (audit_events, workflow_history, lifecycle_events) have no
               DELETE policy for the application role — this is a controlled migration move (the rows
               are already copied and verified into the dedicated database, where their append-only
               property is intact), not an application-reachable deletion.

Failure before cutover leaves the tenant fully on the shared pool, untouched; the half-built dedicated
database is discardable. Failure of cleanup after cutover leaves only unread stale rows in the shared
pool — recoverable, not loss.

Retained utility (Rule 13): deployment/migration. The freeze makes it safe against concurrent writes;
run it as an operator action.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "platform-kernel" / "python"))

import db_bootstrap  # noqa: E402
import provision_dedicated_db as prov  # noqa: E402
from platform_kernel import db  # noqa: E402

# Every tenant-scoped table, in foreign-key dependency order (parents before children), so a binary
# COPY into the dedicated database never violates an intra-database foreign key. Kept as an ordered
# constant here and asserted equal to the live schema's tenant-scoped set by
# `test_trial_to_paid.test_copy_order_covers_every_tenant_scoped_table`, so a tenant-scoped table
# added later without being added here fails loudly rather than being silently left behind — the
# enumerate-don't-miss discipline, because a missed table is silent data loss.
COPY_ORDER = (
    # No intra-set parents.
    "memberships",
    "tenant_resources",
    "active_contexts",
    "audit_events",
    "tenant_entitlement_plans",
    "tenant_entitlement_overrides",
    "usage_meter_balances",
    "quota_reservations",
    "usage_outbox",
    "lifecycle_events",
    "rate_limit_policies",
    "rate_limit_counters",
    "tenant_feature_toggles",
    "exchange_rates",
    "uom_custom_units",
    # Parents before children.
    "parties",
    # Migration 019 — Party ContactPoint extension. party_contact_points references parties; its
    # verification-events table references party_contact_points. Parents before children.
    "party_contact_points",
    "party_contact_point_verification_events",
    "party_relationships",
    "workflow_definitions",
    "workflow_instances",
    "workflow_history",
)


@dataclass(frozen=True)
class MigrationResult:
    tenant_id: str
    ref: str
    per_table_rows: dict


def _admin_control_conn(admin_url: str, control_url: str):
    """A superuser connection to the control database. Placement changes to the tenant registry are
    system operations: under a tenant scope the registry policies (migration 007) refuse a tenant
    modifying its own placement row, so the flip would be a silent no-op. The superuser bypasses RLS,
    which is correct here — the migration is an operator action on the registry, not tenant self-service."""
    admin_control = prov._swap_database(admin_url, prov._database_name(control_url))
    return db.connect(admin_control, autocommit=True)


def _set_migrating(admin_url: str, control_url: str, tenant_id: str, migrating: bool) -> None:
    """Set (or clear) the freeze flag on the control registry row (as superuser)."""
    conn = _admin_control_conn(admin_url, control_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tenants SET placement_state = %s WHERE id = %s",
                ("migrating" if migrating else "stable", tenant_id),
            )
    finally:
        conn.close()


def _admin_conns(admin_url: str, shared_url: str, dedicated_url: str):
    """Superuser connections to the shared and dedicated databases.

    The copy runs as the superuser rather than under a tenant session for a concrete reason:
    PostgreSQL refuses `COPY FROM` on a table with row-level security ("COPY FROM not supported with
    row-level security"). The superuser bypasses RLS, so `COPY FROM` works; the tenant scope RLS
    would otherwise provide is supplied explicitly by a `WHERE tenant_id = <tenant>` on the source
    query, which is exact and visible rather than implicit.
    """
    admin_shared = prov._swap_database(admin_url, prov._database_name(shared_url))
    admin_dedicated = prov._swap_database(admin_url, prov._database_name(dedicated_url))
    return db.connect(admin_shared, autocommit=False), db.connect(admin_dedicated, autocommit=False)


def _copy_all_tables(shared_url: str, dedicated_url: str, tenant_id: str, admin_url: str) -> dict:
    """Binary-COPY every tenant-scoped table's rows for this tenant, shared → dedicated, as superuser
    with an explicit tenant filter. Binary COPY preserves every type (ids, timestamps, JSONB)."""
    counts: dict = {}
    shared_conn, ded_conn = _admin_conns(admin_url, shared_url, dedicated_url)
    try:
        with shared_conn.cursor() as scur, ded_conn.cursor() as dcur:
            for table in COPY_ORDER:
                with scur.copy(
                    f"COPY (SELECT * FROM {table} WHERE tenant_id = %s) TO STDOUT (FORMAT BINARY)",
                    (tenant_id,),
                ) as out:
                    with dcur.copy(f"COPY {table} FROM STDIN (FORMAT BINARY)") as inp:
                        for block in out:
                            inp.write(block)
                dcur.execute(f"SELECT count(*) FROM {table} WHERE tenant_id = %s", (tenant_id,))
                counts[table] = dcur.fetchone()[0]
        ded_conn.commit()
    finally:
        ded_conn.close()
        shared_conn.close()
    return counts


def _verify_counts(shared_url: str, dedicated_url: str, tenant_id: str, expected: dict, admin_url: str) -> None:
    """Per table, the dedicated count for the tenant must equal the shared count. Refuse otherwise."""
    shared_conn, ded_conn = _admin_conns(admin_url, shared_url, dedicated_url)
    try:
        with shared_conn.cursor() as scur, ded_conn.cursor() as dcur:
            for table in COPY_ORDER:
                scur.execute(f"SELECT count(*) FROM {table} WHERE tenant_id = %s", (tenant_id,))
                shared_n = scur.fetchone()[0]
                dcur.execute(f"SELECT count(*) FROM {table} WHERE tenant_id = %s", (tenant_id,))
                ded_n = dcur.fetchone()[0]
                if shared_n != ded_n:
                    raise RuntimeError(
                        f"verification failed for {table}: shared has {shared_n} rows, dedicated "
                        f"has {ded_n}. Refusing to cut over — the tenant stays on the shared pool."
                    )
    finally:
        ded_conn.close()
        shared_conn.close()


def _cutover(admin_url: str, control_url: str, tenant_id: str, ref: str) -> None:
    """The one atomic instant: flip the control registry to dedicated and clear the freeze (as
    superuser — a placement change is a system operation on the registry, see _admin_control_conn)."""
    conn = _admin_control_conn(admin_url, control_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tenants SET placement_kind = 'dedicated', placement_ref = %s, "
                "placement_state = 'stable' WHERE id = %s",
                (ref, tenant_id),
            )
    finally:
        conn.close()


def _cleanup_shared(admin_url: str, shared_url: str, tenant_id: str) -> None:
    """Delete the tenant's now-stale rows from the shared pool, children first.

    Uses the superuser connection to the shared database: the append-only tables have no DELETE
    policy for the application role, and this is a controlled post-cutover move of rows already
    copied and verified into the dedicated database.
    """
    shared_db = prov._database_name(shared_url)
    admin_shared = prov._swap_database(admin_url, shared_db)
    conn = db.connect(admin_shared, autocommit=True)
    try:
        with conn.cursor() as cur:
            for table in reversed(COPY_ORDER):
                cur.execute(f"DELETE FROM {table} WHERE tenant_id = %s", (tenant_id,))
    finally:
        conn.close()


def migrate_tenant_to_dedicated(
    *,
    tenant_id: str,
    tenant_name: str,
    ref: str,
    target_url: str,
    admin_url: str,
    control_url: str,
) -> MigrationResult:
    """Move `tenant_id` from the shared pool to its own dedicated database. See the module docstring."""
    # freeze
    _set_migrating(admin_url, control_url, tenant_id, True)
    try:
        # prepare — stand up the dedicated DB, do NOT flip the control registry yet
        prov.provision_dedicated_database(
            tenant_id=tenant_id, tenant_name=tenant_name, ref=ref,
            target_url=target_url, admin_url=admin_url, control_url=control_url, activate=False,
        )
        # copy + verify
        counts = _copy_all_tables(control_url, target_url, tenant_id, admin_url)
        _verify_counts(control_url, target_url, tenant_id, counts, admin_url)
    except BaseException:
        # Anything before cutover: leave the tenant on the shared pool, clear the freeze.
        _set_migrating(admin_url, control_url, tenant_id, False)
        raise
    # cutover (also clears the freeze) then cleanup. Set the dedicated connection in the environment
    # BEFORE the flip so a resolve immediately after cutover can route to it.
    os.environ[f"BOPEN_DEDICATED_DB__{ref}"] = target_url
    _cutover(admin_url, control_url, tenant_id, ref)
    _cleanup_shared(admin_url, control_url, tenant_id)
    return MigrationResult(tenant_id=tenant_id, ref=ref, per_table_rows=counts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--tenant-name", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--target-url", required=True, help="app-role URL of the dedicated database")
    parser.add_argument("--admin-url", default=os.environ.get(db_bootstrap.ENV_ADMIN_URL, ""))
    parser.add_argument("--control-url", default=os.environ.get(db_bootstrap.ENV_APP_URL, ""))
    args = parser.parse_args()
    if not args.admin_url or not args.control_url:
        print("ERROR: admin and control URLs are required", file=sys.stderr)
        return 2
    result = migrate_tenant_to_dedicated(
        tenant_id=args.tenant_id, tenant_name=args.tenant_name, ref=args.ref,
        target_url=args.target_url, admin_url=args.admin_url, control_url=args.control_url,
    )
    print(f"Migrated tenant {result.tenant_id} to dedicated database (ref {result.ref}).")
    print(f"Rows moved per table: {result.per_table_rows}")
    print(f'Export:  BOPEN_DEDICATED_DB__{result.ref}="{args.target_url}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
