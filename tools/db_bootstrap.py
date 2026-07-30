#!/usr/bin/env python3
"""
bOPEN verification database bootstrap.

Work package: BOPEN-P35-001 (WP-P35-01, deliverable D-03)

Provisions a local PostgreSQL database, an unprivileged application role, and applies the
migrations in `infrastructure/database/` in order. The application role is deliberately not
a superuser and does not own the tables, because a superuser bypasses Row-Level Security
entirely and would make every isolation test pass for the wrong reason.

Usage:
    python tools/db_bootstrap.py --status
    python tools/db_bootstrap.py --apply
    python tools/db_bootstrap.py --rollback 003

Connection:
    Admin connection comes from BOPEN_ADMIN_DATABASE_URL, e.g.
        postgresql://postgres:<password>@127.0.0.1:5432/postgres
    Nothing is read from a file and no credential is stored by this tool.

Exit codes:
    0  requested operation completed
    1  operation failed
    2  could not run (psycopg missing, admin URL absent, server unreachable)
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "infrastructure" / "database"

ENV_ADMIN_URL = "BOPEN_ADMIN_DATABASE_URL"
ENV_APP_URL = "BOPEN_DATABASE_URL"

DEFAULT_DB = "bopen_dev"
DEFAULT_ROLE = "bopen_app"

MIGRATION_PATTERN = re.compile(r"^(\d{3})_(?!.*\.down$)(.+)\.sql$")
ROLLBACK_PATTERN = re.compile(r"^(\d{3})_(.+)\.down\.sql$")
COMPENSATE_PATTERN = re.compile(r"^(\d{3})_(.+)\.compensate\.sql$")

# Suffixes that mark a companion script rather than a forward migration. Kept in one place so
# that adding a new companion kind requires touching this line, which is the only defence
# against the exclusion being forgotten a fourth time.
COMPANION_SUFFIXES = (".down.sql", ".compensate.sql")


def require_psycopg():
    try:
        import psycopg  # noqa: F401
        return psycopg
    except ImportError:
        print(
            "ERROR: psycopg is not installed.\n"
            "       python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        raise SystemExit(2)


def admin_url() -> str:
    url = os.environ.get(ENV_ADMIN_URL, "").strip()
    if not url:
        print(
            f"ERROR: {ENV_ADMIN_URL} is not set.\n"
            f"       Set it to a superuser connection on the target server, e.g.\n"
            f"       export {ENV_ADMIN_URL}="
            f"postgresql://postgres:<password>@127.0.0.1:5432/postgres\n"
            f"\n"
            f"       This tool never reads or writes a credential file.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return url


def forward_migrations() -> list[tuple[str, Path]]:
    found = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        # Companion scripts are excluded by suffix rather than by a lookahead in the pattern:
        # `003_x.down.sql` still matches `^(\d{3})_(.+)\.sql$`, so a pattern-only exclusion
        # silently applied every rollback as a forward migration.
        #
        # The list is a tuple rather than a single suffix because this defect has now recurred:
        # adding `.compensate.sql` reintroduced it verbatim, and it was caught only because
        # `--status` printed the compensation script as a migration to apply. Any new companion
        # suffix must be added here, and the wildcard glob above is what makes forgetting easy.
        if path.name.endswith(COMPANION_SUFFIXES):
            continue
        match = MIGRATION_PATTERN.match(path.name)
        if match:
            found.append((match.group(1), path))
    return found


def rollback_migration(number: str) -> Path | None:
    for path in MIGRATIONS_DIR.glob("*.down.sql"):
        match = ROLLBACK_PATTERN.match(path.name)
        if match and match.group(1) == number:
            return path
    return None


def compensation_script(number: str) -> Path | None:
    """Return the data-compensation script for a migration, if one exists.

    A constraint-adding migration is not round-trippable on its rollback alone: while the
    constraints are absent the system accepts rows that violate them, and those rows then block
    re-application. The compensation is the third part of the strategy AGENTS.md section 14
    requires, and it is a separate file because it deletes data and must never run implicitly.
    """
    for path in MIGRATIONS_DIR.glob("*.compensate.sql"):
        match = COMPENSATE_PATTERN.match(path.name)
        if match and match.group(1) == number:
            return path
    return None


def cmd_compensate(number: str) -> int:
    psycopg = require_psycopg()

    path = compensation_script(number)
    if path is None:
        print(f"ERROR: no compensation script for migration {number}", file=sys.stderr)
        return 1

    if os.environ.get("BOPEN_DB_NON_PRODUCTION", "").strip() != "1":
        print(
            "REFUSED: compensation DELETES rows.\n"
            "         On a development database those rows are artefacts of a rollback\n"
            "         window. On a database holding real tenant data they are evidence of an\n"
            "         incident, and deleting them destroys that evidence — quarantine them\n"
            "         under an approved incident procedure instead.\n"
            "         Set BOPEN_DB_NON_PRODUCTION=1 to confirm this is not such a database.",
            file=sys.stderr,
        )
        return 1

    target = re.sub(r"/[^/]*$", f"/{DEFAULT_DB}", admin_url())
    try:
        with psycopg.connect(target, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(path.read_text(encoding="utf-8"))
                removed = cur.rowcount
            conn.commit()
    except Exception as exc:
        print(f"ERROR: compensation failed: {exc}", file=sys.stderr)
        return 1

    print(f"compensated using {path.name} (last statement removed {max(removed, 0)} rows)")
    print("Re-run `--apply` to restore the constraints.")
    return 0


def host_port(url: str) -> str:
    """Extract host:port from a connection URL.

    Derived from the admin URL rather than assumed, so a verification instance running on a
    non-default port is not silently reported as 5432 in the URL this tool prints.
    """
    match = re.search(r"@([^/@]+)/", url)
    return match.group(1) if match else "127.0.0.1:5432"


def app_url(password: str, database: str = DEFAULT_DB, admin: str | None = None) -> str:
    location = host_port(admin or os.environ.get(ENV_ADMIN_URL, ""))
    return f"postgresql://{DEFAULT_ROLE}:{password}@{location}/{database}"


# Migration ledger.
#
# Added after executing the migration 003 rollback (acceptance criterion A-06) exposed that
# --apply re-ran every migration from scratch and aborted on the first non-idempotent statement
# (`CREATE POLICY` in 001, which has no IF NOT EXISTS form). It had only ever worked because the
# database was empty the first time. That defect was invisible until a rollback was actually
# executed rather than assumed to work.
#
# The checksum column does double duty. It detects a migration file that changed after being
# applied, which AGENTS.md section 14 prohibits ("migrations are append-only after merge"). A
# rule that is only written down is a preference; this makes it a check.
LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(16) PRIMARY KEY,
    filename    TEXT NOT NULL,
    checksum    CHAR(64) NOT NULL,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_ledger(cur) -> dict[str, tuple[str, str]]:
    cur.execute("SELECT version, filename, checksum FROM schema_migrations")
    return {row[0]: (row[1], row[2]) for row in cur.fetchall()}


def cmd_status() -> int:
    psycopg = require_psycopg()
    url = admin_url()

    try:
        with psycopg.connect(url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s", (DEFAULT_DB,)
                )
                db_exists = cur.fetchone() is not None
                cur.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s", (DEFAULT_ROLE,)
                )
                role_exists = cur.fetchone() is not None
    except Exception as exc:
        print(f"ERROR: cannot reach the server: {exc}", file=sys.stderr)
        return 2

    print("bOPEN database status")
    print(f"- server:            {version.split(',')[0]}")
    print(f"- database {DEFAULT_DB!r}: {'present' if db_exists else 'absent'}")
    print(f"- role {DEFAULT_ROLE!r}:     {'present' if role_exists else 'absent'}")
    print(f"- forward migrations: {len(forward_migrations())}")
    for number, path in forward_migrations():
        has_rollback = rollback_migration(number) is not None
        has_comp = compensation_script(number) is not None
        marker = "with rollback" if has_rollback else "NO ROLLBACK"
        if has_comp:
            marker += " + compensation"
        print(f"    {number}  {path.name}  ({marker})")
    return 0


def cmd_apply(password: str) -> int:
    psycopg = require_psycopg()
    from psycopg import sql

    url = admin_url()

    # Database and role creation cannot run inside a transaction block.
    try:
        with psycopg.connect(url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (DEFAULT_ROLE,))
                if cur.fetchone() is None:
                    cur.execute(
                        sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                            sql.Identifier(DEFAULT_ROLE), sql.Literal(password)
                        )
                    )
                    print(f"created role {DEFAULT_ROLE}")
                else:
                    cur.execute(
                        sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                            sql.Identifier(DEFAULT_ROLE), sql.Literal(password)
                        )
                    )
                    print(f"role {DEFAULT_ROLE} already present; password reset")

                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DEFAULT_DB,))
                if cur.fetchone() is None:
                    cur.execute(
                        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DEFAULT_DB))
                    )
                    print(f"created database {DEFAULT_DB}")
                else:
                    print(f"database {DEFAULT_DB} already present")
    except Exception as exc:
        print(f"ERROR: provisioning failed: {exc}", file=sys.stderr)
        return 1

    # Migrations run as the admin role against the target database. The admin owns the
    # tables; the application role is granted DML only. This split is what makes
    # FORCE ROW LEVEL SECURITY observable: if the application role owned the tables, it
    # would need FORCE to be constrained at all, and a missing FORCE would go unnoticed.
    target = re.sub(r"/[^/]*$", f"/{DEFAULT_DB}", url)
    try:
        with psycopg.connect(target, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(LEDGER_DDL)
            conn.commit()

            with conn.cursor() as cur:
                ledger = read_ledger(cur)

            for number, path in forward_migrations():
                digest = checksum(path)

                if number in ledger:
                    recorded_name, recorded_digest = ledger[number]
                    if recorded_digest != digest:
                        # AGENTS.md section 14: migrations are append-only after merge. A file
                        # that changed after being applied means the schema in this database no
                        # longer corresponds to the file that describes it, and re-running it
                        # would not reconcile them.
                        print(
                            f"ERROR: {path.name} changed after it was applied.\n"
                            f"       recorded checksum {recorded_digest[:12]}…\n"
                            f"       file checksum     {digest[:12]}…\n"
                            f"       Migrations are append-only after merge (AGENTS.md §14).\n"
                            f"       Add a new migration rather than editing this one.",
                            file=sys.stderr,
                        )
                        return 1
                    print(f"skipped {path.name} (already applied)")
                    continue

                statement = path.read_text(encoding="utf-8")
                with conn.cursor() as cur:
                    cur.execute(statement)
                    cur.execute(
                        "INSERT INTO schema_migrations (version, filename, checksum) "
                        "VALUES (%s, %s, %s)",
                        (number, path.name, digest),
                    )
                conn.commit()
                print(f"applied {path.name}")

            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "GRANT SELECT, INSERT, UPDATE, DELETE "
                        "ON ALL TABLES IN SCHEMA public TO {}"
                    ).format(sql.Identifier(DEFAULT_ROLE))
                )
                cur.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(
                        sql.Identifier(DEFAULT_ROLE)
                    )
                )
            conn.commit()
            print(f"granted DML on public schema to {DEFAULT_ROLE}")
    except Exception as exc:
        print(f"ERROR: migration failed: {exc}", file=sys.stderr)
        return 1

    print("\nBootstrap complete. Export the application URL:\n")
    print(f'    export {ENV_APP_URL}="{app_url(password)}"')
    print(
        "\nThen run the isolation suite:\n"
        "    python tools/run_tests.py\n"
    )
    return 0


def cmd_rollback(number: str) -> int:
    psycopg = require_psycopg()

    path = rollback_migration(number)
    if path is None:
        print(
            f"ERROR: no rollback script found for migration {number}.\n"
            f"       AGENTS.md section 14 requires a forward, rollback or compensating "
            f"strategy for every migration.",
            file=sys.stderr,
        )
        return 1

    if os.environ.get("BOPEN_DB_NON_PRODUCTION", "").strip() != "1":
        print(
            "REFUSED: rollback drops tables that may hold audit records.\n"
            "         Set BOPEN_DB_NON_PRODUCTION=1 to confirm the target is a "
            "development or verification database.",
            file=sys.stderr,
        )
        return 1

    target = re.sub(r"/[^/]*$", f"/{DEFAULT_DB}", admin_url())
    try:
        with psycopg.connect(target, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(path.read_text(encoding="utf-8"))
                # Clearing the ledger entry in the same transaction as the rollback keeps the
                # two from disagreeing. If the entry survived, a later --apply would skip the
                # migration and leave the database missing objects the ledger claims are there.
                cur.execute("DELETE FROM schema_migrations WHERE version = %s", (number,))
            conn.commit()
    except Exception as exc:
        print(f"ERROR: rollback failed: {exc}", file=sys.stderr)
        return 1

    print(f"rolled back {path.name}")
    return 0


def cmd_baseline() -> int:
    """Record already-applied migrations without running them.

    Needed to adopt a database provisioned before the ledger existed. Only marks a migration as
    applied when its objects are actually present, checked per migration, so it cannot be used
    to skip work that was never done.
    """
    psycopg = require_psycopg()
    target = re.sub(r"/[^/]*$", f"/{DEFAULT_DB}", admin_url())

    # A cheap existence probe per migration. Deliberately not a general mechanism: a migration
    # without a probe is not baselined, which fails safe.
    PROBES = {
        "001": "SELECT to_regclass('public.memberships')",
        "002": "SELECT to_regclass('public.usage_outbox')",
        "003": "SELECT to_regclass('public.audit_events')",
    }

    try:
        with psycopg.connect(target, autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute(LEDGER_DDL)
            conn.commit()

            with conn.cursor() as cur:
                ledger = read_ledger(cur)
                for number, path in forward_migrations():
                    if number in ledger:
                        print(f"skipped {path.name} (already in ledger)")
                        continue
                    probe = PROBES.get(number)
                    if probe is None:
                        print(f"skipped {path.name} (no existence probe defined)")
                        continue
                    cur.execute(probe)
                    if cur.fetchone()[0] is None:
                        print(f"skipped {path.name} (objects not present; run --apply)")
                        continue
                    cur.execute(
                        "INSERT INTO schema_migrations (version, filename, checksum) "
                        "VALUES (%s, %s, %s)",
                        (number, path.name, checksum(path)),
                    )
                    print(f"baselined {path.name}")
            conn.commit()
    except Exception as exc:
        print(f"ERROR: baseline failed: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true", help="report server and migration state")
    group.add_argument("--apply", action="store_true", help="provision and apply all migrations")
    group.add_argument("--rollback", metavar="NNN", help="run the rollback script for migration NNN")
    group.add_argument("--baseline", action="store_true", help="record already-applied migrations in the ledger without running them")
    group.add_argument("--compensate", metavar="NNN", help="remove rows that block re-application of migration NNN (DELETES DATA)")
    parser.add_argument(
        "--password",
        default=os.environ.get("BOPEN_APP_PASSWORD", "bopen_local_dev"),
        help=(
            "password for the application role. Development default is a clearly "
            "non-production value; override via BOPEN_APP_PASSWORD."
        ),
    )
    args = parser.parse_args()

    if args.status:
        return cmd_status()
    if args.apply:
        return cmd_apply(args.password)
    if args.baseline:
        return cmd_baseline()
    if args.compensate:
        return cmd_compensate(args.compensate)
    return cmd_rollback(args.rollback)


if __name__ == "__main__":
    raise SystemExit(main())
