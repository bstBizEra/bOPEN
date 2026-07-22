---
name: bopen-bpro-reference-integration
description: >-
  Design and review the bPro reference integration proving it consumes bOPEN identity tenancy authorization Entitlement audit and event contracts without duplicating the platform kernel.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.bpro.reference.integration
  version: "0.1.0"
  owner: bpro-product-authority
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN bPro Reference Integration

## Purpose

Demonstrate a real product flow on bOPEN while keeping project-management behavior outside platform core.

## Use this skill when

- Building the first bPro vertical slice
- Reviewing bPro for duplicated platform concepts
- Validating portal event and Entitlement integration

## Do not use this skill when

- Moving project semantics into bOPEN core
- Creating bPro-local identity Tenant Role or Entitlement kernels
- Claiming conformance without end-to-end evidence

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`integration-design`, `gap-review`, `vertical-slice`, `conformance-test`

## Procedure

1. **Choose reference flow.** Select a bounded create-Tenant join enable-bPro create-Project scenario.
2. **Map contracts.** Identify Principal Membership context authorization Entitlement audit and outbox calls.
3. **Protect boundaries.** Keep Project Initiative and Work Item ownership in bPro.
4. **Implement adapters.** Use platform interfaces and stable capability IDs.
5. **Verify tenancy.** Run same-Tenant and cross-Tenant API database and portal tests.
6. **Verify events and evidence.** Trace outbox audit correlation and gate proof.
7. **Report gaps.** Classify missing platform contract product defect or deferred capability.

## Mandatory controls

- No bPro-local duplicate users Tenants Memberships Roles or Entitlements.
- bPro tenant-owned tables use RLS.
- Capability and event names are namespaced.
- Reference flow covers denial and recovery.
- Platform core remains domain-neutral.

## Output contract

- Reference integration design
- Contract mapping and adapters
- End-to-end verification matrix
- Conformance verdict and gaps

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
