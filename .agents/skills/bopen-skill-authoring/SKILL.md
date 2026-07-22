---
name: bopen-skill-authoring
description: >-
  Create revise package and statically evaluate Agent Skills-compatible bOPEN packages with SKILL.md bopen.skill.yaml schemas policies test prompts provenance and release evidence.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.skill.authoring
  version: "0.1.0"
  owner: bopen-skills-authority
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Skill Authoring and Evaluation

## Purpose

Produce portable governed skills whose activation authority runtime boundaries and evidence are explicit and testable.

## Use this skill when

- Creating a repository or product skill
- Improving trigger precision or output contracts
- Preparing a release candidate

## Do not use this skill when

- Granting runtime permissions to a skill
- Publishing an unreviewed external skill
- Replacing durable workflow logic with prompt instructions

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`create`, `revise`, `evaluate`, `package`, `description-tuning`

## Procedure

1. **Capture intent.** Define outcome activation language non-goals and authority boundary.
2. **Design package.** Create SKILL.md manifest schemas references and policies.
3. **Declare requirements.** List capabilities and tools without granting them.
4. **Create evaluations.** Add positive negative security tenancy failure and recovery cases.
5. **Validate.** Run schema reference checksum and dangerous-content checks.
6. **Package.** Generate inventory SBOM provenance and checksums.
7. **Set lifecycle.** Use VALIDATED until independent evaluation approval and signing.

## Mandatory controls

- Description says what the skill does and when to trigger.
- Tool declarations are requirements not grants.
- No secrets or mutable latest dependencies.
- Published versions are immutable.
- Static checks do not substitute for model evaluation.

## Output contract

- Complete skill directory
- Validation and static-evaluation reports
- Release manifest SBOM provenance and checksums
- Promotion recommendation

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
