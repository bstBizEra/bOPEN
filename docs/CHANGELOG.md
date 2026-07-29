# Documentation Changelog

## 2026-07-29 — Evidence and Phase 3 contract-control repair

- Corrected `EVD-P2-DECISION-001` from an unsupported conditional-acceptance claim to
  maker-side technical evidence with independent, security, and completion authority pending.
- Corrected `D-P2-015`: migration `001_tenant_isolation_baseline.sql` contains no durable
  transactional outbox.
- Repaired `tools/run_tests.py` so contracts are mandatory and category totals are reported.
- Added six Phase 3 schema-control tests and tightened the seven Phase 3 schemas for lifecycle,
  context, idempotency, quota, reason-code, and rate-limit consistency.
- Aligned artifact, coverage, status, traceability, and work-package registers with the
  Phase 3 implementation hold. No Phase 3 production source or migration was created.
- **Source:** Direct repository inspection and deterministic local verification.
  **Timestamp:** `2026-07-29T06:57:43Z`. **Agent ID:** `Codex`.
- **Reason:** Repair evidence-integrity and contract-test gaps before any Phase 3 entry gate.
  **Benefit of old phase:** Earlier artifacts collected the intended milestones, roles, and
  risks. **Expected outcome:** Verifiable contract-freeze evidence that cannot be mistaken for
  approval, production authority, or Phase 3 implementation authority.

## 2026-07-29 — Phase 2 entry and implementation

- Bound `BOPEN-IDP-001` (Approved for Phase 2) into `docs/04-platform/`; marked
  `BOPEN-IDP-001-DRAFT.md` **Superseded** with a pointer to the replacement (WP-P2-01).
- Bound `BOPEN-P2-001` execution plan into `docs/work-packages/`; registered
  `BOPEN-P1-001` and `BOPEN-P2-001` in the work-package register.
- Recorded `DEC-0007` (adopt IDP-001), `DEC-0008` (bind P2-001) and `DEC-0009`
  (ADR/decision resolution — **Open, blocking**).
- Added `AGENTS.md` §3.1 recording the Phase 2 implementation hold.
- Implemented `MILE-2.1`..`MILE-2.5` (invitation engine, membership state machine,
  tenant context switching, enterprise IdP/SCIM bridge, delegated cross-tenant access)
  with 145 passing tests.
- **Implementation proceeded ahead of the `BOPEN-P2-001` §23 entry gate on explicit
  operator direction.** The deviation, the thirteen decisions taken by implementation
  default, and the known gaps are recorded in
  [`docs/evidence/phase-2/provisional-decisions.md`](evidence/phase-2/provisional-decisions.md).

## 2026-07-13 - local preparation

- Prepared downloaded BOPEN-BOOT-001 full pack for local version control.
- Fixed `pnpm test:governance` quoting so unittest discovery works in Windows PowerShell.
- Added local bootstrap validation evidence for BOOT-P0-05.

## 2026-07-12 — v1.0

- Created BOPEN-BOOT-001 full AGENTS.md and documentation bootstrap pack.
