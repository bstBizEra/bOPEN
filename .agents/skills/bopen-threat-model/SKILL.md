---
name: bopen-threat-model
description: >-
  Create or update STRIDE-A threat models with architecture data-flow and trust-boundary analysis for Tenant identity support event agent integration and supply-chain security.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.threat.model
  version: "0.1.0"
  owner: bopen-platform-security
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Threat Model

## Purpose

Identify realistic threats assets controls residual risk and verifiable remediation without inventing unsupported vulnerabilities.

## Use this skill when

- Threat modeling a subsystem
- Updating a prior model after changes
- Reviewing support access agents CI or providers

## Do not use this skill when

- Declaring exploitable findings without evidence
- Running intrusive penetration activity
- Replacing independent security testing

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`full`, `incremental`, `component`, `commit-diff`

## Procedure

1. **Establish scope.** Identify revision boundaries assets and deployment.
2. **Build architecture view.** Map components stores identities and external systems.
3. **Build data flow.** Trace sensitive data and controls across trust boundaries.
4. **Apply STRIDE-A.** Analyze spoofing tampering repudiation disclosure denial elevation and abuse.
   Include confused-deputy scenarios wherever one principal, agent, service or support actor can exercise another context's authority.
5. **Verify controls.** Check actual code and configuration.
6. **Prioritize.** Rate likelihood impact reachability and control strength.
7. **Report.** Produce findings mitigations evidence heatmap and verification plan.

## Mandatory controls

- Verify before flagging.
- Tenant isolation and support access are trust boundaries.
- Skills and agent tools are untrusted until promoted.
- Severity reflects reachability and impact.
- Every high finding has mitigation and a test.
- Residual risk is never accepted by the model author; acceptance requires an attributable human Security Authority decision.

## Output contract

- Architecture and data-flow diagrams
- STRIDE-A inventory
- Prioritized findings and mitigations
- Incremental change report

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
