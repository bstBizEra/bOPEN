#!/usr/bin/env python3
from pathlib import Path
import json, re, sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]

required=[
'AGENTS.md','BOPEN-BOOT-001.md','README.md','CONTRIBUTING.md','SECURITY.md','GOVERNANCE.md',
'docs/README.md','docs/DOCUMENT-STATUS.md','docs/DOCUMENT-COVERAGE.md','docs/GLOSSARY.md','docs/TRACEABILITY-MATRIX.md',
'docs/exceptions/EXCEPTION-REGISTER.md',
'apps/AGENTS.md','services/AGENTS.md','packages/AGENTS.md','contracts/AGENTS.md','infrastructure/AGENTS.md','tests/AGENTS.md','research/AGENTS.md','docs/AGENTS.md',
'docs/02-requirements/BOPEN-REQ-001-DRAFT.md','docs/03-architecture/BOPEN-ARCH-001-DRAFT.md',
'docs/04-platform/BOPEN-TENANT-001-DRAFT.md','docs/04-platform/BOPEN-AUTHZ-001-DRAFT.md',
'docs/04-platform/BOPEN-ENT-001-DRAFT.md','docs/04-platform/BOPEN-MOD-001-DRAFT.md','docs/07-security/BOPEN-SEC-001-DRAFT.md']
required += [
'docs/decisions/DEC-0011.md',
'docs/evidence/EVD-RES-004-g3-runtime-design.md',
'docs/resources/open-source-research/BOPEN-RES-001/02-execution/g3-runtime-pack-design.md',
'research/sources/boxyhq-g3-runtime-design.schema.json',
'research/sources/boxyhq-g3-runtime-design.json',
'tools/validate_research_g3_design.py',
'tools/report_research_g3_design.py',
'tools/generate_research_artifact_inventory.py',
'tests/governance/test_research_g3_design_controls.py',
]
required += [
'docs/work-packages/GOV-P0-03.md','docs/evidence/EVD-GOV-003-root-control-surfaces.md',
'docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json','tools/validate_root_control_surfaces.py',
'docs/work-packages/QUAL-P0-00.md','docs/evidence/EVD-QUAL-001-qualification-common.md',
'docs/manifests/QUAL-P0-00-PACKAGE-MANIFEST.json','tools/validate_qualification_common.py',
'docs/work-packages/TECH-P0-01.md','docs/evidence/EVD-TECH-001-technology-qualification.md',
'docs/manifests/TECH-P0-01-PACKAGE-MANIFEST.json','tools/validate_technology_qualification.py',
'docs/work-packages/QUAL-P0-02.md','docs/evidence/EVD-QUAL-002-identity-qualification.md',
'docs/manifests/QUAL-P0-02-PACKAGE-MANIFEST.json','tools/validate_identity_qualification.py',
'docs/work-packages/QUAL-INTEG-001.md','docs/evidence/EVD-QUAL-INTEG-001-review-candidate.md',
'docs/manifests/RES-P0-05-DOCUMENT-MANIFEST.json',
'docs/manifests/QUAL-INTEG-001-INTEGRATION-MANIFEST.json',
'docs/manifests/QUAL-INTEG-001-AGGREGATE-MANIFEST.json',
'docs/manifests/MANIFEST-INDEX.jsonl','tools/generate_document_manifest.py',
'tools/validate_qual_integ_001.py','tools/report_qual_integ_001.py',
'tests/governance/test_qual_integ_001.py','artifacts/validation/qual-integ-001-readiness.json',
]
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

# QUAL-INTEG-001 shared validation surfaces must preserve the complete accepted DAG.
validation_tokens = [
    'validate_root_control_surfaces.py', 'validate_qualification_common.py',
    'validate_technology_qualification.py', 'validate_identity_qualification.py',
    'validate_research_g3_design.py', 'generate_document_manifest.py --check-index',
    'validate_qual_integ_001.py', 'report_qual_integ_001.py --check',
    'check_clean_room.py', 'check_secrets.py', 'check_supply_chain.py',
]
for rel in ['package.json','.github/workflows/bootstrap-governance.yml','.gitea/workflows/governance.yml']:
    path=ROOT/rel
    text=path.read_text(encoding='utf-8') if path.exists() else ''
    for token in validation_tokens:
        if token not in text: errors.append(f'VALIDATION DAG TOKEN MISSING {rel}: {token}')
for rel in ['.github/workflows/bootstrap-governance.yml','.gitea/workflows/governance.yml']:
    text=(ROOT/rel).read_text(encoding='utf-8') if (ROOT/rel).exists() else ''
    if 'fetch-depth: 0' not in text: errors.append(f'FULL GIT HISTORY CHECKOUT MISSING: {rel}')

if errors:
    print('bOPEN repository validation: FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('bOPEN repository validation: PASS')
print(f'Checked {len(required)} mandatory paths and governance invariants.')
