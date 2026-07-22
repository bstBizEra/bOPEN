---
name: bopen-tenant-context-propagation
description: >-
  Design trace and verify Active Tenant Context across HTTP database transactions background jobs events caches audit support access and agent executions for every tenant-sensitive path.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.tenant.context.propagation
  version: "0.1.0"
  owner: bopen-platform-security
  lifecycle: CANDIDATE
  risk-class: SKR3
---

# bOPEN Tenant Context Propagation

## Purpose

Ensure tenant authority is server-validated explicit correlated and fail-closed from request entry through downstream effects.

## Use this skill when

- Adding an API job cache event consumer or agent tool that touches tenant data
- Investigating wrong-tenant behavior
- Designing tenant switching or support access

## Do not use this skill when

- Trusting client-supplied Tenant IDs
- Inferring Tenant from a resource without authorization
- Using global cache keys for tenant-owned data

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`trace`, `design`, `review`, `negative-test-plan`

## Procedure

1. **Resolve context.** Authenticate Principal and validate active Membership server-side.
2. **Bind request.** Create immutable context with Tenant Principal correlation and assurance.
3. **Propagate transaction.** Set transaction-local database context and prevent pool leakage.
4. **Propagate async.** Carry Tenant and causation data then revalidate at consumption.
5. **Scope cache.** Include Tenant and authorization versions in keys.
6. **Record audit.** Persist effective Tenant and decision context.
7. **Test fail-closed.** Exercise missing stale mismatched and forged context.

## Mandatory controls

- Trusted server logic establishes context.
- Database context is transaction-local and safely cleared.
- Consumers revalidate because events are not authority tokens.
- Support access requires an explicit expiring grant and reason.
- Negative tests cover APIs jobs caches and events.

## Output contract

- End-to-end context map
- Context and middleware contract
- Boundary-specific negative tests
- Blocking findings

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
