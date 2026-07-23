import json
import unittest
from pathlib import Path

TIER_DIR = Path(__file__).resolve().parent
ALLOWED = {"__init__.py", "test_guard.py", "README.md", "AGENTS.md", "negative-tests.manifest.json"}


class SkeletonTierGuard(unittest.TestCase):
    """Fail-closed guard: a real implementation may not appear without its armed negative tests."""

    def test_tier_is_skeleton_only_or_arms_required_negatives(self):
        manifest = json.loads((TIER_DIR / "negative-tests.manifest.json").read_text(encoding="utf-8"))
        present = {p.name for p in TIER_DIR.iterdir() if p.is_file()}
        unexpected = present - ALLOWED
        if not unexpected:
            self.assertEqual(manifest.get("status"), "inactive",
                             "skeleton tier must declare status 'inactive' until implementation is armed")
            return
        self.assertEqual(manifest.get("status"), "armed",
                         f"implementation files present without an armed negative-test manifest: {sorted(unexpected)}")
        required = set(manifest.get("requiredNegativeTests", []))
        self.assertTrue(required, "an armed tier must declare requiredNegativeTests")
        missing = required - present
        self.assertFalse(missing, f"armed tier missing required negative tests: {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
