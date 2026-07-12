# DEV-P0-01 - Multi-tenant development readiness contracts

**Status:** Accepted for development-readiness execution  
**Owner:** Engineering Authority  
**Sponsor authorization:** 2026-07-13 instruction to start bOPEN multi-tenant DEV readiness  
**Governing artifacts:** `BOPEN-BOOT-001`, `BOPEN-TENANT-001-DRAFT`, `BOPEN-AUTHZ-001-DRAFT`, `BOPEN-SEC-001-DRAFT`  
**Architecture decisions:** `ADR-0006`, `ADR-0007`, `ADR-0008`  
**Phase:** Phase 0 contract readiness

## Objective

Make the minimum multi-tenant boundary executable as draft contracts and negative acceptance evidence before production kernel implementation begins.

## Authorized scope

- draft membership, active-context, and tenant-ownership contracts;
- synthetic acceptance fixtures for allow and deny behavior;
- standard-library validation and tests;
- documentation, traceability, and evidence updates.

## Prohibited scope

- production API, database, authentication, authorization, or tenant-provisioning logic;
- migrations or tenant-owned storage;
- upstream source reuse or translation;
- approval of draft normative artifacts;
- bypass of BOPEN-RES-001 G7 or the implementation gate.

## Deliverables

1. Draft membership contract that does not conflate membership with role, permission, or entitlement.
2. Draft active-context contract that accepts only server-validated context sources.
3. Draft tenant-ownership envelope for tenant-owned resources.
4. Multi-tenant readiness acceptance fixture with API and database cross-tenant denial scenarios.
5. Contract validator rules and focused negative tests.
6. EVD-DEV-001 validation receipt and updated traceability.

## Acceptance criteria

1. Every contract is marked draft and uses the `bopen://` namespace.
2. Tenant, principal, membership, context, and resource identifiers are explicit.
3. Missing, suspended, forged, mismatched, and cross-tenant contexts deny by default.
4. Cross-tenant denial is represented at both API and database enforcement layers.
5. Authorization and audit evidence share the same correlation ID, decision, reason, and policy version.
6. Full repository, contract, clean-room, secret, supply-chain, and test validation passes.

## Dependencies and blocked decisions

Production implementation remains blocked by BOPEN-RES-001 G7, approved requirements and architecture, approved tenant/authz/security artifacts, accepted production implementation work, and database isolation design. These draft contracts are development inputs only.

## Provenance

**Source:** Existing bOPEN invariants, draft artifacts, ADR-0006/0007/0008, and sponsor instruction  
**Timestamp:** 2026-07-13T03:10:00+07:00  
**Agent ID:** bCodex (BST Motor)
