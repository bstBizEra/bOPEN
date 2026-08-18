"""Living inventory of the foreign keys a cross-database tenant split cannot enforce.

Work package: BOPEN-WP-FK-INVENTORY-001
Governing artifacts: docs/01-product/roadmap.md (Phase 3.6);
                     docs/01-product/KERNEL-AUTONOMY-OBJECTIVE.md section 4

WHY THIS EXISTS

roadmap.md sizes the hard part of Phase 3.6 as "twelve foreign keys currently reference tenants or
principals and cannot survive a split across databases, because PostgreSQL cannot enforce a foreign
key across them."

That sentence was written 2026-07-31, before migrations 018-022 added UOM, ContactPoint, Location,
Notification and the tenant-cascade remediation. Nobody recounted. A phase was sized from a number
five migrations out of date, and the error surfaced only because someone happened to count.

This test recounts on every run. It is the smallest thing that stops the number drifting.

WHY IT DOES NOT USE THE DATABASE

The obvious implementation queries pg_constraint. It was rejected: on 2026-08-17 the contract
conformance gate reported a false FAIL because the database timed out and database-gated coverage
vanished with it. A gate whose verdict depends on an external service being reachable goes red on
infrastructure, and a gate that cries wolf is one readers learn to ignore.

So the inventory is derived from the migration files, which are the same objects CI checks out. It
runs on the standard library alone, with no environment.

METHOD, AND ITS LIMITS

Forward migrations are read in order. Inline REFERENCES inside CREATE TABLE bodies are recorded;
ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY adds; ALTER TABLE ... DROP CONSTRAINT removes.
Rollback files are excluded -- counting them is how a raw grep reports 53 references where 30
constraints exist.

This is not a SQL parser. It handles the shapes this repository uses and would need extending for
others. A shape it cannot read is a silent miss, which is why test_derivation_is_not_vacuous asserts
the reader found a substantial inventory before any count is trusted.

CROSS-CHECK ON RECORD

On 2026-08-17 the live catalogue was queried directly:

    select confdeltype, count(*) from pg_constraint
    where contype='f' and confrelid='tenants'::regclass group by 1;
      -> 13 RESTRICT, 17 CASCADE

The static derivation below reproduces 13 and 17 exactly. That agreement is the reason to trust it.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "infrastructure" / "database"

# The inventory as it stands. A change here is a real change to what a cross-database split must
# solve; make it deliberately and state the new count in the commit message.
EXPECTED = {
    ("tenants", "CASCADE"): 17,
    ("tenants", "RESTRICT"): 13,
}
EXPECTED_TOTAL = 30

_CREATE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-z0-9_]+)\s*\((.*?)\n\)\s*;", re.I | re.S
)
_INLINE = re.compile(
    r"^\s*([a-z0-9_]+)\s+[^,]*?REFERENCES\s+(tenants|principals)\s*\([^)]*\)"
    r"(?:\s+ON\s+DELETE\s+(CASCADE|RESTRICT|SET\s+NULL|NO\s+ACTION))?",
    re.I | re.M,
)
_ADD = re.compile(
    r"ALTER\s+TABLE\s+([a-z0-9_]+)\s+ADD\s+CONSTRAINT\s+([a-z0-9_]+)\s+"
    r"FOREIGN\s+KEY\s*\([^)]*\)\s*REFERENCES\s+(tenants|principals)\s*\([^)]*\)"
    r"(?:\s+ON\s+DELETE\s+(CASCADE|RESTRICT|SET\s+NULL|NO\s+ACTION))?",
    re.I,
)
_DROP = re.compile(
    r"ALTER\s+TABLE\s+([a-z0-9_]+)\s+DROP\s+CONSTRAINT\s+(?:IF\s+EXISTS\s+)?([a-z0-9_]+)", re.I
)


def forward_migrations() -> list[pathlib.Path]:
    return sorted(p for p in MIGRATIONS.glob("*.sql") if ".down." not in p.name)


def derive_inventory() -> dict:
    """Net foreign keys to tenants/principals after every forward migration is applied in order."""
    fks: dict = {}
    for path in forward_migrations():
        sql = path.read_text(encoding="utf-8", errors="replace")

        for table, body in _CREATE.findall(sql):
            for column, target, action in _INLINE.findall(body):
                fks[(table.lower(), column.lower())] = {
                    "target": target.lower(),
                    "on_delete": (action or "NO ACTION").upper(),
                    "migration": path.name,
                }

        for statement in sql.split(";"):
            dropped = _DROP.search(statement)
            if dropped:
                table, constraint = dropped.group(1).lower(), dropped.group(2).lower()
                fks.pop((table, constraint), None)
                # A constraint named <table>_<column>_fkey shadows the inline column entry.
                shadowed = constraint
                if shadowed.startswith(table + "_"):
                    shadowed = shadowed[len(table) + 1 :]
                if shadowed.endswith("_fkey"):
                    shadowed = shadowed[: -len("_fkey")]
                fks.pop((table, shadowed), None)

            added = _ADD.search(statement)
            if added:
                fks[(added.group(1).lower(), added.group(2).lower())] = {
                    "target": added.group(3).lower(),
                    "on_delete": (added.group(4) or "NO ACTION").upper(),
                    "migration": path.name,
                }
    return fks


class CrossDatabaseForeignKeyInventory(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = derive_inventory()

    def test_derivation_is_not_vacuous(self) -> None:
        """A reader that matches nothing would pass every count assertion below."""
        self.assertGreater(len(forward_migrations()), 15, "forward migrations not found")
        self.assertGreater(
            len(self.inventory), 20, "the reader found almost nothing; it is broken, not the schema"
        )

    def test_rollback_migrations_are_excluded(self) -> None:
        """Counting rollback files is how a raw grep reports 53 references for 30 constraints."""
        self.assertTrue(list(MIGRATIONS.glob("*.down.sql")), "no rollback migrations to exclude")
        for path in forward_migrations():
            self.assertNotIn(".down.", path.name)

    def test_inventory_has_not_drifted(self) -> None:
        counts: dict = {}
        for entry in self.inventory.values():
            key = (entry["target"], entry["on_delete"])
            counts[key] = counts.get(key, 0) + 1

        self.assertEqual(
            counts,
            EXPECTED,
            "\nThe cross-database foreign-key inventory changed.\n"
            "This is the number Phase 3.6 is sized against. If the change is intended, update\n"
            "EXPECTED in this file and state the new count in the commit message, so the next\n"
            "reader inherits a number rather than a memory.\n"
            "derived:  " + str(sorted(counts.items())) + "\n"
            "expected: " + str(sorted(EXPECTED.items())),
        )
        self.assertEqual(sum(counts.values()), EXPECTED_TOTAL)

    def test_principals_half_is_already_solved(self) -> None:
        """016_principal_reference_survives_placement removed every foreign key to principals.

        Recorded as a test rather than a comment because roadmap.md still describes the Phase 3.6
        problem as tenants OR principals. Half of it is closed, and a reader sizing the work from
        that sentence would plan for constraints that no longer exist.
        """
        to_principals = {k: v for k, v in self.inventory.items() if v["target"] == "principals"}
        self.assertEqual(
            to_principals,
            {},
            "a foreign key to principals reappeared; 016 removed them deliberately because a "
            "cross-database reference cannot be enforced",
        )

    def test_roadmap_figure_is_stale(self) -> None:
        """The roadmap says twelve. It is thirty, and none of them reference principals.

        This test fails when the roadmap is corrected, which is the point: the sentence cannot be
        fixed without also retiring the test that records it was wrong.
        """
        roadmap = (ROOT / "docs" / "01-product" / "roadmap.md").read_text(
            encoding="utf-8", errors="replace"
        )
        self.assertIn(
            "twelve foreign keys",
            roadmap,
            "roadmap.md no longer says 'twelve foreign keys' -- if it was corrected, delete this "
            "test and record the new figure in the commit message",
        )
        self.assertNotEqual(12, EXPECTED_TOTAL)


if __name__ == "__main__":
    unittest.main()
