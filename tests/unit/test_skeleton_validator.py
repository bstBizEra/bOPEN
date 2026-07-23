# Status: draft preparation test
# Work package: SKEL-P0-01
# Stable dependency: no
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('validate_skeleton', ROOT / 'tools' / 'validate_skeleton.py')
if SPEC is None or SPEC.loader is None:
    raise RuntimeError('Unable to import skeleton validator')
validator = importlib.util.module_from_spec(SPEC)
sys.modules['validate_skeleton'] = validator
SPEC.loader.exec_module(validator)


class SkeletonValidatorTest(unittest.TestCase):
    def test_repository_candidate_passes_full_validation(self) -> None:
        report = validator.validate_repository(ROOT, mode='full')
        self.assertEqual([], report.errors, '\n'.join(report.errors))

    def test_no_runtime_implementation_is_present(self) -> None:
        self.assertEqual([], validator.find_business_logic(ROOT))

    def test_all_contract_shells_are_draft_and_non_stable(self) -> None:
        errors = validator.check_contracts(ROOT)
        self.assertEqual([], errors, '\n'.join(errors))


if __name__ == '__main__':
    unittest.main()
