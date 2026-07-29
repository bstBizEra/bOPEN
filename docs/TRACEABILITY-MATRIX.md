# Traceability Matrix

| Requirement | Artifact | ADR/contract | Work package | Evidence | Status |
|---|---|---|---|---|---|
| REQ-GOV-001 Agent governance | BOPEN-BOOT-001 | Root/scoped AGENTS.md | BOOT-P0-02 | Repository validator | Implemented |
| REQ-GOV-002 Document control | BOPEN-BOOT-001 | Document templates | BOOT-P0-03 | Manifest validator | Implemented |
| REQ-RES-001 Clean-room separation | BOPEN-RES-001 | ADR-0002 | RES-P0-07 | EVD-RES-001-G7 | **Passed (G7)** |
| REQ-TEN-001 Tenant boundary | BOPEN-TENANT-001 | ADR-0005, ADR-0007 | BOOT-P0-11 | 001_tenant_isolation_baseline.sql | **Approved & Built** |
| REQ-MEM-001 First-class membership | BOPEN-TENANT-001 | ADR-0006 | BOOT-P0-11 | membership-transition.json | **Approved & Built** |
| REQ-CTX-001 Explicit active context | BOPEN-TENANT-001 | HTTP_HEADER_SPEC.md | BOOT-P0-11 | tenant-context.json | **Approved & Built** |
| REQ-AUTH-001 Deny-by-default | BOPEN-AUTHZ-001 | ADR-0008 | BOOT-P0-11 | authorization-decision.json | **Approved & Built** |
| REQ-TECH-001 Infrastructure Selection | BOPEN-ARCH-TECH-001 | ADR-0005, ADR-0009 | BOOT-P0-10 | TECHNOLOGY-MATRIX.md | **Approved** |
| REQ-LANG-001 Language Runtimes | BOPEN-ENG-LANG-001 | PROGRAMMING-LANGUAGES-MATRIX.md | BOOT-P0-10 | PROGRAMMING-LANGUAGES-MATRIX.md | **Approved** |
| REQ-ENT-001 Entitlement separation | BOPEN-ENT-001 | Pending decision contract | Phase 3 | Pending | Draft |
| REQ-MOD-001 Versioned capability registry | BOPEN-MOD-001 | module-manifest.schema.json | Phase 3 | Contract validation | Draft |
