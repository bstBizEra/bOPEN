# bOPEN Future Development Plan v1.0

**Document ID:** `BOPEN-PROD-PLAN-001`  
**Version:** `1.0`  
**Status:** Approved Roadmap Plan  
**Issued:** 2026-07-29  
**Owner:** Product Authority & Engineering Authority  
**Classification:** Strategic Development & Execution Plan  

---

## 1. Executive Summary

Having successfully cleared **Gate G7** and implemented the **Phase 1 Platform Kernel Vertical Slice** ([packages/kernel-core/](file:///c:/laragon/www/bopen/packages/kernel-core) & [services/platform-kernel/](file:///c:/laragon/www/bopen/services/platform-kernel)), this plan details the future engineering milestones for Phase 2, Phase 3, and Phase 4.

---

## 2. Phase-by-Phase Execution Milestones

### Phase 2 — Membership & Enterprise Onboarding (Immediate Focus)

**Goal**: Support invitation workflows, tenant context switching, delegated partner access, and membership state machines.

| Milestone ID | Target Deliverable | Governing Specs & Schemas | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **MILE-2.1** | Principal Invitation Engine | [membership-transition.json](../../contracts/schemas/membership-transition.json) | Issue, validate, and expire tenant member invitations (`invited` -> `active`). |
| **MILE-2.2** | Tenant Context Switching API | [tenant-context.json](../../contracts/schemas/tenant-context.json) | Switch active tenant context seamlessly via authenticated API headers. |
| **MILE-2.3** | Membership Revocation & Offboarding | [BOPEN-TENANT-001](../04-platform/BOPEN-TENANT-001.md) | Revoking membership instantly revokes active context & denies access. |
| **MILE-2.4** | Delegated Cross-Tenant Access | [BOPEN-AUTHZ-001](../04-platform/BOPEN-AUTHZ-001.md) | Time-bounded partner/support grants with auto-expiry. |

---

### Phase 3 — Capability & Commercial Entitlement Kernel

**Goal**: Formalize module registration, commercial licensing, quotas, and feature flags.

| Milestone ID | Target Deliverable | Governing Specs | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **MILE-3.1** | Capability Registry Service | `BOPEN-MOD-001` | Dynamic registration of module capability manifests and dependencies. |
| **MILE-3.2** | Commercial Entitlement Engine | `BOPEN-ENT-001` | Enforce plan tier limits, feature rollout flags, and subscription checks. |
| **MILE-3.3** | Quota & Usage Metering | `BOPEN-ENT-001` | Real-time usage event tracking against tenant subscription quotas. |

---

### Phase 4 — Common Business Foundation & Satellite Integration

**Goal**: Build reusable business foundation microservices and integrate initial satellite products.

| Milestone ID | Target Deliverable | Governing Specs | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **MILE-4.1** | Party & Relationship Service | [BOPEN-PARTY-001](../05-foundation/BOPEN-PARTY-001-DRAFT.md) | Person, organization, and B2B vendor/supplier graph management. |
| **MILE-4.2** | Document & Location Foundations | `docs/05-foundation/` | Document storage signatures & geofence location management. |
| **MILE-4.3** | bPro & bFleet Product Integration | `docs/10-products/` | Compose first commercial product offerings on top of bOPEN kernel. |

---

## 3. Quality & Governance Invariants

Every future milestone must satisfy:
1. **Contract-First**: OpenAPI / JSON Schema contracts defined before code.
2. **Deny-by-Default**: ReBAC/ABAC authorization checks on every endpoint.
3. **Physical Tenant Isolation**: PostgreSQL Row-Level Security policies active.
4. **Validation Suite**: `python tools/validate_repository.py` and `python tools/check_clean_room.py` passing cleanly.
