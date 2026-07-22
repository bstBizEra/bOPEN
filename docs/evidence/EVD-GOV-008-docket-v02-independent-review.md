# EVD-GOV-008 — Independent Exact-SHA Review of the PG-G0 Authority Docket v0.2 Candidate

**Version:** 0.1
**Status:** Draft technical evidence
**Work package:** GOV-P0-04 (Proposed; not accepted)
**Generated:** 2026-07-23
**Maker under review:** BST-Codex-Motor (docket v0.2 batch maker; EVD-GOV-007)
**Independent checker:** Claude (BST-SA Motor worker agent; claude-fable-5 session)
**Checker independence:** Different agent vendor, runtime and session; the checker authored none of the reviewed commit. The checker authored parts of the substrate lineage (GOV-P0-04 maker), which is disclosed; the reviewed delta `26bea09..b929821` is entirely Codex-authored.
**Candidate commit SHA:** `b929821af83ff774be2bfb10dcb5588d862dcaf2`
**Candidate tree SHA:** `e1c91773eddc5e1aa02dc048e7708d3684266599`
**Substrate (parent):** `26bea090c0aca14f1337c4be1a146fd48bb1f626`
**Branch:** `codex/GOV-P0-04-docket-v02`
**Worktree state:** clean at the exact candidate SHA throughout the review
**Verdict:** `ACCEPT_EXACT_SHA` (technical evidence only)

## Commands and results (at the exact candidate SHA)

- `npm run validate` — exit 0: repository (27 paths), contracts, program controls (7 registers), authority identity register, program-G0 report check, docket check, versioned manifest check (273 records), clean-room, secrets, supply-chain all PASS.
- `python -m unittest discover -s tests -p 'test_*.py'` — 180/180 passed.
- `python tools/validate_pg_g0_authority_docket.py` — `NOT_READY`, `validation_errors: []`, 30 blockers, all human-pending; PG-G0 false; production authorization false.
- `git diff --check` — clean.

## Substance verification

1. **Matrix v0.2 adoption surface:** the bound `registers/AUTHORITY-MATRIX.json` carries the proposal's ten entries (three new actions `APPROVE_GOVERNANCE_BASELINE`, `APPROVE_PROGRAM_REGISTERS`, `PASS_PG_G0`; `ACCEPT_WORK_ITEM` concurrence aligned to prose as `Owning Artifact Authority`) while remaining `0.2.0-draft` with null approval provenance — content staged, adoption disposition correctly pending.
2. **Docket v0.2:** version `0.2.0-draft`, state `PENDING_HUMAN_DECISIONS`; zero signed decision requests; `effective_outcome` all false; every `non_authority_flags` entry false; ten `PG-G0-PREP` surfaces plus the five `PG-G0-DEC` decisions all `PENDING`.
3. **Binding inventory:** all 34 records in `PG-G0-AUTH-001-V0.2-BINDING-INVENTORY.json` verified byte-exact against the substrate commit `26bea09` — zero SHA-256 mismatches.
4. **Identity register integrity:** the operator-approved `AUTHORITY-IDENTITY-REGISTER.json` (approved_by `HUMAN-OPERATOR-001`) is byte-identical to its Batch 1 state; the candidate does not touch it.
5. **Signing Pass 2 surface:** enumerates the thirteen Batch 2 dispositions unsigned, with prerequisites requiring this independent receipt before any signature, and an atomic append-only five-ledger activation template that rewrites no genesis bytes.
6. **Root-control activation revision:** the validator/schema revision admits an appended activation event only as a single atomic, identically-signed append across all five ledgers; the Draft/Inactive genesis constants remain enforced for the pre-activation prefix.

## Decision boundary

This receipt is independent technical verification of the exact candidate SHA only. It does not sign any Batch 2 disposition, approve BOPEN-GOV-001, DEC-0013 or any register, accept GOV-P0-01 or GOV-P0-04, activate a ledger, pass BOOT-B7 or PG-G0, or authorize merge, release, runtime or production implementation. All thirteen dispositions remain the operator's.

## Self-certification

```yaml
self_certification:
  agent_id: Claude BST-SA Motor (claude-fable-5)
  peer_agent_id: BST-Codex-Motor
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  candidate_verdict: ACCEPT_EXACT_SHA
  ready_for_operator_review: true
```
