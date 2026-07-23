# Status: draft preparation guard
# Work package: SKEL-P0-01
# Stable dependency: no
from __future__ import annotations

from pathlib import Path

RUNTIME_SUFFIXES = {
    '.py', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.go', '.rs',
    '.java', '.kt', '.kts', '.cs', '.rb', '.php', '.dart', '.swift',
    '.sql', '.prisma', '.graphql', '.gql', '.sh', '.bash', '.ps1'
}
KERNEL_ZONES = ('apps', 'services', 'packages', 'sdk', 'infrastructure')


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_runtime_implementation(root: Path | None = None) -> list[Path]:
    root = root or repository_root()
    findings: list[Path] = []
    for zone in KERNEL_ZONES:
        base = root / zone
        if not base.exists():
            continue
        for path in base.rglob('*'):
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            if any(part in {'tests', 'test', '__pycache__'} for part in rel.parts):
                continue
            if path.name.endswith('.d.ts'):
                continue
            if path.suffix.lower() in RUNTIME_SUFFIXES:
                findings.append(rel)
    return sorted(findings, key=lambda item: item.as_posix())


def negative_tests_for_tier(tier: str, root: Path | None = None) -> list[Path]:
    root = root or repository_root()
    tier_dir = root / 'tests' / tier
    tokens = {
        'unit': ('negative', 'invalid', 'reject'),
        'contract': ('negative', 'invalid', 'reject'),
        'integration': ('negative', 'failure', 'rollback', 'reject'),
        'tenant-isolation': ('negative', 'cross_tenant', 'wrong_tenant', 'tenant_isolation', 'deny'),
        'authorization': ('negative', 'unauthorized', 'forbidden', 'deny')
    }[tier]
    results: list[Path] = []
    for path in tier_dir.rglob('*'):
        if not path.is_file() or path.name == 'test_placeholder_guard.py':
            continue
        lower = path.name.lower().replace('-', '_')
        if not any(token in lower for token in tokens):
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        marker = f'BOPEN_NEGATIVE_TEST: {tier}'
        if marker in text:
            results.append(path.relative_to(root))
    return sorted(results, key=lambda item: item.as_posix())


def assert_tier_guard(tier: str, root: Path | None = None) -> None:
    root = root or repository_root()
    implementation = find_runtime_implementation(root)
    if not implementation:
        return
    negative_tests = negative_tests_for_tier(tier, root)
    if negative_tests:
        return
    rendered = ', '.join(path.as_posix() for path in implementation)
    raise AssertionError(
        f'Fail-closed {tier} guard: runtime implementation detected without '
        f'a tier-specific negative test. Implementation files: {rendered}'
    )
