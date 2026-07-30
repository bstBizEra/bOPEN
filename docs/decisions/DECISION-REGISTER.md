# Decision Register

| ID | Decision | Status | Owner |
|---|---|---|---|
| DEC-0001 | Create BOPEN-BOOT-001 repository governance pack | Approved | Engineering Authority |
| DEC-0002 | Keep production implementation gated until G7 and normative approval | **Approved (G7 Passed)** | Architecture Authority |
| DEC-0003 | Select production technology stack (PostgreSQL RLS, BoxyHQ Jackson IdP, ReBAC) | **Approved** ([BOPEN-ARCH-TECH-001](../03-architecture/TECHNOLOGY-MATRIX.md)) | Architecture Authority |
| DEC-0004 | Select programming language stack (TypeScript Gateway/SDKs, Python Kernel, Go Microservices) | **Approved** ([BOPEN-ENG-LANG-001](../08-engineering/PROGRAMMING-LANGUAGES-MATRIX.md)) | Engineering Authority |
| DEC-0005 | Adopt master technology & language architecture execution plan | **Approved** ([BOPEN-ARCH-PLAN-001](../03-architecture/FINAL-TECH-PLAN.md)) | Architecture Authority |
| DEC-0006 | Keep bOPEN as codename pending brand clearance | Open condition | Product Authority |
| DEC-0007 | Adopt `BOPEN-IDP-001` as the approved normative identity, federation, SCIM, token and delegation standard for Phase 2, superseding `BOPEN-IDP-001-DRAFT` | **Approved** ([BOPEN-IDP-001](../04-platform/BOPEN-IDP-001.md)) — Phase 2 Completed | Engineering Authority |
| DEC-0008 | Bind `BOPEN-P2-001` as the accepted Phase 2 execution work package governing `MILE-2.1`..`MILE-2.5` | **Approved** ([BOPEN-P2-001](../work-packages/BOPEN-P2-001-EXECUTION-PLAN.md)) — Phase 2 Completed | Engineering Authority |
| DEC-0009 | Resolve `ADR-P2-001`..`ADR-P2-010` and `D-P2-001`..`D-P2-015` before any Phase 2 code mutation | **Approved** ([DEC-P2-DOCKET](DEC-P2-DOCKET.md)) | Engineering Authority |
| DEC-0010 | Record `ADR-P2-00X` plan labels as aliases of `ADR-0010`..`ADR-0019` | **Approved** ([DEC-P2-DOCKET](DEC-P2-DOCKET.md) §2) | Architecture Authority |
| DEC-0011 | Accept implementation deltas arising from `D-P2-002`, `D-P2-007` and `D-P2-015` | **Approved** ([DEC-P2-DOCKET](DEC-P2-DOCKET.md) §4) | Engineering/Security Authorities |
| DEC-P3-ENTRY | Authorize Phase 3 Implementation via Evidence-Driven Gate Realization (`AGENTS.md` §19.6) | **Approved (GO ON EVIDENCE)** ([DEC-P3-ENTRY](DEC-P3-ENTRY.md)) | Engineering/Architecture Authorities |
| DEC-P35-RUNTIME | Insert Phase 3.5 Runtime Realization before Phase 4; bound `AGENTS.md` §19.6 with an evidence admissibility floor and independent verification quorum (`BOPEN-GOV-EBIV-001`); reconcile conflicting gate registers | **Proposed** ([DEC-P35-RUNTIME](DEC-P35-RUNTIME.md)) | Engineering/Architecture Authorities |
| DEC-P35-AUDIT-ENVELOPE | Resolve which audit envelope is the contract: `audit-event.json` deviates from `BOPEN-P1-001` §10.2, which the uncontracted lifecycle producer already implements | **Proposed** ([DEC-P35-AUDIT-ENVELOPE](DEC-P35-AUDIT-ENVELOPE.md)) | Architecture/Engineering Authorities |
| DEC-P35-PHASE2-STORAGE | Six blocking decisions before Phase 2 can be persisted: identifier format, sessions with no tenant, delegated grants under RLS, two incompatible context tables, group-mapping key, overlapping grants | **Proposed** ([DEC-P35-PHASE2-STORAGE](DEC-P35-PHASE2-STORAGE.md)) | Architecture/Engineering/Security Authorities |
