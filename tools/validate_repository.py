#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
from validate_skill_registry import validate as validate_skill_registry

ROOT=Path(__file__).resolve().parents[1]
errors=[]

required=[
'AGENTS.md','BOPEN-BOOT-001.md','README.md','CONTRIBUTING.md','SECURITY.md','GOVERNANCE.md',
'docs/README.md','docs/DOCUMENT-STATUS.md','docs/DOCUMENT-COVERAGE.md','docs/GLOSSARY.md','docs/TRACEABILITY-MATRIX.md',
'apps/AGENTS.md','services/AGENTS.md','packages/AGENTS.md','contracts/AGENTS.md','infrastructure/AGENTS.md','tests/AGENTS.md','research/AGENTS.md','docs/AGENTS.md',
'docs/02-requirements/BOPEN-REQ-001-DRAFT.md','docs/03-architecture/BOPEN-ARCH-001-DRAFT.md',
'docs/04-platform/BOPEN-TENANT-001-DRAFT.md','docs/04-platform/BOPEN-AUTHZ-001-DRAFT.md',
'docs/04-platform/BOPEN-ENT-001-DRAFT.md','docs/04-platform/BOPEN-MOD-001-DRAFT.md','docs/07-security/BOPEN-SEC-001-DRAFT.md']
for rel in required:
    if not (ROOT/rel).exists(): errors.append(f'MISSING: {rel}')

root_agents=(ROOT/'AGENTS.md').read_text(encoding='utf-8') if (ROOT/'AGENTS.md').exists() else ''
for phrase in ['Clean-room controls','Architectural invariants','Stop conditions','Tenant data safety']:
    if phrase not in root_agents: errors.append(f'AGENTS missing required section: {phrase}')

# No committed upstream source except permitted marker files
up=ROOT/'research/upstream'
if up.exists():
    for p in up.rglob('*'):
        if p.is_file() and p.name not in {'README.md','.gitkeep'}:
            errors.append(f'UPSTREAM SOURCE PRESENT: {p.relative_to(ROOT)}')

# Controlled BOPEN docs should contain metadata markers
for p in (ROOT/'docs').rglob('BOPEN-*.md'):
    txt=p.read_text(encoding='utf-8',errors='replace')
    if '**Status:**' not in txt and p.name not in {'BOPEN-RES-001.md'}:
        errors.append(f'DOCUMENT STATUS MISSING: {p.relative_to(ROOT)}')

# Draft JSON schemas must parse
for p in (ROOT/'docs/06-contracts').rglob('*.json'):
    try: json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'INVALID JSON {p.relative_to(ROOT)}: {e}')

for error in validate_skill_registry():
    errors.append(f'SKILL REGISTRY: {error}')

if errors:
    print('bOPEN repository validation: FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('bOPEN repository validation: PASS')
print(f'Checked {len(required)} mandatory paths, governance invariants and the closed skill registry.')
