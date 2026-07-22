---
name: bopen-repository-harness
description: >-
  Establish or improve repository-level agent instructions enforceable project rules failure memory drift checks and CI gates for AGENTS.md Copilot instructions repository governance recurring mistakes and architecture-rule enforcement.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.repository.harness
  version: "0.1.0"
  owner: bopen-platform-engineering
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Repository Harness

## Purpose

Turn repository conventions and repeated failures into durable instructions deterministic checks and review evidence.

## Use this skill when

- Bootstrapping the bOPEN repository
- Adding AGENTS.md scoped instructions checks or CI
- Preventing repeated coding-agent mistakes

## Do not use this skill when

- Implementing an unrelated product feature
- Creating duplicate guidance when an authoritative file exists
- Replacing code or security review

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`assess`, `bootstrap`, `harden`, `drift-review`

## Procedure

1. **Inspect repository.** Read manifests instructions workflows scripts tests and architecture docs.
2. **Inventory rules.** Separate always-on file-scoped deterministic and manual-review rules.
3. **Choose surfaces.** Prefer existing AGENTS.md instructions scripts and CI locations.
4. **Implement minimum harness.** Add precise instructions and fast checks without generic duplication.
5. **Record failure memory.** Document high-risk recurring failures and their detection check.
6. **Verify.** Run commands test drift scripts and produce an adoption report.

## Mandatory controls

- Repository source of truth overrides generic templates.
- High-value rules should be enforceable where practical.
- Generated files and forbidden paths must be explicit.
- Do not weaken branch review or CI controls.
- Every check explains the rule it protects.

## Output contract

- Repository harness assessment
- AGENTS.md and scoped instruction changes
- Drift checks and CI integration
- Adoption report

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
