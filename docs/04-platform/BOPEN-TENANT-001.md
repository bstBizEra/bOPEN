# BOPEN-TENANT-001 — bOPEN Tenant, Organization & Isolation Specification v1.0

**Document ID:** `BOPEN-TENANT-001`  
**Version:** `1.0`  
**Status:** Approved for Phase 1 implementation  
**Issued:** 2026-07-29  
**Owner:** Architecture & Data Authorities  
**Classification:** Normative Specification  

---

## 1. Core Distinctions

```text
Tenant != Organization != Legal Entity
Membership != Role != Permission != Entitlement
```

## 2. Approved Lifecycle States

- **Tenant States**: `draft`, `pending_verification`, `approved`, `provisioning`, `active`, `restricted`, `suspended`, `cancellation_pending`, `terminated`, `retention`, `purged`.
- **Membership States**: `invited`, `active`, `suspended`, `declined`, `expired`, `revoked`, `left`, `removed`.
