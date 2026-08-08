"""
Structural guard: an append-only table may not leave its tenant edge on CASCADE.

Work package: WP-P35-08 (Refusal Matrix R-7)
Governing artifacts: DEC-P4-NOTIFY-TENANT-CASCADE §6, §7; AGENTS.md §8, §14;
                     BOPEN-GOV-EBIV-001

An append-only guarantee in this repository is built from two things: RLS policies that grant
SELECT and INSERT but no UPDATE or DELETE, and an `ON DELETE RESTRICT` foreign key to the parent
row. Migration 009 records the reason the second is needed — *"PostgreSQL performs foreign-key
actions with row security bypassed"* — so a policy alone cannot stop a cascade.

Both were in place on eleven tables and neither defended them, because the row also carried
`tenant_id REFERENCES tenants(id) ON DELETE CASCADE`. The tenant edge reaches the row first and
the RESTRICT edge is never consulted. Reproduced live on the notification tables by an independent
verifier: the tenant delete succeeded and the attempt and receipt rows went to zero.

This test is R-7 of the Refusal Matrix, and it is the row that decides whether WP-P35-08 fixes an
instance or a class. The defect has already recurred four times — in migrations 014, 019, 020 and
021 — and 014 is the migration that was written to teach this exact lesson, having closed the
*instance* edge while leaving the *tenant* edge CASCADE. Without a structural check the fifth
foundation will reintroduce it.

It reads the migration files rather than the live database deliberately: the point is to fail in
review, on the change that introduces the defect, not after that change has been applied somewhere.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "infrastructure" / "database"

TABLE_RE = re.compile(
    r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_]+)\s*\((.*?)\n\);", re.S | re.I
)
TENANT_EDGE_RE = re.compile(
    r"tenant_id[^,]*REFERENCES\s+tenants\s*\(\s*id\s*\)[^,]*?ON DELETE (CASCADE|RESTRICT|SET NULL)",
    re.S | re.I,
)
ALTER_RESTRICT_RE = re.compile(
    r"ALTER TABLE\s+([a-z_]+)\s+ADD CONSTRAINT.*?ON DELETE RESTRICT", re.S | re.I
)
ALTER_TENANT_EDGE_RE = re.compile(
    r"ALTER TABLE\s+([a-z_]+)\s+ADD CONSTRAINT\s+[a-z_]+\s+FOREIGN KEY\s*\(\s*tenant_id\s*\)"
    r"\s*REFERENCES\s+tenants\s*\(\s*id\s*\)[^;]*?ON DELETE (CASCADE|RESTRICT)",
    re.S | re.I,
)


def _forward_migrations() -> list[Path]:
    return sorted(p for p in MIGRATIONS.glob("*.sql") if not p.name.endswith(".down.sql"))


def _survey() -> tuple[dict[str, str], dict[str, str]]:
    """Return (tenant_edge_action_by_table, append_only_table -> migration that made it so).

    A table counts as append-only-protected if any `ON DELETE RESTRICT` foreign key targets its
    parent, whether declared at CREATE TABLE or added by a later ALTER. Missing the ALTER form is
    how `workflow_history` escaped an earlier hand survey.
    """
    tenant_edge: dict[str, str] = {}
    protected: dict[str, str] = {}

    for path in _forward_migrations():
        src = path.read_text(encoding="utf-8", errors="replace")

        for m in TABLE_RE.finditer(src):
            table, body = m.group(1), m.group(2)
            edge = TENANT_EDGE_RE.search(body)
            if edge:
                tenant_edge[table] = edge.group(1).upper()
            if re.search(r"ON DELETE RESTRICT", body, re.I):
                protected.setdefault(table, path.name)

        for m in ALTER_RESTRICT_RE.finditer(src):
            protected.setdefault(m.group(1), path.name)

        # a later migration may move the tenant edge itself — WP-P35-08 does exactly this
        for m in ALTER_TENANT_EDGE_RE.finditer(src):
            tenant_edge[m.group(1)] = m.group(2).upper()

    return tenant_edge, protected


class AppendOnlyTablesGuardTheirTenantEdge(unittest.TestCase):
    """WP-P35-08 R-7."""

    def test_the_survey_itself_finds_something(self):
        """A structural check that matches nothing passes vacuously and measures nothing.

        This asserts the parser still works against the migration set — if a refactor changes the
        SQL style enough that nothing is recognised, the real assertion below would go green while
        checking zero tables.
        """
        tenant_edge, protected = _survey()
        self.assertGreater(len(tenant_edge), 5, "tenant edges parsed: the survey found almost nothing")
        self.assertGreater(len(protected), 5, "append-only tables parsed: the survey found almost nothing")
        self.assertIn("audit_events", protected, "the known-good example is not being seen")

    def test_no_append_only_table_leaves_its_tenant_edge_on_cascade(self):
        """The guarantee is only as strong as every ON DELETE action that reaches the row."""
        tenant_edge, protected = _survey()

        offenders = sorted(
            (table, tenant_edge[table], migration)
            for table, migration in protected.items()
            if tenant_edge.get(table) == "CASCADE"
        )

        self.assertEqual(
            offenders,
            [],
            "These tables rely on ON DELETE RESTRICT for append-only evidence while their own "
            "tenant_id edge is ON DELETE CASCADE, so deleting the tenant erases the evidence and "
            "the RESTRICT edge is never consulted:\n"
            + "\n".join(f"    {t:<45} CASCADE   (protected by {m})" for t, _, m in offenders)
            + "\n\nUse ON DELETE RESTRICT on the tenant edge, as audit_events (003) and "
            "lifecycle_events (005) already do. See DEC-P4-NOTIFY-TENANT-CASCADE.",
        )

    def test_the_known_good_pattern_is_still_in_place(self):
        """A positive control: the tables that already do this correctly must keep doing it.

        Without this, a change that moved audit_events to CASCADE would make the assertion above
        report more offenders rather than fewer — but nothing would say the reference pattern had
        been lost.
        """
        tenant_edge, _ = _survey()
        for table in ("audit_events", "lifecycle_events"):
            self.assertEqual(
                tenant_edge.get(table),
                "RESTRICT",
                f"{table} is the pattern the rest are measured against; its tenant edge must stay "
                f"ON DELETE RESTRICT",
            )


if __name__ == "__main__":
    unittest.main()
