# Traceability Matrix

| Requirement | Artifact | ADR/contract | Work package | Evidence | Status |
|---|---|---|---|---|---|
| REQ-GOV-001 Agent governance | BOPEN-BOOT-001 | Root/scoped AGENTS.md | BOOT-P0-02 | EVD-BOOT-001 | Evidence generated |
| REQ-GOV-002 Document control | BOPEN-BOOT-001 | Document templates | BOOT-P0-03 | EVD-BOOT-002 | Evidence generated |
| REQ-ENG-001 Local source-control baseline | BOPEN-BOOT-001 | repository-model/branching/local-development/DEC-0006/DEC-0008 | BOOT-P0-09/BOOT-P0-01 | EVD-BOOT-004/EVD-BOOT-010/EVD-BOOT-011 | Execution complete; protected controls verified |
| REQ-ENG-002 Contract validation harness | BOPEN-BOOT-001 | contract-governance/schema-conventions | BOOT-P0-10 | EVD-BOOT-005 | Started |
| REQ-ENG-003 First vertical-slice acceptance fixture | BOPEN-BOOT-001 | FIRST-VERTICAL-SLICE-SPEC/audit-event schema | BOOT-P0-11 | EVD-BOOT-006 | Started |
| REQ-ENG-004 Bootstrap exit-gate readiness | BOPEN-BOOT-001 | BOOTSTRAP-GATES/report_bootstrap_gates.py | BOOT-P0-12 | EVD-BOOT-007/EVD-BOOT-011 | Ready for authority review; B7 pending |
| REQ-ENG-005 Bootstrap validation evidence closure | BOPEN-BOOT-001 | BOOTSTRAP-GATES/EVIDENCE-INDEX | BOOT-P0-02/03/12 | EVD-BOOT-008 | Review required |
| REQ-ENG-006 Bootstrap security and supply-chain controls | BOPEN-BOOT-001 | check_secrets/check_supply_chain/CI | BOOT-P0-05/06 | EVD-BOOT-009 | Execution complete |
| REQ-ENG-007 BOOT-P0 completion self-review | BOPEN-BOOT-001 | WORK-PACKAGE-REGISTER/DEC-0007/DEC-0008 | BOOT-P0-01 through BOOT-P0-12 | EVD-BOOT-009/EVD-BOOT-011 | Execution reconciled; DEC-0007 authority decision pending |
| REQ-RES-001 Clean-room separation | BOPEN-RES-001 | ADR-0002 | RES-P0-01/14 | Source/evidence registers | In progress |
| REQ-RES-002 R0 controlled reproduction | BOPEN-RES-001 | DEC-0009/pin contract/research scripts | RES-P0-01/02/03 | EVD-RES-002 | G0-G2 pass with conditions |
| REQ-RES-003 R1 core relationship trace | BOPEN-RES-001 | DEC-0009/R1 trace contract and runner | RES-P0-04/05/06/07 | EVD-RES-003 | RES-P0-04 complete at E2; G3 open |
| REQ-TEN-001 Tenant boundary | BOPEN-TENANT-001 | Pending | Future | Pending | Draft |
| REQ-TEN-002 Multi-tenant DEV readiness | BOPEN-TENANT-001/BOPEN-AUTHZ-001/BOPEN-SEC-001 | membership/active-context/tenant-ownership schemas | DEV-P0-01 | EVD-DEV-001 | Draft contracts validated |
| REQ-MEM-001 First-class membership | BOPEN-TENANT-001 | ADR-0006/membership schema | DEV-P0-01 | EVD-DEV-001 | Draft contract validated |
| REQ-CTX-001 Explicit active context | BOPEN-TENANT-001 | active-context schema | DEV-P0-01 | EVD-DEV-001 | Draft contract validated |
| REQ-AUTH-001 Deny-by-default | BOPEN-AUTHZ-001 | Pending policy contract | Future | Pending | Draft |
| REQ-ISO-001 API and database tenant isolation | BOPEN-TENANT-001/BOPEN-SEC-001 | tenant-ownership schema/readiness fixture | DEV-P0-01 | EVD-DEV-001 | Negative fixture validated |
| REQ-ENT-001 Entitlement separation | BOPEN-ENT-001 | Pending decision contract | Future | Pending | Draft |
| REQ-MOD-001 Versioned capability registry | BOPEN-MOD-001 | module-manifest.schema.json | BOOT-P0-10 | Contract validation | Draft |
| GOAL-NS-001 Certified Module Enablement Rate and certification conditions | BOPEN-GOAL-001 | program-goal.requirements.json/DEC-0010 | GOV-P0-01 | EVD-GOV-001 | Draft; no certified modules |
| GOAL-OUT-01..08 Strategic outcome catalog | BOPEN-GOAL-001 | program-goal.requirements.json | GOV-P0-01 | EVD-GOV-001 | Draft; outcomes not achieved |
| GOAL-PG-G0 Program governance bootstrap | BOPEN-GOAL-001/BOPEN-GOV-001 | program-control registers/report_program_g0.py | GOV-P0-01 | EVD-GOV-001 | NOT_READY |
| GOAL-PG-P0..P4/C0 Program lifecycle gates | BOPEN-GOAL-001 | program-lifecycle-crosswalk/DEC-0010 | GOV-P0-01 and future accepted packages | Future independent evidence | NOT_READY |
| GOAL-MR-01..08 Measurement integrity rules | BOPEN-GOAL-001/BOPEN-GOV-001 | program-control validator | GOV-P0-01 | EVD-GOV-001 | Draft controls |
| REQ-GOV-003 Attributable human approval envelopes | BOPEN-GOV-001 Draft | pg-g0-authority-docket schema/validator | GOV-P0-02 Proposed | EVD-GOV-002 | Draft; all human decisions pending |
| REQ-GOV-004 Exact instruction-path authority | DEC-0012 Proposed | PG-G0 authority docket blockers | GOV-P0-02 Proposed | EVD-GOV-002 | UNRESOLVED; no equivalence inferred |
| GOAL-PG-G0 Human authority routing | BOPEN-GOAL-001/BOPEN-GOV-001 Drafts | PG-G0-AUTH-001/PG-G0-GATE-001 Drafts | GOV-P0-02 Proposed | EVD-GOV-002 | NOT_READY; no gate action in effective matrix |

