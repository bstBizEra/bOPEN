#!/usr/bin/env python3
"""
bOPEN Canonical Test Runner
Configures Python package roots dynamically and executes all repository test suites.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_CATEGORIES = (
    ("unit", ROOT / "tests" / "unit"),
    ("integration", ROOT / "tests" / "integration"),
    ("contracts", ROOT / "tests" / "contracts"),
    ("isolation", ROOT / "tests" / "isolation"),
    ("governance", ROOT / "tests" / "governance"),
)

# Configure sys.path for test discovery
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT / "sdk" / "python"))
sys.path.insert(0, str(ROOT))


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    category_counts = {}

    for category, test_dir in TEST_CATEGORIES:
        if not test_dir.is_dir():
            print(f"ERROR: required test category is missing: {test_dir}", file=sys.stderr)
            return 2

        category_suite = loader.discover(start_dir=str(test_dir))
        test_count = category_suite.countTestCases()
        if test_count == 0:
            print(f"ERROR: required test category is empty: {test_dir}", file=sys.stderr)
            return 2

        category_counts[category] = test_count
        suite.addTests(category_suite)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\nCanonical test inventory:")
    for category, _ in TEST_CATEGORIES:
        print(f"- {category}: {category_counts[category]}")
    print(f"- total: {suite.countTestCases()}")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
