# Phase 2 — Membership & Enterprise Onboarding Completion Decision

**Document ID:** `EVD-P2-DECISION-001`  
**Version:** `1.0.1`  
**Status:** **CORRECTED MAKER EVIDENCE / AUTHORITY ACCEPTANCE NOT PROVEN**  
**Issued:** 2026-07-29  
**Work Package:** `BOPEN-P2-001`  
**Governing Standard:** `BOPEN-IDP-001`  
**Completion Authority:** Pending an identifiable authority receipt  

---

## 1. Executive Decision

Phase 2 (**Membership & Enterprise Onboarding**) is technically implemented and the
current repository test suite passes. The previous v1.0 statement that Phase 2 had received
signed conditional acceptance is not supported by an identifiable authority receipt,
independent checker receipt, or exact candidate commit/tree.

This document therefore records **maker-side technical evidence only**. It does not close
`DEC-0009`, ratify `ADR-0010`..`ADR-0019`, open the Phase 3 implementation gate, or authorize
production deployment.

---

## 2. Governance Roles & Accountability

| Role | Assigned Entity | Status |
| :--- | :--- | :--- |
| **Maker** | Platform Kernel Engineering Team | Implemented MILE-2.1..2.5 |
| **Technical verifier** | Codex | Reproduced the current tests; not an independent acceptance authority |
| **Independent Checker** | Pending | No exact-candidate checker receipt is attached |
| **Security Reviewer** | Pending | A passing prohibited-field test is not a Security Authority approval |
| **Completion Authority** | Pending | No identifiable signed acceptance receipt is attached |

---

## 3. Recorded Conditions & Technical Risk Register

| Decision ID | Condition / Risk Description | Disposition / Mitigating Control |
| :--- | :--- | :--- |
| **D-P2-002** | Token digest pepper defense-in-depth | Unkeyed SHA-256 remains implemented. Any acceptance or deferral requires Engineering and Security Authority disposition. |
| **D-P2-007** | ES256 KMS JWKS signing key custody | The deterministic test signer is non-production. ES256, external key custody, JWKS, and rotation remain production blockers. |
| **D-P2-015** | Transactional outbox audit durability | Audit contract violations fail closed, but no durable outbox exists. Migration `001_tenant_isolation_baseline.sql` contains no outbox or audit table. |

---

## 4. Verification Receipts

* **Canonical Repository Test Suite**: **PASSED (151/151 OK)** via `python tools/run_tests.py`
  * Unit: 124
  * Integration: 11
  * Contracts: 8
  * Isolation: 3
  * Governance: 5
* **Repository Validation**: **PASS** via `python tools/validate_repository.py`
* **Clean-Room Verification**: **PASS** via `python tools/check_clean_room.py`
* **Prohibited-Field Secret Scan**: **0 Leaks** (`test_P2_T066_prohibited_field_scan_over_all_evidence`)

The earlier 145-test figure remains a historical pre-repair baseline. The canonical suite now
contains six additional Phase 3 contract-control tests and MUST report 151 tests.

---

## 5. Evidence Binding and Authority Boundary

| Field | Observed value |
|---|---|
| Repository | `C:\laragon\www\bopen` |
| Target branch | `claude/BOPEN-P2-001-membership-onboarding` |
| Base commit | `e65baf1dcfd84a101513719594dccf34bf8eacbc` |
| Base tree | `9aad32031278f9a0a0beba01b57442ed0b6016b8` |
| Candidate binding | **UNCOMMITTED WORKTREE — no immutable candidate tree exists yet** |
| Production authority | **NOT PROVEN / NOT GRANTED** |
| Phase 3 implementation authority | **NOT PROVEN / NOT GRANTED** |

The next authority-bearing review MUST bind the complete candidate to an exact commit and tree,
attach separately attributable checker and authority receipts, and preserve the unresolved
production conditions.

---

## 6. Correction Record

- **Source:** Direct repository inspection and deterministic local verification.
- **Timestamp:** `2026-07-29T06:57:43Z`.
- **Agent ID:** `Codex`.
- **Reason:** Correct unsupported checker/authority claims, the incorrect transactional-outbox
  assertion, and the canonical-runner test count.
- **Benefit of old phase:** The v1.0 record collected the intended roles, risks, and verification
  commands in one place.
- **Expected outcome of new phase:** Technical evidence remains usable without being mistaken for
  independent acceptance, architecture approval, deployment authority, or Phase 3 source authority.
