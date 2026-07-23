#!/usr/bin/env python3
# Status: draft preparation validator
# Work package: SKEL-P0-01
# Stable dependency: no
"""Dependency-free, read-only, fail-closed validator for SKEL-P0-01."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

ZONES = ('apps', 'services', 'packages', 'contracts', 'sdk', 'infrastructure', 'tools', 'tests', 'docs')
KERNEL_ZONES = ('apps', 'services', 'packages', 'sdk', 'infrastructure')
TIERS = ('unit', 'contract', 'integration', 'tenant-isolation', 'authorization')
PACKAGES = ('kernel-contracts', 'kernel-testing')
RUNTIME_SUFFIXES = {
    '.py', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.go', '.rs', '.java',
    '.kt', '.kts', '.cs', '.rb', '.php', '.dart', '.swift', '.sql', '.prisma',
    '.graphql', '.gql', '.sh', '.bash', '.ps1',
}
CONTRACTS = {
    'tenant.contract.json': ('BOPEN-CONTRACT-TENANT-001', 'BOPEN-TENANT-001'),
    'organization.contract.json': ('BOPEN-CONTRACT-ORGANIZATION-001', 'BOPEN-TENANT-001'),
    'membership.contract.json': ('BOPEN-CONTRACT-MEMBERSHIP-001', 'BOPEN-TENANT-001'),
    'active-tenant-context.contract.json': ('BOPEN-CONTRACT-ACTIVE-CONTEXT-001', 'BOPEN-TENANT-001'),
    'authorization-decision.contract.json': ('BOPEN-CONTRACT-AUTHZ-DECISION-001', 'BOPEN-AUTHZ-001'),
    'entitlement.contract.json': ('BOPEN-CONTRACT-ENTITLEMENT-001', 'BOPEN-ENT-001'),
    'module-manifest.contract.json': ('BOPEN-CONTRACT-MODULE-MANIFEST-001', 'BOPEN-MOD-001'),
    'capability.contract.json': ('BOPEN-CONTRACT-CAPABILITY-001', 'BOPEN-MOD-001'),
    'party.contract.json': ('BOPEN-CONTRACT-PARTY-001', 'BOPEN-PARTY-001'),
    'event-envelope.contract.json': ('BOPEN-CONTRACT-EVENT-ENVELOPE-001', 'BOPEN-ARCH-001'),
    'audit-envelope.contract.json': ('BOPEN-CONTRACT-AUDIT-ENVELOPE-001', 'BOPEN-ARCH-001'),
}
BANNED_SCHEMA_KEYS = {
    'required', 'properties', 'patternProperties', 'dependentSchemas', 'oneOf',
    'anyOf', 'allOf', 'not', 'if', 'then', 'else', 'enum', 'const', 'minimum',
    'maximum', 'minLength', 'maxLength',
}


@dataclass
class ValidationReport:
    errors: list[str]
    checks: dict[str, int]

    @property
    def ok(self) -> bool:
        return not self.errors


def _json(path: Path, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f'invalid JSON {path}: {exc}')
        return None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def _draft_version(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r'0\.\d+\.\d+(?:-[\w.-]+)?', value) is not None


def check_scope_boundary(root: Path) -> list[str]:
    errors: list[str] = []
    allowed = set(ZONES) | {'README.md', 'package.json'}
    errors += [f'unapproved top-level path: {name}' for name in sorted({p.name for p in root.iterdir()} - allowed)]
    if not (root / 'README.md').is_file() or (root / 'README.md').read_bytes() != b'# bOPEN':
        errors.append('pre-existing README.md bytes changed from the base commit')
    prohibited = ('research/upstream/', 'docs/00-governance/registers/')
    secret_names = {'.env', '.env.local', '.env.production', 'id_rsa', 'id_ed25519', 'credentials.json', 'secrets.json', 'root-ledger-genesis.json'}
    for path in root.rglob('*'):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            errors.append(f'symlink is prohibited: {rel}')
        if '__pycache__' in path.parts or path.suffix == '.pyc':
            errors.append(f'generated Python cache is prohibited: {rel}')
        if any(rel.startswith(prefix) for prefix in prohibited):
            errors.append(f'prohibited path populated: {rel}')
        if path.is_file() and (path.name in secret_names or path.suffix.lower() in {'.pem', '.key', '.p12', '.pfx'}):
            errors.append(f'secret-bearing filename is prohibited: {rel}')
        if path.is_file() and path.stat().st_size <= 2_000_000:
            text = path.read_text(encoding='utf-8', errors='ignore')
            if re.search(r'(?m)^-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----', text):
                errors.append(f'private-key material detected: {rel}')
    return errors


def check_structure(root: Path) -> list[str]:
    errors: list[str] = []
    for zone in ZONES:
        base = root / zone
        if not base.is_dir():
            errors.append(f'missing required zone: {zone}/')
            continue
        for name in ('README.md', 'AGENTS.md'):
            if not (base / name).is_file():
                errors.append(f'missing scoped zone file: {zone}/{name}')
        agents = base / 'AGENTS.md'
        if agents.is_file():
            text = agents.read_text(encoding='utf-8').lower()
            for phrase in ('no production business logic', 'never weaken', 'stable dependency'):
                if phrase not in text:
                    errors.append(f'{zone}/AGENTS.md lacks {phrase!r}')
    for tier in TIERS:
        for name in ('README.md', 'test_placeholder_guard.py'):
            if not (root / 'tests' / tier / name).is_file():
                errors.append(f'missing test-tier artifact: tests/{tier}/{name}')
    return errors


def _python_logic(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeDecodeError):
        return True
    return any(not isinstance(node, (ast.Module, ast.Expr, ast.Constant)) for node in ast.walk(tree))


def _script_logic(path: Path) -> bool:
    text = path.read_text(encoding='utf-8', errors='replace')
    return any(re.search(pattern, text, re.I) for pattern in (
        r'\bimport\s+', r'\brequire\s*\(', r'\bclass\s+', r'\bfunction\s+', r'=>',
        r'\bfetch\s*\(', r'\b(?:SELECT|INSERT|UPDATE|DELETE)\b', r'\brouter\b', r'\bhandler\b',
    ))


def find_business_logic(root: Path) -> list[str]:
    findings: list[str] = []
    for zone in KERNEL_ZONES:
        for path in (root / zone).rglob('*'):
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            if path.name.endswith('.d.ts'):
                stripped = re.sub(r'/\*.*?\*/', '', path.read_text(encoding='utf-8'), flags=re.S).strip()
                if stripped != 'export {};':
                    findings.append(f'{rel}: declaration root is not empty')
                continue
            if path.suffix.lower() not in RUNTIME_SUFFIXES:
                continue
            if path.suffix.lower() == '.py' and _python_logic(path):
                reason = 'Python AST contains executable/import/definition nodes'
            elif path.suffix.lower() != '.py' and _script_logic(path):
                reason = 'import/script/handler heuristic matched'
            else:
                reason = 'runtime-source extension is prohibited'
            findings.append(f'{rel}: {reason}')
    return sorted(findings)


def check_contracts(root: Path) -> list[str]:
    errors: list[str] = []
    base = root / 'contracts' / 'draft'
    actual = {p.name for p in base.glob('*.contract.json')}
    errors += [f'missing contract shell: {name}' for name in sorted(set(CONTRACTS) - actual)]
    errors += [f'unregistered contract shell: {name}' for name in sorted(actual - set(CONTRACTS))]
    seen: set[str] = set()
    for name, (artifact_id, source_id) in CONTRACTS.items():
        path = base / name
        if not path.is_file():
            continue
        data = _json(path, errors)
        if not isinstance(data, dict):
            continue
        control = data.get('x-bopen-control')
        if not isinstance(control, dict):
            errors.append(f'{name} missing x-bopen-control')
            continue
        checks = {
            'artifact_id': control.get('artifact_id') == artifact_id,
            'status': control.get('status') == 'draft',
            'version': _draft_version(control.get('version')),
            'owner': bool(str(control.get('owner', '')).strip()),
            'stable_dependency': control.get('stable_dependency') is False,
            'work_package': control.get('work_package') == 'SKEL-P0-01',
        }
        errors += [f'{name} invalid {key}' for key, ok in checks.items() if not ok]
        if artifact_id in seen:
            errors.append(f'duplicate contract artifact_id: {artifact_id}')
        seen.add(artifact_id)
        trace = control.get('normative_traceability')
        if not isinstance(trace, list) or len(trace) != 1 or not isinstance(trace[0], dict):
            errors.append(f'{name} requires one traceability record')
        else:
            item = trace[0]
            if item.get('artifact_id') != source_id or item.get('link') != f'artifact:{source_id}':
                errors.append(f'{name} must trace to {source_id}')
            if not isinstance(item.get('requirement_ids'), list) or not item.get('section_refs'):
                errors.append(f'{name} traceability fields are incomplete')
        if data.get('type') != 'object' or data.get('additionalProperties') is not True:
            errors.append(f'{name} must remain an open object shell')
        errors += [f'{name} contains enforceable key {key}' for key in BANNED_SCHEMA_KEYS if key in data]
        surface = data.get('x-bopen-surface')
        if not isinstance(surface, dict) or surface.get('semantics_deferred') is not True:
            errors.append(f'{name} must explicitly defer semantics')
    manifest = _json(base / 'CONTRACT-MANIFEST.json', errors)
    if isinstance(manifest, dict):
        entries = manifest.get('contracts')
        expected_paths = {f'contracts/draft/{name}' for name in CONTRACTS}
        actual_paths = {entry.get('path') for entry in entries if isinstance(entry, dict)} if isinstance(entries, list) else set()
        if manifest.get('status') != 'draft' or manifest.get('stable_dependency') is not False or actual_paths != expected_paths:
            errors.append('contract manifest is incomplete or not draft/non-stable')
    return errors


def check_packages(root: Path) -> list[str]:
    errors: list[str] = []
    for name in PACKAGES:
        base = root / 'packages' / name
        for rel in ('README.md', 'package.json', 'types/index.d.ts'):
            if not (base / rel).is_file():
                errors.append(f'missing package file: packages/{name}/{rel}')
        if (base / 'src').exists() or (base / 'dist').exists():
            errors.append(f'packages/{name} contains src/ or dist/')
        data = _json(base / 'package.json', errors)
        if not isinstance(data, dict):
            continue
        if data.get('private') is not True or not _draft_version(data.get('version')) or data.get('types') != 'types/index.d.ts':
            errors.append(f'packages/{name} is not a private 0.x typed skeleton')
        if any(key in data for key in ('main', 'module', 'exports', 'bin')):
            errors.append(f'packages/{name} defines a runtime entry')
        if any(data.get(key) for key in ('dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies')):
            errors.append(f'packages/{name} declares dependencies')
        scripts = data.get('scripts')
        if not isinstance(scripts, dict) or not all(key in scripts for key in ('build', 'lint', 'test')):
            errors.append(f'packages/{name} lacks build/lint/test wiring')
        control = data.get('bopen')
        if not isinstance(control, dict) or control.get('status') != 'draft' or control.get('stableDependency') is not False:
            errors.append(f'packages/{name} lacks draft non-stable control')
    return errors


def check_test_guards(root: Path) -> list[str]:
    errors: list[str] = []
    for tier in TIERS:
        text = (root / 'tests' / tier / 'test_placeholder_guard.py').read_text(encoding='utf-8')
        if 'assert_tier_guard' not in text or f"'{tier}'" not in text:
            errors.append(f'tests/{tier}/test_placeholder_guard.py is not tier-bound')
    helper = root / 'tests' / '_support' / 'skeleton_guard.py'
    if not helper.is_file():
        return errors + ['missing tests/_support/skeleton_guard.py']
    text = helper.read_text(encoding='utf-8')
    for phrase in ('find_runtime_implementation', 'negative_tests_for_tier', 'BOPEN_NEGATIVE_TEST', 'raise AssertionError'):
        if phrase not in text:
            errors.append(f'skeleton_guard.py lacks {phrase}')
    return errors


def _payload_digest(entries: list[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: str(item['path'])):
        digest.update(str(entry['path']).encode())
        digest.update(b'\0')
        digest.update(str(entry['sha256']).encode())
        digest.update(b'\n')
    return digest.hexdigest()


def check_documentation(root: Path) -> list[str]:
    errors: list[str] = []
    required = (
        'docs/status/DOCUMENT-STATUS.md', 'docs/work-packages/SKEL-P0-01.md',
        'docs/evidence/EVD-SKEL-001.md', 'docs/manifests/SKEL-P0-01.package-manifest.json',
        'docs/ledgers/repository-change-ledger.ndjson', 'docs/traceability/SKEL-P0-01.traceability.json',
    )
    errors += [f'missing documentation surface: {rel}' for rel in required if not (root / rel).is_file()]
    manifest_path = root / 'docs/manifests/SKEL-P0-01.package-manifest.json'
    manifest = _json(manifest_path, errors)
    if isinstance(manifest, dict):
        files = manifest.get('files')
        if manifest.get('status') != 'draft' or manifest.get('work_package') != 'SKEL-P0-01' or not isinstance(files, list):
            errors.append('package manifest control is invalid')
        else:
            seen: set[str] = set()
            for entry in files:
                rel = entry.get('path') if isinstance(entry, dict) else None
                if not isinstance(rel, str) or rel in seen:
                    errors.append(f'invalid/duplicate manifest path: {rel!r}')
                    continue
                seen.add(rel)
                path = root / rel
                if not path.is_file() or entry.get('sha256') != _sha(path) or entry.get('bytes') != path.stat().st_size:
                    errors.append(f'package manifest mismatch: {rel}')
                if entry.get('status') != 'draft':
                    errors.append(f'package manifest entry not draft: {rel}')
            if manifest.get('file_count') != len(files) or manifest.get('payload_sha256') != _payload_digest(files):
                errors.append('package manifest count/payload digest mismatch')
    ledger_path = root / 'docs/ledgers/repository-change-ledger.ndjson'
    if ledger_path.is_file():
        previous: str | None = None
        sequence = 0
        entries: list[dict[str, object]] = []
        for index, line in enumerate(filter(str.strip, ledger_path.read_text(encoding='utf-8').splitlines()), start=1):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f'ledger line {index} invalid: {exc}')
                continue
            sequence += 1
            if entry.get('sequence') != sequence or entry.get('previous_entry_hash') != previous:
                errors.append(f'ledger line {index} is not append-only')
            claimed = entry.get('entry_hash')
            core = dict(entry)
            core.pop('entry_hash', None)
            if claimed != hashlib.sha256(_canonical(core)).hexdigest():
                errors.append(f'ledger line {index} hash mismatch')
            previous = claimed if isinstance(claimed, str) else None
            entries.append(entry)
        if entries and isinstance(manifest, dict):
            last = entries[-1]
            if last.get('manifest_sha256') != _sha(manifest_path) or last.get('payload_sha256') != manifest.get('payload_sha256'):
                errors.append('ledger does not bind current manifest/payload')
            if last.get('ledger_scope') != 'repository-preparation-not-root-governance':
                errors.append('ledger scope does not exclude root governance')
    return errors


def check_root_wiring(root: Path) -> list[str]:
    errors: list[str] = []
    data = _json(root / 'package.json', errors)
    if not isinstance(data, dict):
        return errors
    if data.get('private') is not True or not _draft_version(data.get('version')):
        errors.append('root package must remain private and 0.x')
    if data.get('packageManager') != 'pnpm@11.17.0':
        errors.append('packageManager must remain pnpm@11.17.0')
    scripts = data.get('scripts')
    if not isinstance(scripts, dict):
        return errors + ['root scripts are missing']
    validate = scripts.get('validate', '')
    for key in ('build', 'lint', 'test', 'validate:skeleton'):
        if key not in scripts or f'npm run {key}' not in validate:
            errors.append(f'validate chain is missing {key}')
    control = data.get('bopen')
    if not isinstance(control, dict) or control.get('status') != 'draft' or control.get('scope') != 'validate-chain-only':
        errors.append('root package control must be draft/validate-chain-only')
    return errors


def validate_repository(root: Path, mode: str = 'full') -> ValidationReport:
    groups = {
        'scope_boundary': check_scope_boundary,
        'structure': check_structure,
        'business_logic': find_business_logic,
        'contracts': check_contracts,
        'packages': check_packages,
        'test_guards': check_test_guards,
        'root_wiring': check_root_wiring,
        'documentation': check_documentation,
    }
    selected = tuple(groups) if mode == 'full' else ('scope_boundary', 'structure', 'business_logic', 'contracts', 'packages', 'root_wiring')
    errors: list[str] = []
    checks: dict[str, int] = {}
    for name in selected:
        findings = groups[name](root)
        checks[name] = len(findings)
        errors.extend(f'[{name}] {finding}' for finding in findings)
    return ValidationReport(errors, checks)


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate the additive draft-only bOPEN repository skeleton.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--mode', choices=('full', 'lint'), default='full')
    args = parser.parse_args()
    report = validate_repository(args.root.resolve(), args.mode)
    if report.ok:
        print(f'SKEL-P0-01 skeleton validation PASS ({len(report.checks)} check groups, 0 findings)')
        for name in report.checks:
            print(f'  - {name}: PASS')
        return 0
    print(f'SKEL-P0-01 skeleton validation FAIL ({len(report.errors)} findings)')
    for error in report.errors:
        print(f'  - {error}')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
