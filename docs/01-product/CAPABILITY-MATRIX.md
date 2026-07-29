# bOPEN Capability & Architecture Matrix v1.0

**Document ID:** `BOPEN-PROD-MATRIX-001`  
**Version:** `1.0`  
**Status:** Approved Specification  
**Issued:** 2026-07-29  
**Owner:** Product Authority & Architecture Authority  
**Classification:** Strategic Product & Governance Matrix  

---

## 1. Platform Kernel Modules Matrix (12 Modules)

| Module Name | Strategic Phase | Status | Core Capability | Security & Data Isolation | Target Satellite Integrations |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Identity & Principal** | Phase 1 | **Approved & Built** | Authenticates global entities (human, service, device, agent). | Global UUID; IdP SAML/OIDC JWT claims (`sub`). | All Products |
| **Tenant Boundary** | Phase 1 | **Approved & Built** | Commercial, legal, and security isolation boundary. | PostgreSQL RLS (`001_tenant_isolation_baseline.sql`). | All Products |
| **Organization Graph** | Phase 1 | **Approved & Built** | Corporate legal entity hierarchies inside tenants. | Tenant-scoped uniqueness (`tenant_id`, `org_id`). | bERP, PropTech, bPro |
| **Membership & Access** | Phase 1 | **Approved & Built** | Principal-to-tenant relationship state machine (`active`, `revoked`). | Server-validated `active_membership_id`. | All Products |
| **Active Context Validation** | Phase 1 | **Approved & Built** | Session context validation per API request (`X-Context-ID`). | Explicit token validation; zero trust. | All Products |
| **Authorization Engine** | Phase 1 | **Approved & Built** | ReBAC/ABAC decision engine (`ALLOW`/`DENY`). | Deny-by-default (`authorization-decision.json`). | All Products |
| **Entitlement & Usage** | Phase 3 | Proposed | Commercial plan tiers, quotas, feature rollout. | Metering counters & subscription checks. | All Products |
| **Capability Registry** | Phase 3 | Proposed | Module contract registration & capability discovery. | Contract signature verification. | All Products |
| **Event Pipeline** | Phase 1 | **Approved & Built** | Dual event stream (Domain Events + Security Audit Events). | Structured audit log (`audit-event.json`). | All Products |
| **Integration & Agent Boundary**| Phase 1 | **Approved & Built** | Governed access boundary for external AI agents & webhooks. | Multi-agent execution rules (`AGENTS.md` Sec 19). | All Products |
| **Tenant Data Isolation** | Phase 1 | **Approved & Built** | Database-level physical isolation (PostgreSQL RLS). | `SET LOCAL app.current_tenant_id = '...'`. | All Products |
| **Platform Control Plane** | Phase 1 | **Approved** | Tenant provisioning, health metrics, global governance. | Super-admin access controls. | Platform Operations |

---

## 2. Common Business Foundation Modules Matrix (10 Modules)

| Foundation Module | Strategic Phase | Core Capability | Dependency Contracts | Primary Product Consumer |
| :--- | :---: | :--- | :--- | :--- |
| **Party Model** | Phase 4 | Persons, organizations, and business relationships. | `BOPEN-PARTY-001` | bERP, bPro, PropTech |
| **Relationship Engine** | Phase 4 | B2B vendor, supplier, customer linkages. | `Party`, `Tenant` | bERP, bFleet, LDM |
| **Document Management** | Phase 4 | File storage, signatures, document access control. | `Audit`, `Authz` | PropTech, bPro, LDM |
| **Location & Geography** | Phase 4 | Physical sites, addresses, geofences, GPS points. | `Tenant` | bFleet, LDM, PropTech |
| **Money & Currency** | Phase 4 | Multi-currency units, exchange rates, rounding. | `Tenant` | bERP, bPro, Tourism |
| **Measurement & UOM** | Phase 4 | Standard units of measure and quantity conversions. | `Tenant` | bERP, Agriculture, LDM |
| **Calendar & Schedules** | Phase 4 | Operating hours, shifts, holiday calendars. | `Tenant` | bFleet, bPro, Tourism |
| **Asset Baseline** | Phase 4 | Generic physical/digital asset lifecycle tracking. | `Location`, `Tenant` | bFleet, PropTech, bERP |
| **Workflow State Engine** | Phase 4 | Task approvals, transitions, business processes. | `Events`, `Authz` | All Satellite Products |
| **Notification Engine** | Phase 4 | Transactional alerts (Email, SMS, Push, Webhooks). | `Events`, `Party` | All Satellite Products |

---

## 3. Industry Satellite Products Mapping (9 Products)

```text
                               ┌─────────────────────────────────────────┐
                               │       bOPEN Platform Kernel Core        │
                               │  (Identity, Tenancy, Authz, Audit, RLS) │
                               └────────────────────┬────────────────────┘
                                                    │
                               ┌────────────────────┴────────────────────┐
                               │   Common Business Foundation Modules    │
                               │  (Party, Location, Money, Workflow, etc)│
                               └────────────────────┬────────────────────┘
                                                    │
     ┌──────────────┬──────────────┬────────────────┼──────────────┬──────────────┬──────────────┐
     │              │              │                │              │              │              │
     ▼              ▼              ▼                ▼              ▼              ▼              ▼
  [bPro]        [bFleet]       [PropTech]        [bERP]          [LDM]      [Agriculture]    [Insurance]
 (Practice)    (Logistics)     (RealEstate)     (Enterprise)  (Distribution)  (AgriTech)       (Claims)
```
