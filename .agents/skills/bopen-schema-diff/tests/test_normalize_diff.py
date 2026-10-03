import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_diff import normalize


class NormalizeDiffTests(unittest.TestCase):
    def test_atlas_fixture_normalizes(self):
        sql = (ROOT / "fixtures/engine/atlas-plan.sql").read_text(encoding="utf-8")
        changes = normalize(sql, "atlas")
        self.assertGreaterEqual(len(changes), 2)
        self.assertTrue(all("atlas" in c["engine_findings"] for c in changes))

    def test_drop_is_breaking(self):
        changes = normalize("DROP TABLE projects;", "unknown")
        self.assertEqual(changes[0]["operation"], "drop")
        self.assertEqual(changes[0]["classification"]["compatibility"], "breaking")


if __name__ == "__main__":
    unittest.main()
