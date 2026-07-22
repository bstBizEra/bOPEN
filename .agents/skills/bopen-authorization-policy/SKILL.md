---
name: bopen-authorization-policy
description: >-
  Design and review authorization using Principal Membership Active Tenant Context roles permissions conditions resource relationships Tenant state and explicit decision reasons for WP-04 and access-control changes.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.authorization.policy
  version: "0.1.0"
  owner: bopen-authorization-authority
  lifecycle: CANDIDATE
  risk-class: SKR3
---

# bOPEN Authorization Policy

## Purpose

Produce deterministic explainable and testable decisions without confusing Membership roles Entitlements or database isolation.

## Use this skill when

- Defining roles and permissions
- Adding resource-level or support access
- Reviewing allow and deny behavior

## Do not use this skill when

- Treating Entitlement as Permission
- Using UI visibility as authorization
- Replacing database isolation with policy code

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`policy-design`, `decision-review`, `role-model`, `resource-relationship`, `test-matrix`

## Procedure

1. **Normalize request.** Identify Principal Tenant scope capability action resource and assurance.
2. **Validate context.** Check active Principal Tenant and Membership.
3. **Check availability.** Verify Module availability Entitlement and enablement separately.
4. **Evaluate policy.** Apply role permissions conditions relationships and temporary grants.
5. **Decide.** Return allow or deny with stable reason codes.
6. **Enforce downstream.** Align service and database controls.
7. **Test.** Cover role boundaries stale grants resource mismatch and cross-Tenant denial.

## Mandatory controls

- Deny by default.
- Decision reason codes are auditable and non-leaking.
- Membership Role Permission and Entitlement remain separate.
- Temporary grants expire and are scoped.
- Every privileged path has negative tests.

## Output contract

- Authorization model and policies
- Decision contract and reason codes
- Role and Permission matrix
- Positive and negative tests

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
