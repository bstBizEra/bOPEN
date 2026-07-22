---
name: bopen-skill-admission
description: >-
  Inspect and decide admission of third-party or newly authored skill packages using provenance license script network prompt-injection permission dependency evaluation and revocation review.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.skill.admission
  version: "0.1.0"
  owner: bopen-skills-security-review
  lifecycle: CANDIDATE
  risk-class: SKR3
---

# bOPEN Skill Admission

## Purpose

Prevent untrusted content or executable resources from entering the bOPEN catalog without bounded evidence and ownership.

## Use this skill when

- Installing or updating an external skill
- Reviewing an internal skill before catalog entry
- Investigating a skill incident

## Do not use this skill when

- Assuming popularity means trust
- Approving from SKILL.md alone
- Executing unknown scripts outside an approved sandbox

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`admission-review`, `update-review`, `quarantine`, `revocation-review`

## Procedure

1. **Freeze artifact.** Hash the package and record exact source revision.
2. **Inspect content.** Review instructions references scripts assets policies and metadata.
3. **Analyze execution.** Identify shell filesystem network secret dependency and persistence behavior.
4. **Analyze instructions.** Check prompt injection authority escalation tenant selection and policy bypass.
5. **Review provenance.** Validate owner license notices dependencies and update path.
6. **Run bounded tests.** Execute static and sandboxed adversarial evaluations.
7. **Decide.** Approve conditionally approve quarantine reject or revoke with evidence.

## Mandatory controls

- No automatic admission from an upstream branch.
- All executable files and transitive dependencies are in scope.
- Unknown license or provenance blocks admission.
- Cross-tenant or secret-exfiltration findings block release.
- Approved artifacts are pinned by digest.

## Output contract

- Admission decision
- Severity findings and remediation
- Provenance and license entry
- Pinned digest owner and review date

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
