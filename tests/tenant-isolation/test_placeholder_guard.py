# Status: draft preparation guard
# Work package: SKEL-P0-01
# Stable dependency: no
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_support'))
from skeleton_guard import assert_tier_guard  # noqa: E402


class TenantIsolationPlaceholderGuardTest(unittest.TestCase):
    def test_real_implementation_requires_negative_coverage(self) -> None:
        assert_tier_guard('tenant-isolation')


if __name__ == '__main__':
    unittest.main()
