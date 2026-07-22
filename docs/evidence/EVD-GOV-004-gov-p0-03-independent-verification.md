# EVD-GOV-004 — Independent Exact-SHA Verification of GOV-P0-03 Candidate

**Version:** 0.1
**Status:** Draft
**Work package:** GOV-P0-04 (Proposed; not accepted)
**Generated:** 2026-07-22
**Maker under review:** Codex root GOV-P0-03 maker (`BST-Codex-Motor`)
**Independent checker:** Claude (BST-SA Motor worker agent; claude-sonnet-5)
**Checker independence:** The checker is a different agent vendor, runtime and session from the maker; the checker authored none of the reviewed commits.
**Candidate commit SHA:** `a29ec1d8ab28d38621dc4db176b7b2abf2ea44cb`
**Candidate tree SHA:** `ff3cb910385f04ccc3b0e077cf4329b79f7fe3f6`
**Branch:** `codex/GOV-P0-03-root-controls`
**Worktree state:** clean at exact candidate SHA before and during verification
**Verdict:** `ACCEPT_EXACT_SHA` (technical evidence only)

## Commands and results

All commands executed at the exact candidate SHA on Windows (`C:\laragon\www\bopen-worktrees\gov-p0-03-root-controls`):

- `python tools/validate_root_control_surfaces.py` — exit 0; 5 root controls and 11 manifest-bound package files PASS.
- `python tools/validate_repository.py` — exit 0; 27 mandatory paths PASS.
- `python tools/validate_contracts.py` — exit 0; 19 machine-readable contracts PASS.
- `python tools/validate_program_controls.py` — exit 0; 7 draft registers PASS fail-closed semantic validation.
- `python tools/validate_pg_g0_authority_docket.py` — exit 0; `NOT_READY`, zero `validation_errors`, 18 blockers, PG-G0 false, production authorization false.
- `python tools/check_clean_room.py` — exit 0.
- `python tools/check_secrets.py` — exit 0.
- `python tools/check_supply_chain.py` — exit 0.
- `python -m unittest discover -s tests -p 'test_*.py'` — 160/160 passed.
- `python tools/report_program_g0.py --check` — exit 0; committed readiness artifact matches deterministic generation.
- `git diff --check` — clean.

## Disclosed observations (not candidate defects)

**Test-fixture fragility (for the GOV-P0-02 maker):** in `tests/governance/test_pg_g0_authority_docket.py`, the `committed_file` mock inside `validate()` resolves `ROOT / relative` before the temp fixture root. The five identity negative tests therefore fail spuriously as soon as a real file exists at `docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json` — which is exactly the state Step 1 of the operator packet will create. The mock should prefer the temp root. Verified empirically at this base: adding a draft register at that path produced 5 failures; keeping the path vacant restores 160/160.


`python tools/generate_document_manifest.py --check` exits 1: the root `docs/DOCUMENT-MANIFEST.json` snapshot (250 records) predates GOV-P0-02/03 (a fresh generation yields 261). This is a known, deliberately unresolved state pending the DEC-0012 manifest disposition (deterministic replacement vs immutable versioned snapshots). GOV-P0-02/03 followed the versioned-snapshot convention (`docs/manifests/`) rather than regenerating the root manifest. No validator required by GOV-P0-03 fails on this state.

## Decision boundary

This receipt is independent technical verification only. It does not accept GOV-P0-03, approve DEC-0012, pass any research, bootstrap or program gate, or authorize merge, release, runtime or production implementation. Human authority dispositions remain pending and are consolidated in `docs/00-governance/PG-G0-OPERATOR-DECISION-PACKET.md`.

## Self-certification

```yaml
self_certification:
  agent_id: claude-sonnet-5 (BST-SA Motor)
  peer_agent_id: BST-Codex-Motor
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```
