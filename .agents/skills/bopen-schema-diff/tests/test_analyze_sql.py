import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_sql import analyze_text


class AnalyzeSqlTests(unittest.TestCase):
    def analyze(self, name):
        return analyze_text((ROOT / "fixtures/sql" / name).read_text(encoding="utf-8"))

    def test_safe_tenant_table(self):
        report = self.analyze("safe_tenant_table.sql")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["verdict"], "SAFE")

    def test_disable_rls_blocks(self):
        report = self.analyze("disable_rls.sql")
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertIn("BOPEN-TENANT-001", {f["rule_id"] for f in report["findings"]})

    def test_missing_tenant_id_blocks(self):
        report = self.analyze("missing_tenant_id.sql")
        self.assertEqual(report["status"], "BLOCK")
        self.assertIn("BOPEN-TENANT-010", {f["rule_id"] for f in report["findings"]})

    def test_drop_column_is_destructive(self):
        report = self.analyze("drop_column.sql")
        self.assertEqual(report["verdict"], "DESTRUCTIVE")

    def test_public_grant_security_critical(self):
        report = self.analyze("grant_public.sql")
        self.assertEqual(report["verdict"], "SECURITY_CRITICAL")

    def test_unscoped_unique_detected(self):
        report = self.analyze("unscoped_unique.sql")
        self.assertIn("BOPEN-TENANT-013", {f["rule_id"] for f in report["findings"]})


if __name__ == "__main__":
    unittest.main()
