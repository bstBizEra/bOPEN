#!/usr/bin/env python3
"""Independent defensive probe for WP-P35-06 dedicated placement candidate d8dd023.

Creates a randomized second PostgreSQL database, exercises physical placement and the
fail-closed routes, then removes only the randomized records/database it created.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT))

EXPECTED_COMMIT = "d8dd023d237191d2c042269ae058b503f4ffaebf"
EXPECTED_TREE = "2fdc86855d0e663fe54ed4549ecb5f10245de0e2"
EXPECTED_MIGRATION = "3d4f230c43f35fc5db3dbc6b9d9346a448c8dffc"


def git_oid(spec: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", spec], cwd=ROOT, text=True
    ).strip()


def sibling_url(url: str, database: str) -> str:
    return re.sub(r"/[^/?]+(\?|$)", rf"/{database}\1", url, count=1)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(git_oid(f"{EXPECTED_COMMIT}^{{commit}}") == EXPECTED_COMMIT, "candidate commit mismatch")
    require(git_oid(f"{EXPECTED_COMMIT}^{{tree}}") == EXPECTED_TREE, "candidate tree mismatch")
    require(
        git_oid(f"{EXPECTED_COMMIT}:infrastructure/database/015_placement_identity.sql")
        == EXPECTED_MIGRATION,
        "candidate migration blob mismatch",
    )

    control_url = os.environ.get("BOPEN_DATABASE_URL", "").strip()
    admin_url = os.environ.get("BOPEN_ADMIN_DATABASE_URL", "").strip()
    require(bool(control_url), "BOPEN_DATABASE_URL is required")
    require(bool(admin_url), "BOPEN_ADMIN_DATABASE_URL is required")

    import psycopg

    from platform_kernel import db, placement
    from tools import provision_dedicated_db as provision

    suffix = uuid.uuid4().hex[:10]
    database = f"bopen_codex_dedi_{suffix}"
    dedicated_url = sibling_url(control_url, database)
    owner = str(uuid.uuid4())
    other = str(uuid.uuid4())
    lonely = str(uuid.uuid4())
    shared = str(uuid.uuid4())
    owner_ref = f"codex{suffix}"
    other_ref = f"wrong{suffix}"
    lonely_ref = f"unset{suffix}"
    owner_key = f"{placement.DEDICATED_ENV_PREFIX}{owner_ref}"
    other_key = f"{placement.DEDICATED_ENV_PREFIX}{other_ref}"
    created_tenants = [owner, other, lonely, shared]

    try:
        provision.provision_dedicated_database(
            tenant_id=owner,
            tenant_name="Codex Dedicated Probe",
            ref=owner_ref,
            target_url=dedicated_url,
            admin_url=admin_url,
            control_url=control_url,
        )
        os.environ[owner_key] = dedicated_url

        with db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status) VALUES (%s, 'Codex Shared Probe', 'active')",
                (shared,),
            )

        with db.tenant_session(owner) as cur:
            cur.execute(
                "INSERT INTO parties (tenant_id, party_type, display_name) "
                "VALUES (%s, 'organization', 'Codex Physical Placement') RETURNING id",
                (owner,),
            )
            party_id = str(cur.fetchone()[0])

        conn = db.connect(dedicated_url, autocommit=True)
        try:
            with db.tenant_session(owner, connection=conn) as cur:
                cur.execute("SELECT tenant_id FROM placement_identity")
                require([str(row[0]) for row in cur.fetchall()] == [owner], "owner cannot read identity")
                cur.execute("SELECT count(*) FROM parties WHERE id = %s", (party_id,))
                require(cur.fetchone()[0] == 1, "routed write absent from dedicated database")

            with db.tenant_session(other, connection=conn) as cur:
                cur.execute("SELECT count(*) FROM placement_identity")
                require(cur.fetchone()[0] == 0, "other tenant scope exposed placement identity")

            with db.system_session(connection=conn) as cur:
                cur.execute("SELECT count(*) FROM placement_identity")
                require(cur.fetchone()[0] == 0, "unset tenant scope exposed placement identity")

            singleton_refused = False
            try:
                with db.tenant_session(owner, connection=conn) as cur:
                    cur.execute("INSERT INTO placement_identity (tenant_id) VALUES (%s)", (owner,))
            except psycopg.errors.UniqueViolation:
                singleton_refused = True
            require(singleton_refused, "second placement identity was not refused by singleton key")
        finally:
            conn.close()

        control_conn = db.connect(control_url, autocommit=True)
        try:
            with db.tenant_session(owner, connection=control_conn) as cur:
                cur.execute("SELECT count(*) FROM parties WHERE id = %s", (party_id,))
                require(cur.fetchone()[0] == 0, "dedicated write was present in shared pool")
        finally:
            control_conn.close()

        with db.tenant_session(shared) as cur:
            cur.execute("SELECT count(*) FROM parties WHERE id = %s", (party_id,))
            require(cur.fetchone()[0] == 0, "shared tenant reached dedicated row")

        with db.system_session() as cur:
            cur.execute(
                "INSERT INTO tenants (id, name, status, placement_kind, placement_ref) "
                "VALUES (%s, 'Codex Misroute Probe', 'active', 'dedicated', %s), "
                "(%s, 'Codex Unconfigured Probe', 'active', 'dedicated', %s)",
                (other, other_ref, lonely, lonely_ref),
            )
        os.environ[other_key] = dedicated_url

        misroute_refused = False
        try:
            with db.tenant_session(other):
                pass
        except placement.PlacementUnresolved:
            misroute_refused = True
        require(misroute_refused, "misrouted tenant was not refused")

        unconfigured_refused = False
        try:
            with db.tenant_session(lonely):
                pass
        except placement.PlacementUnresolved:
            unconfigured_refused = True
        require(unconfigured_refused, "unconfigured dedicated tenant fell through")

        print("PASS candidate/tree/blob bound")
        print("PASS owner identity visible; other and unset scopes see zero rows")
        print("PASS second identity refused by singleton key")
        print("PASS routed write is dedicated-only and unreachable from shared placement")
        print("PASS misrouted and unconfigured dedicated tenants refused")
        return 0
    finally:
        os.environ.pop(owner_key, None)
        os.environ.pop(other_key, None)
        try:
            with db.system_session() as cur:
                cur.execute("DELETE FROM tenants WHERE id = ANY(%s)", (created_tenants,))
        except Exception:
            pass
        try:
            provision.drop_database(database, admin_url)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
