---
name: bopen-adr-governance
description: >-
  Create review supersede and validate bOPEN Architectural Decision Records for technology selection platform boundaries providers security decisions irreversible tradeoffs and material deviations.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.adr.governance
  version: "0.1.0"
  owner: bopen-architecture-authority
  lifecycle: CANDIDATE
  risk-class: SKR1
---

# bOPEN ADR Governance

## Purpose

Produce machine-readable and human-reviewable decisions with explicit authority alternatives consequences evidence and lifecycle state.

## Use this skill when

- Making a material architecture or technology choice
- Reviewing or superseding a prior ADR
- Validating the ADR register

## Do not use this skill when

- Minor implementation details
- Backdating or fabricating approval
- Using an ADR to bypass security or legal review

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`create`, `review`, `supersede`, `index`

## Procedure

1. **Locate register.** Find the sequence related decisions and supersession links.
2. **Establish context.** State problem drivers constraints scope and authority.
3. **Evaluate alternatives.** Document credible options and rejection rationale.
4. **Record decision.** Describe the chosen option and positive and negative consequences.
5. **Define implementation.** Specify rollout verification monitoring rollback and migration.
6. **Set status.** Use Proposed unless an authorized approval record exists.
7. **Update index.** Add relationships evidence and review requirements.

## Mandatory controls

- ADR numbering is sequential and stable.
- Proposed is the default state.
- Approval cannot be inferred from authorship.
- Negative consequences and rejected alternatives are mandatory.
- Superseded ADRs remain immutable historical evidence.

## Output contract

- ADR Markdown file
- ADR index update
- Validation findings
- Decision dependencies

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