## Append-only Batch 2 signed-state trace — 2026-07-23

| Requirement | Governing source | Machine control | Work package | Evidence | Signed-state result |
|---|---|---|---|---|---|
| REQ-GOV-003 Attributable human approval envelopes | BOPEN-GOV-001 effective; authority matrix v0.2 approved | PG-G0-AUTH-001 v0.3 schema/validator | GOV-P0-04 accepted | Signing Pass 2; EVD-GOV-009 | 13 signed dispositions encoded; exact-SHA review pending |
| REQ-GOV-004 Exact instruction-path authority | DEC-0012 accepted; DEC-0013 effective | root-control schema/validator and five package ledgers | GOV-P0-03 active | Signing Pass 2 B6; EVD-GOV-009 | All five ledgers active atomically |
| GOAL-PG-G0 Human authority routing | approved register set | v0.3 docket and readiness report | GOV-P0-01 accepted | EVD-GOV-009 | `NOT_READY`; five B8 decisions and B9 pending |

## Append-only v0.4 signed-state trace - 2026-07-23

| Requirement | Governing source | Machine control | Work package | Evidence | Signed-state result |
|---|---|---|---|---|---|
| REQ-GOV-003 Attributable human approval envelopes | Signing Pass 3; approved identity register | PG-G0-AUTH-001 v0.4 schema/validator | GOV-P0-04 | EVD-GOV-011 | Five B8 approvals encoded with exact actor provenance |
| GOAL-PG-G0 Human authority routing | PG-G0-GATE-001; v0.4 readiness report | B9/PASS_PG_G0 pending decision surface | GOV-P0-04 | EVD-GOV-011 | `ready_for_pg_g0_gate_decision: true`; independent conformance prerequisite remains |
