# BOPEN-GOV-001 — Program Authority and Delivery-Control Baseline

**Version:** 0.1
**Status:** Draft
**Owner:** Engineering Authority
**Issued:** 2026-07-21
**Work package:** GOV-P0-01
**Governing artifacts:** BOPEN-BOOT-001; BOPEN-GOAL-001 (Draft)
**Decision reference:** DEC-0010 (Proposed)

## Purpose

Define the candidate authority separation and minimum delivery records needed for `PG-G0`. Structural validation of these controls does not approve them or pass `PG-G0`.

## Authority matrix

| Action | Accountable human authority | Maker | Independent checker | Required concurrence | Self-approval |
|---|---|---|---|---|---|
| Approve program goal, outcomes or targets | Product Authority | Requirements/Program agent or delegated human | Governance checker | Architecture Authority; Security/Data where affected | Prohibited |
| Approve architecture or lifecycle crosswalk | Architecture Authority | Architecture agent or delegated human | Architecture checker | Product/Security/Data as applicable | Prohibited |
| Accept a work package | Engineering Authority | Orchestrator/Requirements agent | Governance checker | Owning artifact authority | Prohibited |
| Approve tenant, authorization or security controls | Architecture/Security/Data Authorities | Specialized maker | Security/Isolation checker | All named accountable authorities | Prohibited |
| Pass a program gate | Authority named in the approved gate contract | Evidence coordinator | Independent conformance checker | Required domain authorities | Prohibited |
| Certify a module | Module Certification Authority (to be approved) | Module maker | Independent module/isolation checker | Product, Architecture and Security | Prohibited |
| Promote a skill | Skill Governance Authority (to be approved) | Skill maker | Independent evaluator | Security for privileged use | Prohibited |
| Approve an exception | Authority owning the affected control | Requester | Risk/security checker | Security for security controls | Prohibited |
| Authorize a release | Human Release Authority | Release maker | Independent release checker | Product/Security/Operations as required | Prohibited |

Agent role names are capability labels, not authority identities. A named human or formally delegated authority must record each final decision.

## Work-item control requirements

Every material work item shall record authorization source, accepted-by/at, lifecycle namespace, expiry, maker, independent checker, sessions, worktree, branch, exact base SHA, allowed and prohibited paths, evidence destination, rollback, completion SHA, checker verdict and separate authority disposition.

Active work is invalid when the maker equals the checker, authority is absent, the base SHA is not exact, scope is broad or overlapping, the record is expired, or the referenced goal/requirement is not approved for the requested action.

## Evidence control requirements

Evidence shall bind work item and session IDs to exact repository state; record environment and tool versions, commands and exit codes, artifact hashes, mandatory tests, skips and approved exceptions; distinguish maker result, checker verdict and human decision; and disclose clean-room/security status and residual risks.

## Register requirements

`docs/00-governance/registers/` contains the draft agent, goal, module, skill, schedule, authority and technology-assignment registers. Empty entries are explicit evidence of incompleteness; they shall not be populated with invented identities, approvals, modules or skills.

## PG-G0 decision rule

`PG-G0` remains `NOT_READY` until controlling governance, all five required registers and the authority matrix are approved; technology decisions are assigned under accepted records; work/evidence templates are operational; records are current and internally consistent; and independent evidence is accepted by the designated human authority.

## Security and data implications

No plaintext production credential may be assigned to an agent. Tenant, authorization, security, module certification, skill promotion, exception and release decisions require separation of maker, checker and final human authority.

## Approval

Pending Engineering, Product and Architecture Authority review, with Security and Data concurrence for their controlled actions.
