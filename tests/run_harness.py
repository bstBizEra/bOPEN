#!/usr/bin/env python3
# Status: draft preparation harness
# Work package: SKEL-P0-01
# Stable dependency: no
from __future__ import annotations

import argparse
import importlib.util
import sys
import unittest

sys.dont_write_bytecode = True
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = ROOT / 'tests'
TIERS = ('unit', 'contract', 'integration', 'tenant-isolation', 'authorization')


def load_test_module(path: Path):
    name = 'bopen_test_' + '_'.join(path.relative_to(TEST_ROOT).parts).replace('-', '_').replace('.', '_')
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description='Run the dependency-free bOPEN skeleton guard harness.')
    parser.add_argument('--tier', choices=TIERS)
    args = parser.parse_args()

    tiers = (args.tier,) if args.tier else TIERS
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    for tier in tiers:
        for path in sorted((TEST_ROOT / tier).glob('test_*.py')):
            suite.addTests(loader.loadTestsFromModule(load_test_module(path)))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
