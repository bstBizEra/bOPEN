# Work Package Register

## RES-P0-01 — Governance and workspace

**Tasks:** assign roles; approve scope; create isolated directories; establish evidence store.  
**Acceptance:** G0 checklist signed; no production credentials present.  
**Outputs:** charter approval, RACI, workspace record.

## RES-P0-02 — Provenance and license baseline

**Tasks:** verify repository metadata, commit, license, ownership/acquisition note and dependency license surfaces.  
**Acceptance:** source register complete; legal reviewer assigned.  
**Outputs:** upstream pin, license review draft, checksums.

## RES-P0-03 — Reproducible clone bootstrap

**Tasks:** clone pinned commit; record toolchain; install dependencies; configure synthetic services; run baseline build/tests.  
**Acceptance:** second operator reproduces result.  
**Outputs:** terminal log, environment manifest, test report.

## RES-P0-04 — Repository orientation

**Tasks:** map UI, API, models, schema, integrations and tests.  
**Acceptance:** path inventory covers every required lifecycle.  
**Outputs:** repository structure study and trace index.

## RES-P0-05 — Identity and principal trace

**Tasks:** trace registration, verification, login, session, linked accounts, password reset, lockout and API keys.  
**Acceptance:** positive/negative identity cases evidenced.  
**Outputs:** identity findings and principal gap record.

## RES-P0-06 — Tenant and membership trace

**Tasks:** trace team create/update/delete, owner creation, membership list/update/remove/leave.  
**Acceptance:** state changes and constraints evidenced.  
**Outputs:** tenant/membership map and lifecycle gaps.

## RES-P0-07 — Invitation lifecycle trace

**Tasks:** email/link invite, allowed domains, acceptance, expiry, deletion, replay and concurrency.  
**Acceptance:** end-to-end tests and event/audit evidence captured.  
**Outputs:** invitation state comparison and controls.

## RES-P0-08 — Context and authorization trace

**Tasks:** trace team slug/session resolution, access guards, permission checks and cross-team negatives.  
**Acceptance:** G4 positive and negative cases pass.  
**Outputs:** authorization decision map and missing controls.

## RES-P0-09 — Enterprise identity trace

**Tasks:** SSO, directory sync, tenant binding, provisioning/deprovisioning and account collision.  
**Acceptance:** boundaries and source-of-truth decisions documented.  
**Outputs:** IdP/SCIM integration map.

## RES-P0-10 — Entitlement and commercial trace

**Tasks:** team billing association, subscription states, services/prices, payment permissions and access effect.  
**Acceptance:** entitlement versus billing gap explicitly decided.  
**Outputs:** commercial map and BOPEN-ENT inputs.

## RES-P0-11 — Events, audit and API key trace

**Tasks:** enumerate event/audit points; test failures; trace API key creation/use/revocation.  
**Acceptance:** actor, tenant and correlation gaps recorded.  
**Outputs:** event/audit contract requirements.

## RES-P0-12 — Security and failure-mode review

**Tasks:** threat model, dependency scan, secret scan, IDOR tests, webhook verification and transactional failure tests.  
**Acceptance:** critical findings resolved or formally accepted.  
**Outputs:** risk register and security report.

## RES-P0-13 — bOPEN gap synthesis

**Tasks:** classify patterns ADOPT/ADAPT/REJECT/DEFER; draft requirements and ADR candidates.  
**Acceptance:** every proposal cites reviewed evidence.  
**Outputs:** gap register, decision register, requirement candidates.

## RES-P0-14 — Clean-room handoff

**Tasks:** remove upstream code from handoff; package E5 decisions, requirements, contracts and tests.  
**Acceptance:** provenance review and G7 approval.  
**Outputs:** implementation handoff pack.
