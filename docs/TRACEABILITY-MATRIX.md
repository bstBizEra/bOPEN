# Traceability Matrix

| Requirement | Artifact | ADR/contract | Work package | Evidence | Status |
|---|---|---|---|---|---|
| REQ-GOV-001 Agent governance | BOPEN-BOOT-001 | Root/scoped AGENTS.md | BOOT-P0-02 | Repository validator | Implemented |
| REQ-GOV-002 Document control | BOPEN-BOOT-001 | Document templates | BOOT-P0-03 | Manifest validator | Implemented |
| REQ-RES-001 Clean-room separation | BOPEN-RES-001 | ADR-0002 | RES-P0-07 | EVD-RES-001-G7 | **Passed (G7)** |
| REQ-TEN-001 Tenant boundary | BOPEN-TENANT-001 | ADR-0005, ADR-0007 | BOOT-P0-11 | 001_tenant_isolation_baseline.sql | **Approved & Built** |
| REQ-MEM-001 First-class membership | BOPEN-TENANT-001 | ADR-0006 | BOPEN-P2-001 | membership-transition.json | **Approved & Built** |
| REQ-CTX-001 Explicit active context | BOPEN-TENANT-001 | HTTP_HEADER_SPEC.md | BOPEN-P2-001 | tenant-context.json | **Approved & Built** |
| REQ-AUTH-001 Deny-by-default | BOPEN-AUTHZ-001 | ADR-0008 | BOOT-P0-11 | authorization-decision.json | **Approved & Built** |
| REQ-IDP-001 Enterprise SSO & SCIM | BOPEN-IDP-001 | BOPEN-IDP-001 | BOPEN-P2-001 | docs/evidence/phase-2/ | **Built; maker verified; authority acceptance pending** |
| REQ-TECH-001 Infrastructure Selection | BOPEN-ARCH-TECH-001 | ADR-0005, ADR-0009 | BOOT-P0-10 | TECHNOLOGY-MATRIX.md | **Approved** |
| REQ-LANG-001 Language Runtimes | BOPEN-ENG-LANG-001 | PROGRAMMING-LANGUAGES-MATRIX.md | BOOT-P0-10 | PROGRAMMING-LANGUAGES-MATRIX.md | **Approved** |
| REQ-MOD-001 Capability Registry | BOPEN-MOD-001 | module-manifest.schema.json | BOPEN-P3-001 (Draft) | Contract tests | **Contract freeze candidate; implementation held** |
| REQ-ENT-001 Entitlement Separation | BOPEN-ENT-001 | entitlement-decision.schema.json | BOPEN-P3-001 (Draft) | Contract tests | **Contract freeze candidate; implementation held** |
| PRD-P35-AUTH Runtime authorization closure | BOPEN-PRD-P35-001 | BOPEN-AUTHZ-001 / authorization-decision.json | BOPEN-P35-001 (Proposed) | P35-PRD-T001..T002 required | **Proposed; review finding reproduced** |
| PRD-P35-IDP Verified invitation acceptance | BOPEN-PRD-P35-001 | BOPEN-IDP-001 / invitation.json | BOPEN-P35-001 (Proposed) | P35-PRD-T003 required | **Proposed; review finding reproduced** |
| PRD-P35-METER Durable replay provenance | BOPEN-PRD-P35-001 | BOPEN-ENT-001 / usage-metered-event.schema.json | BOPEN-P35-001 (Proposed) | P35-PRD-T004 required | **Proposed; review finding reproduced** |
| PRD-P35-MOD Non-bypassable module lifecycle | BOPEN-PRD-P35-001 | BOPEN-MOD-001 / module-manifest.schema.json | BOPEN-P35-001 (Proposed) | P35-PRD-T005 required | **Proposed; known characterization defect** |
| PRD-P35-TXN Atomic tenant provisioning | BOPEN-PRD-P35-001 | BOPEN-P1-001 / PostgreSQL transaction | BOPEN-P35-001 (Proposed) | P35-PRD-T006 required | **Proposed; structural gap** |
| PRD-P35-CONTRACT Producer-contract fidelity | BOPEN-PRD-P35-001 | Versioned schemas | BOPEN-P35-001 (Proposed) | P35-PRD-T007 required | **Proposed; conformance debt recorded** |
| PRD-P35-ASSURE Runtime and evidence assurance | BOPEN-PRD-P35-001 | BOPEN-GOV-EBIV-001 / BOPEN-SEC-001 | BOPEN-P35-001 (Proposed) | P35-PRD-T008..T010 required | **Proposed; no completion verdict** |
| PRD-P35-ENTRY Phase 3.5 decision prerequisites | BOPEN-PRD-P35-001 | DEC-P35-RUNTIME / AUDIT-ENVELOPE / PHASE2-STORAGE / AUTH-BOUNDARY | DEC-P35-DOCKET-001 / DEC-P35-PHASE2-STORAGE-ADD-001 | Authority dispositions and role assignments required | **Proposed; all storage items have advisory dispositions; implementation remains held** |
