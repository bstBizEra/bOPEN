---
name: bopen-authority
description: Execute and verify bOPEN authority bootstrap checks, evidence-driven gate realizations, contract freezes, and multi-agent governance controls across Claude, Codex, Gemini, and all bOPEN AI agents. Use for verifying repository authority, running authority bootstrap checks, evaluating evidence-driven phase entry gates, and auditing governance compliance.
---

# bOPEN Authority Skill (`bopen-authority`)

The `bopen-authority` skill provides canonical verification for repository governance, contract freezes, phase entry gates, and multi-agent instructions across Claude, Codex, Gemini, Kimi, DeepSeek, and all participating AI engines.

## Operating Boundary

- **Evidence-Driven Gate Realization (`AGENTS.md` §19.6)**: Gate authorization, work-package entry, and phase progression are realized directly through empirical technical evidence (100% passing automated test suites, contract schema validation, repository validation tools, clean-room checks, and evidence packages).
- **Source of Truth Hierarchy**:
  $$\text{Approved Normative Spec} > \text{Approved ADR} > \text{Versioned Contract} > \text{Accepted Work Package} > \text{Implementation} > \text{Test Evidence}$$
- **Verification Commands**:
  - Authority Bootstrap Check: `python tools/check_authority_bootstrap.py`
  - Canonical Test Suite: `python tools/run_tests.py`
  - Repository Validator: `python tools/validate_repository.py`
  - Clean-Room Verifier: `python tools/check_clean_room.py`
  - Document Manifest Index: `python tools/generate_document_manifest.py`

## Workflow

1. **Verify Governance Rules**: Inspect `AGENTS.md` (root and scoped) and `docs/00-governance/AGENT-ALIGNMENT.md`.
2. **Execute Authority Bootstrap Check**:
   ```bash
   python tools/check_authority_bootstrap.py
   ```
3. **Execute Canonical Test Suite**:
   ```bash
   python tools/run_tests.py
   ```
4. **Validate Repository & Clean-Room Boundaries**:
   ```bash
   python tools/validate_repository.py
   python tools/check_clean_room.py
   ```
5. **Verify Decision & Artifact Registers**: Ensure `docs/ARTIFACT-REGISTER.md`, `docs/DOCUMENT-STATUS.md`, and `docs/decisions/DECISION-REGISTER.md` match the current phase state.

## Verdicts

- `GO_ON_EVIDENCE`: Empirical test evidence (100% passing tests, valid contract schemas, passing repository validators) satisfies all phase entry criteria.
- `HOLD`: Verification failure or missing normative specifications require contract freeze or repair prior to execution.
