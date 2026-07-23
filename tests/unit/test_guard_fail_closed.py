# Status: draft preparation test
# Work package: SKEL-P0-01
# Stable dependency: no
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_support'))
from skeleton_guard import assert_tier_guard  # noqa: E402


class FailClosedGuardBehaviorTest(unittest.TestCase):
    TIERS = ('unit', 'contract', 'integration', 'tenant-isolation', 'authorization')

    @staticmethod
    def _runtime_candidate(root: Path) -> None:
        (root / 'apps').mkdir(parents=True)
        (root / 'apps' / 'runtime.ts').write_text('export const implementation = true;\n', encoding='utf-8')
        for tier in FailClosedGuardBehaviorTest.TIERS:
            (root / 'tests' / tier).mkdir(parents=True)

    def test_every_tier_denies_runtime_without_marked_negative_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._runtime_candidate(root)
            for tier in self.TIERS:
                with self.subTest(tier=tier):
                    with self.assertRaisesRegex(AssertionError, f'Fail-closed {tier} guard'):
                        assert_tier_guard(tier, root)

    def test_explicit_tier_marker_satisfies_only_that_tier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._runtime_candidate(root)
            negative = root / 'tests' / 'unit' / 'test_negative_runtime.py'
            negative.write_text('# BOPEN_NEGATIVE_TEST: unit\n', encoding='utf-8')
            assert_tier_guard('unit', root)
            with self.assertRaisesRegex(AssertionError, 'Fail-closed authorization guard'):
                assert_tier_guard('authorization', root)


if __name__ == '__main__':
    unittest.main()
