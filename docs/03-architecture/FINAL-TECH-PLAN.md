# bOPEN Final Integrated Technology & Language Architecture Plan v1.0

**Document ID:** `BOPEN-ARCH-PLAN-001`  
**Version:** `1.0`  
**Status:** Approved Master Architecture Plan  
**Issued:** 2026-07-29  
**Owner:** Architecture Authority & Engineering Authority  
**Classification:** Master Technology & Language Execution Blueprint  

---

## 1. Executive Synthesis

This master architectural plan integrates the quantitative evaluations from:
* [TECHNOLOGY-MATRIX.md](TECHNOLOGY-MATRIX.md) (`BOPEN-ARCH-TECH-001`) — Infrastructure, Database, Identity & Authorization
* [PROGRAMMING-LANGUAGES-MATRIX.md](../08-engineering/PROGRAMMING-LANGUAGES-MATRIX.md) (`BOPEN-ENG-LANG-001`) — Language Runtimes & Framework Stacks

It establishes the end-to-end production blueprint for bOPEN deployment stamps.

---

## 2. Component-by-Component Production Blueprint

```text
 Client Requests (Browser / Mobile / AI Agents / Satellite Products)
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 1. API Gateway Layer (TypeScript / Node.js + Hono)                      │
 │    - Header Validation: X-Tenant-ID, X-Context-ID, X-Correlation-ID    │
 │    - Schema Validation: Zod / TypeBox (contracts/schemas/)             │
 │    - Async Context: Node.js AsyncLocalStorage                           │
 └────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 2. Enterprise SSO / IdP Bridge (BoxyHQ Jackson Bridge)                  │
 │    - Protocols: SAML 2.0 / OIDC / SCIM 2.0                              │
 │    - Token Claims: sub, tid, mid, roles, scopes                         │
 └────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 3. Platform Kernel Core (Python 3.12 + FastAPI + Pydantic v2)           │
 │    - In-Kernel ReBAC Evaluator: Deny-by-Default (ALLOW / DENY)          │
 │    - Active Context: contextvars.ContextVar                             │
 │    - Audit Dispatcher: Correlated Audit Events (audit-event.json)       │
 └────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 4. Database & Storage Layer (PostgreSQL 16 + Row-Level Security)        │
 │    - DDL Baseline: 001_tenant_isolation_baseline.sql                    │
 │    - RLS Policy: SET LOCAL app.current_tenant_id = 'tnt_...'           │
 └────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ 5. High-Throughput Event Microservices (Go 1.22 + Gin/Fiber)            │
 │    - Asynchronous Event Stream Workers & Metering Microservices         │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack Integration Matrix

| Architectural Layer | Selected Technology | Language Runtime | Framework / Driver | Governing Contract / ADR |
| :--- | :--- | :--- | :--- | :--- |
| **API Gateway & Routing** | Node.js Hono Server | TypeScript v5+ | Hono / Zod | [HTTP_HEADER_SPEC.md](../../sdk/headers/HTTP_HEADER_SPEC.md) |
| **Enterprise SSO Bridge** | BoxyHQ Jackson Bridge | TypeScript / Node.js | SAML 2.0 / OIDC | [BOPEN-IDP-001](../04-platform/BOPEN-IDP-001-DRAFT.md) |
| **Platform Kernel Core** | Python FastAPI Kernel | Python 3.12+ | FastAPI / Pydantic v2 | [BOPEN-ARCH-001](BOPEN-ARCH-001.md) |
| **Authorization Evaluator** | In-Kernel ReBAC Engine | Python / TypeScript | Custom Deny-by-Default | [authorization-decision.json](../../contracts/schemas/authorization-decision.json) |
| **Database & Persistence** | PostgreSQL 16 + RLS | SQL | psycopg3 / pg | [001_tenant_isolation_baseline.sql](../../infrastructure/database/001_tenant_isolation_baseline.sql) |
| **High-Scale Workers** | Go Microservices | Go 1.22+ | Gin / Fiber | [ADR-0009](../adr/ADR-0009.md) |

---

## 4. Governance & Deployment Invariants

1. **Strict Context Propagation**: Every request must carry validated `X-Tenant-ID` and `X-Correlation-ID` headers.
2. **Database-Level Data Protection**: No tenant table may be deployed without PostgreSQL Row-Level Security (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).
3. **Contract-First Validation**: APIs MUST validate request/response bodies against machine-readable JSON schemas in `contracts/schemas/`.
4. **Validation Enforcement**: All deployments MUST pass `python tools/validate_repository.py` and `python tools/check_clean_room.py`.
