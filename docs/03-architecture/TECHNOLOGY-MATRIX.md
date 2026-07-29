# bOPEN Technology Matrix & Scoring Measure Specification v1.0

**Document ID:** `BOPEN-ARCH-TECH-001`  
**Version:** `1.0`  
**Status:** Approved Specification  
**Issued:** 2026-07-29  
**Owner:** Architecture Authority & Security Authority  
**Classification:** Quantitative Technology Evaluation & Architecture Baseline  

---

## 1. Scoring Weight & Evaluation Formula

Candidate technologies for bOPEN platform deployment stamps are evaluated on a 1.0 to 10.0 scale across 6 weighted dimensions:

$$\text{Final Score} = 0.25 \cdot \text{ISO} + 0.20 \cdot \text{SEC} + 0.20 \cdot \text{PERF} + 0.15 \cdot \text{DEV} + 0.10 \cdot \text{LIC} + 0.10 \cdot \text{OPS}$$

| Abbr | Evaluation Dimension | Weight | Description |
| :--- | :--- | :---: | :--- |
| **ISO** | Multi-Tenant Data Isolation | **25%** | Database-level physical isolation (RLS, schema per tenant, tenant_id constraints). |
| **SEC** | Security & Compliance | **20%** | Deny-by-default support, auditability, secret protection, vulnerability track record. |
| **PERF** | Performance & Scalability | **20%** | P99 latency, connection pooling efficiency, throughput under multi-tenant load. |
| **DEV** | Ecosystem & Velocity | **15%** | Type safety, tooling maturity, contract verification support, developer productivity. |
| **LIC** | Clean-Room License Compliance | **10%** | Commercial friendliness (MIT/Apache 2.0/BSD), zero copyleft IP risk. |
| **OPS** | Operational Simplicity | **10%** | Maintenance burden, deployment ease, observability, disaster recovery. |

---

## 2. Technology Evaluation Matrices

### 2.1 Database & Persistence Engine Matrix

| Candidate Engine | ISO (25%) | SEC (20%) | PERF (20%) | DEV (15%) | LIC (10%) | OPS (10%) | Final Weighted Score | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PostgreSQL + Row-Level Security (RLS)** | **9.5** | **9.5** | **9.0** | **9.0** | **10.0** | **8.5** | **9.25 / 10** | **SELECTED CANDIDATE** ([ADR-0005](../adr/ADR-0005.md)) |
| **CockroachDB (Distributed SQL)** | 9.0 | 9.0 | 8.5 | 8.0 | 7.5 | 7.5 | **8.42 / 10** | Supported for Global Scale |
| **MySQL / MariaDB** | 6.5 | 7.5 | 8.5 | 8.5 | 9.0 | 8.5 | **7.73 / 10** | Rejected (Weak native RLS) |
| **DynamoDB / NoSQL** | 7.0 | 8.0 | 9.5 | 7.0 | 8.0 | 8.5 | **7.97 / 10** | Non-Transactional Specialty Only |

---

### 2.2 Authorization & Policy Engine Matrix

| Candidate Engine | ISO (25%) | SEC (20%) | PERF (20%) | DEV (15%) | LIC (10%) | OPS (10%) | Final Weighted Score | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **In-Kernel ReBAC Evaluator (bOPEN Native)** | **10.0** | **9.5** | **9.5** | **9.0** | **10.0** | **9.0** | **9.55 / 10** | **SELECTED BASELINE** ([BOPEN-AUTHZ-001](../04-platform/BOPEN-AUTHZ-001.md)) |
| **SpiceDB / OpenFGA (Zanzibar ReBAC)** | 9.0 | 9.0 | 8.5 | 8.5 | 9.0 | 7.5 | **8.73 / 10** | Supported External Engine |
| **OPA (Open Policy Agent - Rego)** | 7.5 | 8.5 | 8.0 | 7.0 | 10.0 | 7.5 | **7.93 / 10** | Secondary ABAC Alternative |

---

### 2.3 Identity Provider (IdP) & SSO Integration Matrix

| Candidate Engine | ISO (25%) | SEC (20%) | PERF (20%) | DEV (15%) | LIC (10%) | OPS (10%) | Final Weighted Score | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **BoxyHQ Jackson (SAML/OIDC Bridge)** | **9.5** | **9.0** | **9.0** | **9.0** | **10.0** | **9.0** | **9.23 / 10** | **SELECTED IDP BRIDGE** ([BOPEN-IDP-001](../04-platform/BOPEN-IDP-001-DRAFT.md)) |
| **Keycloak Enterprise** | 8.5 | 9.0 | 7.5 | 7.5 | 10.0 | 6.5 | **8.03 / 10** | Supported Enterprise Self-Hosted |
| **Auth0 / Okta (SaaS)** | 9.0 | 9.5 | 9.0 | 9.5 | 7.0 | 9.5 | **8.98 / 10** | Supported Managed SaaS |

---

### 2.4 Language Runtime & Execution Matrix

| Candidate Runtime | ISO (25%) | SEC (20%) | PERF (20%) | DEV (15%) | LIC (10%) | OPS (10%) | Final Weighted Score | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **TypeScript / Node.js** | **9.0** | **9.0** | **8.5** | **9.5** | **10.0** | **9.0** | **9.05 / 10** | **SELECTED FOR SDK & KERNEL** |
| **Python 3.12+** | **9.0** | **9.0** | **7.5** | **9.5** | **10.0** | **9.0** | **8.85 / 10** | **SELECTED FOR KERNEL & ML/DATA** |
| **Go (Golang)** | 9.0 | 9.5 | 9.5 | 8.0 | 10.0 | 9.5 | **9.18 / 10** | High-Throughput Microservice Target |

---

## 3. Thresholds & Superseding Rules

* **Minimum Selection Threshold**: Any candidate technology scoring under **8.0 / 10** is **REJECTED** for core kernel deployment.
* **Architecture Change Requirement**: Changing any selected baseline technology requires a formal ADR superseding [ADR-0005](../adr/ADR-0005.md) or [ADR-0009](../adr/ADR-0009.md).
