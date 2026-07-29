# BOPEN-P3-001 Work Package — Phase 3 Capability & Commercial Entitlement Kernel Execution Plan

**Work Package ID:** `BOPEN-P3-001`
**Version:** `1.0.0`
**Status:** APPROVED FOR EXECUTION (GO ON EVIDENCE)
**Issued:** 2026-07-29
**Governing Specifications:** `BOPEN-MOD-001`, `BOPEN-ENT-001`
**Owner:** Platform Kernel Engineering Authority

---

## 1. Executive Summary

This work package governs **Phase 3 (Capability & Commercial Entitlement Kernel)**. It establishes the capability registry, subscription entitlement evaluator, real-time usage metering pipeline, rate-limiting controls, and database schema `002_phase3_entitlement_metering.sql`.

Per `AGENTS.md` §19.6 and `DEC-P3-ENTRY`, Phase 3 execution is **AUTHORIZED ON EVIDENCE**.

---

## 2. Governance Baseline & Roles (`WP-P3-00`)

* **Maker**: Platform Kernel Engineering Team
* **Independent Checkers**: Claude & Codex AI Subagents
* **Security Authority**: Security Review Team
* **Data Authority**: Database & Isolation Review Team
* **Product Authority**: Product Architecture Team
* **Completion Authority**: Engineering Authority

---

## 3. Work Package Structure

### `WP-P3-01` — Phase 3 Contract & ADR Freeze (`COMPLETED`)
* Resolved ADRs for capability resolution, entitlement precedence, quota windows, and database isolation.
* Frozen JSON schemas under `contracts/schemas/`:
  - `module-manifest.schema.json`
  - `capability-registration.schema.json`
  - `entitlement-decision.schema.json`
  - `usage-metered-event.schema.json`
  - `quota-reservation.schema.json`
  - `rate-limit-decision.schema.json`
  - `entitlement-reason-codes.json`

### `WP-P3-02` — Acceptance Test Suite First
Author negative and positive contract tests under `tests/unit/` and `tests/integration/` prior to kernel implementation:
* Unregistered/unapproved capability denial (`DENY_UNSUPPORTED_CAPABILITY`).
* Tenant context missing or unvalidated (`DENY_INVALID_CONTEXT`).
* Quota limit breach (`DENY_QUOTA_EXCEEDED` -> HTTP 429).
* Rate limit breach (`DENY_RATE_LIMIT_EXCEEDED` -> HTTP 429).
* Cross-tenant entitlement isolation violation.

### `WP-P3-03` — Capability & Module Registry (`kernel_core/capability.py`)
Implement capability lookup, dependency graph validation, and catalog discovery.

### `WP-P3-04` — Commercial Entitlement Evaluator (`kernel_core/entitlement.py`)
Implement tenant subscription plan lookup, overrides, and `is_entitled(context, capability_id)` decision engine.

### `WP-P3-05` — Usage Metering & Outbox (`platform_kernel/metering.py`)
Implement high-throughput transactional outbox event ingestion for metered allowances.

### `WP-P3-06` — Database Schema & RLS (`002_phase3_entitlement_metering.sql`)
Write append-only PostgreSQL migration defining `tenant_entitlement_plans`, `tenant_entitlement_overrides`, `usage_meter_balances`, and tenant isolation RLS policies.

### `WP-P3-07` — Evidence Package & Exit Gate (`docs/evidence/phase-3/`)
Generate evidence manifest, invariant traceability CSV, test execution receipts, and completion decision.
