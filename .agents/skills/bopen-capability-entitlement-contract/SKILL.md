---
name: bopen-capability-entitlement-contract
description: >-
  Design and review Product to Module to Feature to Action to Resource contracts module manifests Tenant Entitlements enablement quotas and access sequencing for WP-05 and product composition.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.capability.entitlement.contract
  version: "0.1.0"
  owner: bopen-product-platform-authority
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Capability and Entitlement Contract

## Purpose

Keep commercial rights availability Tenant configuration and user authorization distinct while enabling composable products and industry packs.

## Use this skill when

- Registering a Product Module Feature Action or Resource
- Defining plans Entitlements or limits
- Composing bPro or another product

## Do not use this skill when

- Using feature flags as commercial Entitlements
- Granting Permission because a Tenant purchased a plan
- Embedding industry logic in the kernel

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`capability-model`, `module-manifest`, `entitlement-model`, `quota-design`, `composition-review`

## Procedure

1. **Define ontology.** Name Product Module Feature Action and Resource consistently.
2. **Create manifest.** Declare dependencies capabilities resources events navigation and compatibility.
3. **Model availability.** Define registration validation approval and platform availability.
4. **Model Tenant rights.** Define Entitlement limits dates and plan versions.
5. **Model enablement.** Define Tenant configuration and rollout flags separately.
6. **Integrate authorization.** Require Permission and policy after Entitlement and enablement.
7. **Test.** Cover missing Entitlement disabled Module quota exhaustion and unauthorized Principal.

## Mandatory controls

- Available Entitled Enabled and Authorized are separate.
- Capability IDs are stable and namespaced.
- Plan versions are immutable after sale.
- Module dependencies are explicit and acyclic.
- Industry behavior stays outside platform core.

## Output contract

- Capability registry entries
- Module manifest and dependency graph
- Entitlement and limit model
- Composition and access tests

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
