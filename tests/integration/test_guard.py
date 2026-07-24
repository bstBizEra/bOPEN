import json
import unittest
from pathlib import Path

TIER_DIR = Path(__file__).resolve().parent
ALLOWED = {"__init__.py", "test_guard.py", "README.md", "AGENTS.md", "negative-tests.manifest.json"}
IGNORED_DIRS = {"__pycache__"}


class SkeletonTierGuard(unittest.TestCase):
    """Fail-closed guard: a real implementation may not appear at ANY depth without armed negative tests.

    Inventory is recursive (rglob), not top-level (iterdir) -- a non-recursive scan would let a
    nested implementation (e.g. tests/<tier>/sub/impl.py) bypass the guard while it stayed green.
    """

    def _implementation_files(self):
        found = []
        for path in TIER_DIR.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(TIER_DIR)
            if any(part in IGNORED_DIRS for part in rel.parts):
                continue
            if path.parent == TIER_DIR and path.name in ALLOWED:
                continue
            found.append(rel.as_posix())
        return sorted(found)

    def test_tier_is_skeleton_only_or_arms_required_negatives(self):
        manifest = json.loads((TIER_DIR / "negative-tests.manifest.json").read_text(encoding="utf-8"))
        implementation_files = self._implementation_files()
        if not implementation_files:
            self.assertEqual(
                manifest.get("status"), "inactive",
                "skeleton tier must declare status 'inactive' until implementation is armed",
            )
            return
        self.assertEqual(
            manifest.get("status"), "armed",
            f"implementation file(s) present (any depth) without an armed negative-test manifest: {implementation_files}",
        )
        required = set(manifest.get("requiredNegativeTests", []))
        self.assertTrue(required, "an armed tier must declare requiredNegativeTests")
        missing = required - set(implementation_files)
        self.assertFalse(missing, f"armed tier missing required negative tests: {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
