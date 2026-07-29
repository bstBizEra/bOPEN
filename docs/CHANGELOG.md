# Documentation Changelog

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
