import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AdapterSafetyTests(unittest.TestCase):
    def test_atlas_wrapper_does_not_contain_apply(self):
        text = (ROOT / "scripts/run_atlas.py").read_text(encoding="utf-8")
        self.assertNotIn('"schema", "apply"', text)
        self.assertNotIn('"migrate", "apply"', text)

    def test_manifest_prohibits_production_mutation(self):
        text = (ROOT / "bopen.skill.yaml").read_text(encoding="utf-8")
        self.assertIn("productionMutation: prohibited", text)


if __name__ == "__main__":
    unittest.main()
