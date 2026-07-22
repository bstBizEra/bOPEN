---
name: bopen-clean-room-research
description: >-
  Conduct governed external and open-source research using source registers license review evidence classification and a clean-room observation-to-requirement workflow for architecture archaeology comparative studies and clone analysis.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.clean.room.research
  version: "0.1.0"
  owner: bopen-research-authority
  lifecycle: CANDIDATE
  risk-class: SKR1
---

# bOPEN Clean-Room Research

## Purpose

Extract reusable architectural knowledge without copying an upstream product into bOPEN or losing provenance and licensing evidence.

## Use this skill when

- Studying external SaaS identity RLS framework authorization or billing systems
- Creating source and license registers
- Turning observations into bOPEN requirements

## Do not use this skill when

- Copying upstream code without approval
- Treating a clone as the bOPEN baseline
- Removing upstream notices or provenance

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`source-study`, `comparison`, `clone-governance`, `finding-to-requirement`

## Procedure

1. **Register source.** Record URL revision license retrieval date and purpose.
2. **Define boundary.** State what may be observed and what may not be copied.
3. **Trace behavior.** Follow UI API model database policy and test flows.
4. **Classify evidence.** Separate direct observation inference limitation and open question.
5. **Map to bOPEN.** Convert patterns into architecture findings and gaps.
6. **Create requirement.** Write bOPEN-owned requirements without upstream naming leakage.
7. **Review license.** Record obligations and legal-review needs.

## Mandatory controls

- Observation is not permission to copy.
- Every finding cites source revision and path.
- License obligations remain attached to source material.
- Upstream concepts are mapped not renamed and shipped.
- Architecture decisions remain bOPEN-owned.

## Output contract

- Research manifest and source register
- Comparison matrix and findings
- Gap register and requirements
- License and provenance record

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
