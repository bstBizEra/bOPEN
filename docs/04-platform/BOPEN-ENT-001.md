# BOPEN-ENT-001 — bOPEN Entitlement, Usage & Commercial Kernel Specification

**Document ID:** `BOPEN-ENT-001`
**Version:** `1.0.0`
**Status:** APPROVED FOR PHASE 3 IMPLEMENTATION

**Issued:** 2026-07-29
**Owner:** Architecture Authority & Engineering Authority
**Classification:** Normative Architecture & Commercial Entitlement Specification

---

## 1. Executive Summary

bOPEN establishes a strict separation between **Commercial Entitlement** and **Platform Authorization**:
* **Authentication** proves who the principal is.
* **Authorization (ReBAC)** evaluates whether the principal's active membership role permits the action.
* **Entitlement (BOPEN-ENT-001)** evaluates whether the tenant's commercial plan tier or subscription grant includes the commercial right to consume the capability.

$$\text{Decision} = \text{Authenticated} \land \text{Authorized (ReBAC)} \land \text{Entitled (Commercial Tier)} \land \text{Within Metered Quota}$$

---

## 2. Entitlement Value Types & Governed Plan Caps

Commercial entitlements support 6 distinct value models:

| Model | Type | Governance Constraint | Example Use Case |
| :--- | :--- | :--- | :--- |
| **Boolean** | `bool` | True / False | Feature gate (e.g. `has_advanced_analytics: true`). |
| **Static Value** | `string` | Frozen string enum | Configuration tier (e.g. `support_sla: "24x7"`). |
| **Capacity** | `int` | Explicit maximum integer cap | Physical limit (e.g. `max_storage_gb: 500`). |
| **Seat Count** | `int` | Explicit maximum seat integer | User limit (e.g. `max_active_members: 50`). |
| **Metered Allowance**| `int` | Explicit monthly integer quota | API call quota (e.g. `monthly_api_calls: 100000`). |
| **Time-Bound Grant** | `datetime` | Absolute ISO UTC timestamp | Temporary trial or promo grant (`trial_expires_at`). |

> **Governance Invariant**: "Enterprise unlimited" is prohibited. All plans MUST specify explicit, governed integer capacity ceilings (e.g., `10_000_000` API calls/month) to prevent unmetered system degradation.

---

## 3. Database Persistence & PostgreSQL Row-Level Security (RLS)

All entitlement grants, plan definitions, tenant overrides, usage balances, and quota reservations are stored in the platform kernel database under migration `002_phase3_entitlement_metering.sql`.

* **Tenant Isolation**: Every entitlement record contains a mandatory `tenant_id` column.
* **Database RLS Enforcement**: Row-Level Security policies ensure tenant queries cannot inspect or mutate cross-tenant entitlement balances.
* **Transactional Outbox**: Usage metering events are committed to a transactional outbox table before dispatching to downstream aggregation pipelines.

---

## 4. Reason Code & HTTP Status Code Mapping

When an entitlement evaluation fails, the engine returns a deterministic decision conforming to [entitlement-reason-codes.json](file:///c:/laragon/www/bopen/contracts/schemas/entitlement-reason-codes.json):

| Reason Code | HTTP Status | Meaning |
| :--- | :---: | :--- |
| `ENTITLEMENT_ALLOWED` | 200 | Entitlement valid and quota available. |
| `DENY_UNSUPPORTED_CAPABILITY` | 403 | Capability not registered in platform catalog. |
| `DENY_NOT_ENTITLED` | 403 | Capability excluded from tenant subscription plan tier. |
| `DENY_FEATURE_DISABLED` | 403 | Feature rollout toggle disabled for tenant. |
| `DENY_QUOTA_EXCEEDED` | 429 | Metered monthly/daily allowance exhausted. |
| `DENY_RATE_LIMIT_EXCEEDED` | 429 | Real-time burst rate limit threshold exceeded. |

---

## 5. Required Contract Schemas

* [entitlement-decision.schema.json](file:///c:/laragon/www/bopen/contracts/schemas/entitlement-decision.schema.json)
* [usage-metered-event.schema.json](file:///c:/laragon/www/bopen/contracts/schemas/usage-metered-event.schema.json)
* [quota-reservation.schema.json](file:///c:/laragon/www/bopen/contracts/schemas/quota-reservation.schema.json)
* [rate-limit-decision.schema.json](file:///c:/laragon/www/bopen/contracts/schemas/rate-limit-decision.schema.json)
* [entitlement-reason-codes.json](file:///c:/laragon/www/bopen/contracts/schemas/entitlement-reason-codes.json)
