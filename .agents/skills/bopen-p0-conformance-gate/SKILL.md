---
name: bopen-p0-conformance-gate
description: >-
  Assemble and review P0 entry and exit evidence across repository governance principal authentication tenancy RLS authorization Entitlement portals events audit recovery supply chain and bPro reference integration.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.p0.conformance.gate
  version: "0.1.0"
  owner: bopen-independent-assurance
  lifecycle: CANDIDATE
  risk-class: SKR3
---

# bOPEN P0 Conformance Gate

## Purpose

Issue a controlled P0 verdict from complete hashable evidence without waiving non-waivable Tenant-isolation or security controls.

## Use this skill when

- Reviewing readiness to start or exit P0
- Assembling work-package evidence
- Checking missing recovery supply-chain or approval proof

## Do not use this skill when

- Self-approving owned work
- Marking missing evidence passed
- Waiving cross-Tenant controls

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`entry-gate-review`, `work-package-review`, `exit-gate-review`, `evidence-index`, `final-verdict`

## Procedure

1. **Load gates.** Use authoritative entry work-package and exit criteria.
2. **Index evidence.** Map criteria to artifacts methods results hashes and reviewers.
3. **Validate integrity.** Check provenance time scope revision and consistency.
4. **Review negative controls.** Confirm cross-Tenant unauthorized stale-context replay and recovery cases.
5. **Assess independence.** Verify separation of duties and approval authority.
6. **Classify gaps.** Mark pass fail incomplete stale or not applicable.
7. **Issue verdict.** Provide pass conditional pass or fail with blockers.

## Mandatory controls

- Tenant isolation authorization and evidence integrity are non-waivable.
- No evidence means no pass.
- Stale evidence is not reused after material change.
- Reviewer independence is recorded.
- Verdict references exact revision and artifact digests.

## Output contract

- P0 evidence index
- Gate-by-gate matrix
- Blocking and conditional findings
- Final verdict and approval needs

Every output distinguishes evidence, inference, assumption and recommendation. Use `schemas/output.schema.json` for structured output.

## Failure handling

- Missing authoritative evidence: issue `decision-required` or `incomplete`; never invent facts.
- Failed mandatory or cross-Tenant control: issue `fail` and identify the blocker.
- Unsafe requested behavior: refuse the unsafe step and preserve the governing boundary.
- Tool or dependency failure: report exactly what ran, what failed and which evidence is unavailable.

## Completion evidence

1. Identify source scope or repository revision.
2. Record checks and important negative cases.
3. List residual risks and required reviewers.
4. Never claim `APPROVED`, `SIGNED`, `PUBLISHED` or production-ready without corresponding evidence.

## References

- `references/bopen-invariants.md`
- `references/control-checklist.md`
- `references/output-contract.md`
- `references/examples.md`
- `policies/execution-policy.yaml`
- `bopen.skill.yaml`
