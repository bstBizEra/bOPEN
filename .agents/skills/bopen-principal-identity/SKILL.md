---
name: bopen-principal-identity
description: >-
  Design and review principals human identities service accounts applications devices agents authentication methods sessions and provider-neutral identity seams for WP-02 and identity-model changes.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.principal.identity
  version: "0.1.0"
  owner: bopen-identity-authority
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Principal and Identity

## Purpose

Preserve one global Principal model while separating authentication identity from Party records and tenant membership.

## Use this skill when

- Creating principal or identity schemas
- Designing login MFA passkeys sessions or account linking
- Reviewing service device or agent identities

## Do not use this skill when

- Modeling customers or suppliers as login accounts
- Creating one user per tenant
- Using provider IDs as canonical principals

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`model`, `review`, `migration`, `authentication-flow`

## Procedure

1. **Classify actors.** Identify human service application device agent and system principals.
2. **Separate concepts.** Distinguish principal identity account authentication method profile and Party.
3. **Define lifecycle.** Specify creation verification linking suspension recovery and termination.
4. **Design provider seam.** Keep canonical IDs and policy independent of the external IdP.
5. **Model sessions.** Define MFA passkeys devices revocation and security activity.
6. **Link tenant access.** Use Membership and Active Tenant Context.
7. **Verify.** Test identity collisions stale sessions provider outage and takeover paths.

## Mandatory controls

- Canonical principal IDs are platform-owned.
- External identities are credentials not the Principal itself.
- Party may exist without a user account.
- Identity recovery is audited and rate limited.
- Agent and service credentials are scoped and rotated.

## Output contract

- Principal and identity model
- Lifecycle and sequence diagrams
- Provider interface contract
- Security and migration tests

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
