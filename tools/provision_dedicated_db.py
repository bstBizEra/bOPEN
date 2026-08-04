#!/usr/bin/env python3
"""Provision a dedicated database for a paying/production tenant — WP-P35-06 (Option D).

Governing artifacts: DEC-P35-TENANCY-MODEL §8, §10; PLAN-P35-06-DEDICATED-DB.

A dedicated database is the **same schema as the shared pool, single-tenant**. This tool:

  1. creates the target database (idempotent);
  2. applies the **full migration ledger** to it, as the admin role, granting DML to the app role —
     the identical applier the shared pool uses (`db_bootstrap.apply_ledger_to`), so a dedicated
     database is never a schema variant;
  3. marks the tenant `dedicated` in the **control** registry (the routing authority
     `resolve_placement` reads);
  4. seeds the dedicated database's single `tenants` row and its `placement_identity` declaration,
     so `verify_connection_serves` can confirm the database serves exactly this tenant.

The dedicated database's connection URL is never written to any table: the seam keeps that secret in
`BOPEN_DEDICATED_DB__<ref>` in the environment. This tool prints the line to export.

Usage:
    python tools/provision_dedicated_db.py \\
        --tenant-id <uuid> --tenant-name "Acme" --ref acme \\
        --target-url postgresql://bopen_app:<pw>@127.0.0.1:5433/bopen_dedi_acme \\
        --admin-url  postgresql://postgres:<pw>@127.0.0.1:5433/postgres \\
        --control-url postgresql://bopen_app:<pw>@127.0.0.1:5433/bopen_dev

Retained utility (Rule 13): deployment/provisioning class. Non-destructive to existing data; refuses
to apply onto a database whose migration ledger diverges from this tree (AGENTS.md §14, via the
applier). Safe and idempotent to re-run.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Import the shared applier and primitives from the sibling bootstrap tool.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import db_bootstrap  # noqa: E402


def _database_name(url: str) -> str:
    m = re.search(r"/([^/?]+)(\?|$)", url)
    if not m:
        raise ValueError(f"cannot read a database name from {url!r}")
    return m.group(1)


def _swap_database(url: str, database: str) -> str:
    return re.sub(r"/[^/?]+(\?|$)", f"/{database}\\1", url, count=1)


def _create_database(database: str, admin_url: str) -> None:
    """Create the target database if it does not exist. CREATE DATABASE cannot run in a transaction."""
    psycopg = db_bootstrap.require_psycopg()
    from psycopg import sql

    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
            # If it already exists, the applier below reconciles it idempotently, or refuses on a
            # divergent ledger. We do not drop it here — this tool never destroys data implicitly.


def drop_database(database: str, admin_url: str) -> None:
    """Terminate connections and drop the database. For teardown of a provisioned dedicated DB."""
    psycopg = db_bootstrap.require_psycopg()
    from psycopg import sql

    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (database,),
            )
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database)))


def _seed_control_registry(control_url: str, tenant_id: str, tenant_name: str, ref: str) -> None:
    """Mark the tenant dedicated in the control registry — the row resolve_placement reads to route."""
    psycopg = db_bootstrap.require_psycopg()
    with psycopg.connect(control_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            # System scope (no tenant), the way the registry is written elsewhere.
            cur.execute("SELECT set_config('app.current_tenant_id', '', true)")
            cur.execute(
                "INSERT INTO tenants (id, name, status, placement_kind, placement_ref) "
                "VALUES (%s, %s, 'active', 'dedicated', %s) "
                "ON CONFLICT (id) DO UPDATE SET "
                "  placement_kind = 'dedicated', placement_ref = EXCLUDED.placement_ref",
                (tenant_id, tenant_name, ref),
            )
        conn.commit()


def _seed_dedicated_identity(target_url: str, tenant_id: str, tenant_name: str, ref: str) -> None:
    """Seed the dedicated database's single tenants row and its placement_identity declaration."""
    psycopg = db_bootstrap.require_psycopg()
    with psycopg.connect(target_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            # The tenants registry is written under system scope, the way it is written elsewhere.
            cur.execute("SELECT set_config('app.current_tenant_id', '', true)")
            cur.execute(
                "INSERT INTO tenants (id, name, status, placement_kind, placement_ref) "
                "VALUES (%s, %s, 'active', 'dedicated', %s) ON CONFLICT (id) DO NOTHING",
                (tenant_id, tenant_name, ref),
            )
            # placement_identity is tenant-matching (migration 015), so its declaration is seeded
            # under the served tenant's own scope. It holds at most one row (singleton PK) and is
            # write-once (no UPDATE policy), so a provisioned identity cannot be silently re-pointed;
            # DO NOTHING keeps re-provisioning idempotent.
            cur.execute("SELECT set_config('app.current_tenant_id', %s, true)", (tenant_id,))
            cur.execute(
                "INSERT INTO placement_identity (tenant_id) VALUES (%s) "
                "ON CONFLICT (singleton) DO NOTHING",
                (tenant_id,),
            )
        conn.commit()


def provision_dedicated_database(
    *,
    tenant_id: str,
    tenant_name: str,
    ref: str,
    target_url: str,
    admin_url: str,
    control_url: str,
) -> None:
    """Provision a dedicated database for `tenant_id`, end to end. Idempotent and re-runnable."""
    database = _database_name(target_url)
    admin_target = _swap_database(admin_url, database)

    _create_database(database, admin_url)
    # Apply the full ledger as the admin (owner) so the app role is DML-only and FORCE RLS is
    # observable — exactly as the shared pool is provisioned.
    db_bootstrap.apply_ledger_to(admin_target, role=db_bootstrap.DEFAULT_ROLE, verbose=False)
    _seed_control_registry(control_url, tenant_id, tenant_name, ref)
    _seed_dedicated_identity(target_url, tenant_id, tenant_name, ref)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--tenant-name", required=True)
    parser.add_argument("--ref", required=True, help="placement_ref; the env var is BOPEN_DEDICATED_DB__<ref>")
    parser.add_argument("--target-url", required=True, help="app-role URL of the dedicated database")
    parser.add_argument("--admin-url", default=os.environ.get(db_bootstrap.ENV_ADMIN_URL, ""))
    parser.add_argument("--control-url", default=os.environ.get(db_bootstrap.ENV_APP_URL, ""))
    args = parser.parse_args()

    if not args.admin_url:
        print(f"ERROR: --admin-url or {db_bootstrap.ENV_ADMIN_URL} is required", file=sys.stderr)
        return 2
    if not args.control_url:
        print(f"ERROR: --control-url or {db_bootstrap.ENV_APP_URL} is required", file=sys.stderr)
        return 2

    provision_dedicated_database(
        tenant_id=args.tenant_id,
        tenant_name=args.tenant_name,
        ref=args.ref,
        target_url=args.target_url,
        admin_url=args.admin_url,
        control_url=args.control_url,
    )

    env_key = f"BOPEN_DEDICATED_DB__{args.ref}"
    print(f"Provisioned dedicated database for tenant {args.tenant_id}.")
    print("Export the connection so the kernel can route to it (never stored in a table):\n")
    print(f'    export {env_key}="{args.target_url}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
