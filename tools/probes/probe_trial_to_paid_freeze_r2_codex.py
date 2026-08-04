#!/usr/bin/env python3
"""Defensive re-probe of the trial-to-paid data-path freeze at candidate 6fdb8e9.

Uses the supported ``tenant_session(..., connection=...)`` form after verification and observes
whether the freeze refuses the write before cutover and cleanup. All objects are randomized and
removed in ``finally``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT))

CANDIDATE = "6fdb8e9fe32b087e7b617730a1e1eab6d452431e"
TREE = "48cf6aebb4b4d09eafb571af5badb0d9647e32f7"
EXPECTED_BLOBS = {
    "services/platform-kernel/python/platform_kernel/db.py":
        "9d035723cc72badafca9465a0b17b5943876b52c",
    "tools/migrate_tenant_to_dedicated.py":
        "65e173e33bb755a445b0e1d2e9b9700b90c2b3b6",
    "tests/isolation/test_trial_to_paid.py":
        "696f6771a733638f81f6568570da63816ceabab2",
    "docs/evidence/phase-3.5/invariant-traceability.csv":
        "9d342b7247a7571a9ad221847b529e0eb19cfc4b",
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
    require(bool(os.environ.get("BOPEN_ADMIN_DATABASE_URL", "").strip()), "BOPEN_ADMIN_DATABASE_URL required")


def sibling_url(url: str, database: str) -> str:
    return re.sub(r"/[^/?]+(\?|$)", rf"/{database}\1", url, count=1)


def main() -> int:
    load_env()
    require(git("rev-parse", f"{CANDIDATE}^{{commit}}") == CANDIDATE, "candidate mismatch")
    require(git("rev-parse", f"{CANDIDATE}^{{tree}}") == TREE, "tree mismatch")
    for path, expected in EXPECTED_BLOBS.items():
        require(git("rev-parse", f"{CANDIDATE}:{path}") == expected, f"blob mismatch: {path}")

    from platform_kernel import db
    from tools import migrate_tenant_to_dedicated as migrate
    from tools import provision_dedicated_db as provision

    control_url = os.environ["BOPEN_DATABASE_URL"]
    admin_url = os.environ["BOPEN_ADMIN_DATABASE_URL"]
    suffix = uuid.uuid4().hex[:10]
    tenant_id = str(uuid.uuid4())
    database = f"bopen_codex_t2p_r2_{suffix}"
    dedicated_url = sibling_url(control_url, database)
    ref = f"codext2pr2{suffix}"
    env_key = f"BOPEN_DEDICATED_DB__{ref}"
    original_verify = migrate._verify_counts
    late_write_id: str | None = None
    ordinary_path_refused = False
    supplied_connection_refused = False

    try:
        with db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, %s, 'active')",
                (tenant_id, f"Codex migration R2 {suffix}"),
            )
        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) "
                "VALUES (%s, 'organization', 'Before migration')",
                (tenant_id,),
            )

        def verify_then_observe_freeze(*args, **kwargs):
            nonlocal late_write_id, ordinary_path_refused, supplied_connection_refused
            original_verify(*args, **kwargs)

            try:
                with db.tenant_session(tenant_id):
                    pass
            except db.TenantMigratingError:
                ordinary_path_refused = True

            supplied = db.connect(control_url, autocommit=True)
            try:
                try:
                    with db.tenant_session(tenant_id, connection=supplied) as cur:
                        cur.execute(
                            "INSERT INTO parties (tenant_id, party_type, display_name) "
                            "VALUES (%s, 'organization', 'SUPPLIED CONNECTION LATE WRITE') RETURNING id",
                            (tenant_id,),
                        )
                        late_write_id = str(cur.fetchone()[0])
                except db.TenantMigratingError:
                    supplied_connection_refused = True
            finally:
                supplied.close()

        migrate._verify_counts = verify_then_observe_freeze
        migrate.migrate_tenant_to_dedicated(
            tenant_id=tenant_id,
            tenant_name=f"Codex migration R2 {suffix}",
            ref=ref,
            target_url=dedicated_url,
            admin_url=admin_url,
            control_url=control_url,
        )

        require(ordinary_path_refused, "connection-less tenant_session was not frozen")
        require(late_write_id is not None or supplied_connection_refused, "supplied path was not observed")

        admin_shared = provision._swap_database(admin_url, provision._database_name(control_url))
        admin_dedicated = provision._swap_database(admin_url, provision._database_name(dedicated_url))
        shared = db.connect(admin_shared, autocommit=True)
        dedicated = db.connect(admin_dedicated, autocommit=True)
        try:
            with shared.cursor() as cur:
                cur.execute("SELECT count(*) FROM parties WHERE id = %s", (late_write_id,))
                late_in_shared = cur.fetchone()[0]
            with dedicated.cursor() as cur:
                cur.execute("SELECT count(*) FROM parties WHERE id = %s", (late_write_id,))
                late_in_dedicated = cur.fetchone()[0]
        finally:
            dedicated.close()
            shared.close()

        observation = {
            "candidate": CANDIDATE,
            "tree": TREE,
            "connectionless_tenant_session_refused": ordinary_path_refused,
            "supplied_connection_tenant_session_refused": supplied_connection_refused,
            "late_write_id": late_write_id,
            "late_write_rows_shared_after_cleanup": late_in_shared,
            "late_write_rows_dedicated_after_cutover": late_in_dedicated,
        }
        print(json.dumps(observation, sort_keys=True))
        require(
            supplied_connection_refused,
            "FREEZE GAP: tenant_session(connection=...) accepted a write while migrating",
        )
        require(
            late_in_shared + late_in_dedicated == 1,
            "DATA LOSS: the supplied-connection write was removed from shared and absent from dedicated",
        )
        return 0
    finally:
        migrate._verify_counts = original_verify
        os.environ.pop(env_key, None)
        try:
            provision.drop_database(database, admin_url)
        except Exception:
            pass
        try:
            with db.system_session() as cur:
                cur.execute("DELETE FROM tenants WHERE id = %s", (tenant_id,))
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
