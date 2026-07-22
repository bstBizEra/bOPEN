---
name: bopen-tenant-membership-lifecycle
description: >-
  Design and review tenants invitations memberships suspension removal reactivation ownership transfer and lifecycle state machines for WP-03 and Tenant Portal membership flows.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.tenant.membership.lifecycle
  version: "0.1.0"
  owner: bopen-tenancy-authority
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Tenant and Membership Lifecycle

## Purpose

Model tenant access as a governed relationship between a global Principal and Tenant with explicit states and auditable transitions.

## Use this skill when

- Designing tenant or membership schemas and APIs
- Implementing invitations
- Reviewing suspension leave removal or ownership transfer

## Do not use this skill when

- Using Tenant to User as an ownership hierarchy
- Using active and inactive as the only states
- Equating Tenant status with subscription status

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`model`, `review`, `migration`, `state-machine`, `invitation-flow`

## Procedure

1. **Define Tenant boundary.** State commercial security and data-isolation responsibility.
2. **Define Membership.** Link Principal and Tenant with status and effective dates.
3. **Model invitations.** Cover issue delivery acceptance decline expiry and revocation.
4. **Model transitions.** Define guards and side effects for active suspended left and removed.
5. **Protect ownership.** Prevent loss of all authorized owners.
6. **Integrate context.** Require active Membership for Active Tenant Context.
7. **Verify.** Test duplicates revoked invites stale sessions and cross-tenant identifiers.

## Mandatory controls

- Invitation acceptance activates Membership and never copies a user.
- Membership status and role assignment are separate.
- Tenant and subscription lifecycle are separate.
- Transitions are idempotent and audited.
- Removal invalidates sessions grants and cached context.

## Output contract

- Tenant and Membership model
- State machines and transitions
- Invitation API and sequence contract
- Negative and recovery tests

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
