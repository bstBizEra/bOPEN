#!/usr/bin/env python3
"""Independent destructive-safety probe for trial-to-paid migration candidate 2a253a5.

The probe injects an ordinary tenant-session write after verification and before cutover. A safe
freeze must refuse it. Candidate 2a253a5 accepts it and then deletes the only copy during cleanup.
The randomized tenant and database are removed in ``finally``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT))

CANDIDATE = "2a253a579eeb8c05273cca33f379006a700dc58c"
TREE = "3229e2cafc14530b8b060111958c71baa5d411cb"
EXPECTED_BLOBS = {
    "infrastructure/database/017_tenant_placement_state.sql":
        "3cfcf9ed6fb296538023a24d70e7bc8538ad443a",
    "tools/migrate_tenant_to_dedicated.py":
        "65e173e33bb755a445b0e1d2e9b9700b90c2b3b6",
    "services/platform-kernel/python/platform_kernel/api.py":
        "58aa9170965a5163cd41d291767d7d72c06da773",
    "tests/isolation/test_trial_to_paid.py":
        "5eb9578427e12ebb62fa5015410100975c999bec",
    "docs/evidence/phase-3.5/invariant-traceability.csv":
        "14cbb8f94fbac60bafe1bcd4191c223580b975bc",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def load_env() -> None:
    for raw in (ROOT / ".env.local").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip()
        if os.environ.get(name):
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[name] = value
    require(bool(os.environ.get("BOPEN_DATABASE_URL", "").strip()), "BOPEN_DATABASE_URL required")
    require(
        bool(os.environ.get("BOPEN_ADMIN_DATABASE_URL", "").strip()),
        "BOPEN_ADMIN_DATABASE_URL required",
    )


def sibling_url(url: str, database: str) -> str:
    return re.sub(r"/[^/?]+(\?|$)", rf"/{database}\1", url, count=1)


def table_rows(connection, table: str, tenant_id: str) -> list[str]:
    with connection.cursor() as cur:
        cur.execute(
            f"SELECT to_jsonb(t)::text FROM {table} AS t WHERE tenant_id = %s "
            "ORDER BY to_jsonb(t)::text",
            (tenant_id,),
        )
        return [row[0] for row in cur.fetchall()]


def main() -> int:
    load_env()
    require(git("rev-parse", f"{CANDIDATE}^{{commit}}") == CANDIDATE, "candidate mismatch")
    require(git("rev-parse", f"{CANDIDATE}^{{tree}}") == TREE, "tree mismatch")
    for path, expected in EXPECTED_BLOBS.items():
        require(git("rev-parse", f"{CANDIDATE}:{path}") == expected, f"blob mismatch: {path}")

    from platform_kernel import db, repositories as repo
    from tests.isolation import test_rls_database_behavior as rls_tests
    from tests.isolation import test_trial_to_paid as migration_tests
    from tools import migrate_tenant_to_dedicated as migrate
    from tools import provision_dedicated_db as provision

    control_url = os.environ["BOPEN_DATABASE_URL"]
    admin_url = os.environ["BOPEN_ADMIN_DATABASE_URL"]
    suffix = uuid.uuid4().hex[:10]
    tenant_id = str(uuid.uuid4())
    database = f"bopen_codex_t2p_{suffix}"
    dedicated_url = sibling_url(control_url, database)
    ref = f"codext2p{suffix}"
    env_key = f"BOPEN_DEDICATED_DB__{ref}"
    principal_id: str | None = None
    original_verify = migrate._verify_counts
    original_scoped = rls_tests.TENANT_SCOPED_TABLES
    late_write_id: str | None = None

    try:
        with db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                (tenant_id, f"Codex migration probe {suffix}"),
            )
        principal = repo.PrincipalRepository().create(
            email=f"codex-t2p-{suffix}@example.com"
        )
        principal_id = principal.id
        repo.MembershipRepository().create(
            tenant_id=tenant_id, principal_id=principal_id, role="owner", state="active"
        )
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) "
                "VALUES (%s, 'organization', 'Pre-freeze row') RETURNING id",
                (tenant_id,),
            )
            prefreeze_party_id = str(cur.fetchone()[0])
            cur.execute(
                "INSERT INTO exchange_rates (tenant_id, from_currency, to_currency, rate) "
                "VALUES (%s, 'USD', 'LAK', 21000.125)",
                (tenant_id,),
            )

        admin_shared_url = provision._swap_database(
            admin_url, provision._database_name(control_url)
        )
        shared_admin = db.connect(admin_shared_url, autocommit=True)
        try:
            snapshot = {
                table: table_rows(shared_admin, table, tenant_id) for table in migrate.COPY_ORDER
            }
        finally:
            shared_admin.close()

        def verify_then_write(*args, **kwargs):
            nonlocal late_write_id
            original_verify(*args, **kwargs)
            # This is the ordinary repository/session route, not a superuser bypass. Placement is
            # still shared_pool and tenant_session does not consult placement_state.
            with db.tenant_session(tenant_id) as cur:
                cur.execute(
                    "INSERT INTO parties (tenant_id, party_type, display_name) "
                    "VALUES (%s, 'organization', 'LATE WRITE AFTER VERIFY') RETURNING id",
                    (tenant_id,),
                )
                late_write_id = str(cur.fetchone()[0])

        migrate._verify_counts = verify_then_write
        migrate.migrate_tenant_to_dedicated(
            tenant_id=tenant_id,
            tenant_name=f"Codex migration probe {suffix}",
            ref=ref,
            target_url=dedicated_url,
            admin_url=admin_url,
            control_url=control_url,
        )
        require(late_write_id is not None, "late write was not injected")

        admin_dedicated_url = provision._swap_database(
            admin_url, provision._database_name(dedicated_url)
        )
        shared_admin = db.connect(admin_shared_url, autocommit=True)
        dedicated_admin = db.connect(admin_dedicated_url, autocommit=True)
        try:
            dedicated_rows = {
                table: table_rows(dedicated_admin, table, tenant_id)
                for table in migrate.COPY_ORDER
            }
            shared_counts = {
                table: len(table_rows(shared_admin, table, tenant_id))
                for table in migrate.COPY_ORDER
            }
            with shared_admin.cursor() as cur:
                cur.execute("SELECT count(*) FROM principals WHERE id = %s", (principal_id,))
                principal_in_control = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM parties WHERE id = %s", (late_write_id,))
                late_in_shared = cur.fetchone()[0]
            with dedicated_admin.cursor() as cur:
                cur.execute("SELECT count(*) FROM principals WHERE id = %s", (principal_id,))
                principal_in_dedicated = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM parties WHERE id = %s", (late_write_id,))
                late_in_dedicated = cur.fetchone()[0]
        finally:
            dedicated_admin.close()
            shared_admin.close()

        require(dedicated_rows == snapshot, "pre-freeze row content/IDs changed during COPY")
        require(all(count == 0 for count in shared_counts.values()), "shared cleanup incomplete")
        require(principal_in_control == 1 and principal_in_dedicated == 0, "principal moved")
        with db.tenant_session(tenant_id) as cur:
            cur.execute("SELECT count(*) FROM parties WHERE id = %s", (prefreeze_party_id,))
            require(cur.fetchone()[0] == 1, "cutover did not route to dedicated data")

        # Prove the future-table guard is sensitive: a classified table absent from COPY_ORDER must
        # make the named coverage test fail.
        rls_tests.TENANT_SCOPED_TABLES = original_scoped + ("codex_unmapped_table",)
        result = unittest.TestResult()
        migration_tests.TestCopyOrderCoverage(
            "test_copy_order_covers_every_tenant_scoped_table"
        ).run(result)
        require(len(result.failures) == 1 and not result.errors, "coverage mutation did not fail")

        observation = {
            "candidate": CANDIDATE,
            "tree": TREE,
            "traceability_inv_migrate_rows": len(
                [
                    line for line in git(
                        "show", f"{CANDIDATE}:docs/evidence/phase-3.5/invariant-traceability.csv"
                    ).splitlines()
                    if line.startswith("INV-MIGRATE-")
                ]
            ),
            "pre_snapshot_content_and_ids_preserved": True,
            "shared_counts_after_cleanup": shared_counts,
            "cutover_routes_prefreeze_id": True,
            "principal_control": principal_in_control,
            "principal_dedicated": principal_in_dedicated,
            "coverage_mutation_failed": True,
            "late_write_committed_while_migrating": late_write_id,
            "late_write_rows_shared_after_cleanup": late_in_shared,
            "late_write_rows_dedicated_after_cutover": late_in_dedicated,
            "verdict": "REFUTED_DATA_LOSS",
        }
        print(json.dumps(observation, sort_keys=True))
        # A committed row vanished from both databases: make the probe fail loudly.
        require(
            late_in_shared + late_in_dedicated == 1,
            "DATA LOSS: a tenant_session write committed after verification while placement_state "
            "was migrating, then cleanup removed it from shared while it was absent from dedicated",
        )
        return 0
    finally:
        migrate._verify_counts = original_verify
        rls_tests.TENANT_SCOPED_TABLES = original_scoped
        os.environ.pop(env_key, None)
        try:
            provision.drop_database(database, admin_url)
        except Exception:
            pass
        try:
            with db.system_session() as cur:
                cur.execute("DELETE FROM tenants WHERE id = %s", (tenant_id,))
                if principal_id:
                    cur.execute("DELETE FROM principals WHERE id = %s", (principal_id,))
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
