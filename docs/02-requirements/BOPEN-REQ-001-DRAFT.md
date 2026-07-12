# BOPEN-REQ-001 — bOPEN Multi-Tenant, Multi-Industry Open Business Platform Product Requirements Specification v1.0

**Document ID:** `BOPEN-REQ-001`  
**Version:** `1.0`  
**Status:** Draft — no implementation authority  
**Issued:** 2026-07-12  
**Owner:** Product Authority  
**Classification:** Internal engineering governance  

## 1. Purpose

Define the product requirements for the bOPEN platform kernel and its reusable business foundations.

## 2. Requirement catalog

| ID | Requirement | Status |
|---|---|---|
| REQ-PLT-001 | The platform shall provide a governed platform control plane separate from tenant administration. | Draft |
| REQ-PRI-001 | The platform shall support human, service, application, device, agent and system principals. | Draft |
| REQ-ID-001 | The platform shall separate authentication identity from business party and tenant membership. | Draft |
| REQ-TEN-001 | The platform shall model tenant as a commercial, policy, security and isolation boundary. | Draft |
| REQ-ORG-001 | The platform shall support organization graphs and legal entities within or across governed tenant relationships. | Draft |
| REQ-MEM-001 | The platform shall model membership as a first-class principal-to-tenant relationship. | Draft |
| REQ-MEM-002 | Membership status, role assignment, job title, permission and entitlement shall be independently governed. | Draft |
| REQ-CTX-001 | Every tenant-scoped action shall resolve and validate an explicit active context. | Draft |
| REQ-AUTH-001 | Authorization shall be deny-by-default and produce an auditable reasoned decision. | Draft |
| REQ-AUTH-002 | Authorization shall support role, scope, resource relationship, condition and delegated grant inputs. | Draft |
| REQ-ENT-001 | Entitlement decisions shall be separate from authorization and feature rollout. | Draft |
| REQ-ENT-002 | The platform shall support boolean, static, capacity, seat and metered entitlements. | Draft |
| REQ-MOD-001 | Products and modules shall register versioned capabilities, resources, dependencies, events and entitlements. | Draft |
| REQ-EVT-001 | Domain events shall use a versioned envelope with tenant, principal, resource, correlation and causation metadata. | Draft |
| REQ-AUD-001 | Security and business-significant actions shall produce immutable, queryable audit evidence. | Draft |
| REQ-DATA-001 | Tenant-owned data shall use database-enforced isolation or an approved physical isolation profile. | Draft |
| REQ-ISO-001 | The platform shall support pooled, bridge, silo and dedicated tenant isolation profiles. | Draft |
| REQ-SEC-001 | The platform shall enforce least privilege, secret protection, supply-chain controls and threat review. | Draft |
| REQ-API-001 | External APIs shall be versioned, contract-tested and context-aware. | Draft |
| REQ-AGT-001 | Agents shall be governed principals with explicit tenant, tool, data and resource grants. | Draft |
| REQ-USG-001 | Billable or limited capability consumption shall emit idempotent usage events. | Draft |
| REQ-OPS-001 | The platform shall provide observability, backup, recovery and incident evidence appropriate to each isolation profile. | Draft |
| REQ-LOC-001 | User and tenant experiences shall support locale, timezone and multilingual requirements. | Draft |
| REQ-EXT-001 | The platform shall support temporary, partner and cross-tenant access only through explicit grants. | Draft |
| REQ-CMP-001 | Product composition shall not duplicate or bypass shared platform kernels. | Draft |

## 3. Non-functional priorities

1. Tenant isolation and security.
2. Contract compatibility and extensibility.
3. Auditability and traceability.
4. Availability and recoverability appropriate to isolation profile.
5. Performance under pooled multi-tenant workloads.
6. Localization for Lao, English and Thai product experiences.
7. Maintainability through modular boundaries and automated evidence.

## 4. Approval dependencies

This draft requires product, architecture, security, data and engineering review. It does not authorize implementation.
